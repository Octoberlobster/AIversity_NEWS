"""
新聞事件分組器 - 完整版
- 使用 google.genai 進行智能分組 (語意向量 + DBSCAN 分群)
- 整合 Supabase 資料庫讀寫
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# --- 環境變數設定 ---
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
print(f"Gemini API Key Loaded: {'Yes' if GEMINI_API_KEY else 'No'}")

# --- 環境檢查 ---
if not SUPABASE_URL or not SUPABASE_KEY:
    print("錯誤：請在 .env 檔案中設定 SUPABASE_URL 與 SUPABASE_KEY")
    sys.exit(1)
if not GEMINI_API_KEY:
    print("錯誤：請在 .env 檔案中設定 GEMINI_API_KEY")
    sys.exit(1)

# --- 套件載入與檢查 ---
try:
    from supabase import create_client
    print("✓ Supabase 套件已載入")
except ImportError:
    print("錯誤：請先安裝 supabase-py：pip install supabase")
    sys.exit(1)

try:
    import google.genai as genai
    print("✓ Google Genai 套件已載入")
except ImportError:
    print("錯誤：請先安裝 google-genai SDK：pip install google-generativeai")
    sys.exit(1)

try:
    import numpy as np
    from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
    from sklearn.metrics import silhouette_score, calinski_harabasz_score
    from sklearn.metrics.pairwise import cosine_similarity
    print("✓ Scikit-learn 和 NumPy 套件已載入")
except ImportError:
    print("錯誤：請先安裝 scikit-learn 和 numpy：pip install scikit-learn numpy")
    sys.exit(1)


class NewsEventGrouper:
    """新聞事件分組器"""

    def __init__(self):
        """初始化客戶端"""
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
            self.use_ai = True  # 設定 AI 功能可用旗標
            print("✓ Gemini Client 初始化成功")
        except Exception as e:
            print(f"✗ Gemini Client 初始化失敗: {e}")
            print("切換到 fallback 模式...")
            self.genai_client = None
            self.use_ai = False # 設定 AI 功能不可用旗標

    def fetch_topic_news_map_from_supabase(self):
        """從 Supabase 的 topic_news_map 表獲取主題新聞映射"""
        try:
            response = self.supabase.table('topic_news_map').select(
                'topic_id, story_id'
            ).execute()
            
            if response.data:
                print(f"✓ 成功獲取 {len(response.data)} 筆主題新聞映射資料")
                return response.data
            else:
                print("✗ topic_news_map 表無資料")
                return []
        except Exception as e:
            print(f"✗ 獲取 topic_news_map 資料時發生錯誤: {e}")
            return []
    
    def group_by_topic_id(self, topic_news_map):
        """根據 topic_id 將新聞分組"""
        topic_groups = {}
        for item in topic_news_map:
            topic_id = item.get('topic_id')
            story_id = item.get('story_id')
            if topic_id and story_id:
                if topic_id not in topic_groups:
                    topic_groups[topic_id] = []
                topic_groups[topic_id].append(story_id)
        
        print(f"✓ 根據 topic_id 分成 {len(topic_groups)} 個主題組")
        for topic_id, story_ids in topic_groups.items():
            print(f"  主題 {topic_id}: {len(story_ids)} 則新聞")
        return topic_groups
    
    def fetch_news_from_supabase(self, story_ids):
        """從 Supabase 批次獲取新聞內容"""
        news_items = []
        if not story_ids:
            return news_items
            
        print(f"開始從 Supabase 批次獲取 {len(story_ids)} 則新聞...")
        try:
            response = self.supabase.table('single_news').select(
                'story_id, news_title, long'
            ).in_('story_id', story_ids).execute()

            if response.data:
                id_to_news_map = {item['story_id']: item for item in response.data}
                # 按照傳入的 story_ids 順序重組，確保與向量順序一致
                for story_id in story_ids:
                    if story_id in id_to_news_map:
                        news_data = id_to_news_map[story_id]
                        news_items.append({
                            'story_id': news_data.get('story_id'),
                            'news_title': news_data.get('news_title', ''),
                            'content': news_data.get('long', '')
                        })
                    else:
                         print(f"✗ story_id {story_id} 在 single_news 表中未找到")
            
            print(f"✓ 成功獲取 {len(news_items)}/{len(story_ids)} 則新聞內容")
        except Exception as e:
            print(f"✗ 批次獲取新聞時發生錯誤: {e}")
        return news_items

    def group_news_by_vectors(self, news_items):
        """使用語意向量和DBSCAN分群演算法將新聞分組為事件分支"""
        if not self.use_ai or len(news_items) < 2:
            print("AI客戶端未初始化或新聞數量不足，切換到簡單分組模式...")
            return self.simple_group_news(news_items)
            
        print("步驟 1/3: 開始使用 Gemini AI 產生新聞語意向量...")
        texts_to_embed = [
            f"{news['news_title']}\n{news['content'][:500]}" for news in news_items
        ]
        
        try:
            # 使用正確的 API 方法處理多個文本
            embeddings = []
            for text in texts_to_embed:
                result = self.genai_client.models.embed_content(
                    model="models/text-embedding-004",
                    contents=text  # 移除不支援的 task_type 參數
                )
                # 正確提取 embedding 數據：EmbedContentResponse.embeddings[0].values
                if hasattr(result, 'embeddings') and len(result.embeddings) > 0:
                    embedding = result.embeddings[0]  # 取第一個 ContentEmbedding
                    if hasattr(embedding, 'values'):
                        embeddings.append(embedding.values)
                    else:
                        embeddings.append(embedding)
                elif hasattr(result, 'embedding') and hasattr(result.embedding, 'values'):
                    embeddings.append(result.embedding.values)
                elif hasattr(result, 'embedding'):
                    embeddings.append(result.embedding)
                else:
                    # 如果是 EmbedContentResponse 物件，打印其屬性以除錯
                    print(f"偵錯：result 類型 = {type(result)}, 屬性 = {dir(result)}")
                    embeddings.append(result)
            print(f"✓ 成功生成 {len(embeddings)} 個新聞向量")
        except Exception as e:
            print(f"✗ AI 生成向量時發生錯誤: {e}")
            print("切換到簡單分組模式...")
            return self.simple_group_news(news_items)

        print("步驟 2/3: 使用多種演算法進行新聞分群並選擇最佳結果...")
        try:
            # 確保 embeddings 是數值陣列
            processed_embeddings = []
            for i, emb in enumerate(embeddings):
                if isinstance(emb, (list, tuple)) and all(isinstance(x, (int, float)) for x in emb):
                    processed_embeddings.append(emb)
                else:
                    # 嘗試轉換為數值
                    if hasattr(emb, 'values'):
                        processed_embeddings.append(emb.values)
                    elif hasattr(emb, 'tolist'):
                        processed_embeddings.append(emb.tolist())
                    else:
                        print(f"無法處理第 {i} 個 embedding，跳過")
                        continue
            
            X = np.array(processed_embeddings)
            print(f"✓ 成功準備 {len(processed_embeddings)} 個向量，維度：{X.shape}")
        except Exception as e:
            print(f"✗ 準備向量時發生錯誤: {e}")
            print("切換到簡單分組模式...")
            return self.simple_group_news(news_items)
        
        # 使用多種演算法並選擇最佳結果
        best_labels, best_algorithm, best_score = self._find_best_clustering(X, len(news_items))
        
        labels = best_labels
        num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        num_noise = list(labels).count(-1)
        print(f"✓ 最佳分群演算法：{best_algorithm}，找到 {num_clusters} 個事件分支和 {num_noise} 則獨立新聞")
        print(f"  分群品質評分：{best_score:.3f}")
        
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(news_items[i])
            
        print("步驟 3/3: 為每個事件分支生成標題和摘要...")
        event_groups = []
        
        # 處理正常分群的新聞
        normal_clusters = {k: v for k, v in clusters.items() if k != -1}
        noise_news = clusters.get(-1, [])
        
        # 如果有噪音點（未分群的新聞），嘗試將它們分配到最相似的分群中
        if noise_news:
            print(f"  正在重新分配 {len(noise_news)} 則未分群新聞到最相似的分支...")
            noise_indices = [i for i, label in enumerate(labels) if label == -1]
            
            for noise_idx in noise_indices:
                noise_vector = X[noise_idx:noise_idx+1]  # 保持2D格式
                best_cluster = -1
                best_similarity = -1
                
                # 計算與每個分群的平均相似度
                for cluster_label, cluster_news in normal_clusters.items():
                    cluster_indices = [i for i, label in enumerate(labels) if label == cluster_label]
                    if cluster_indices:
                        cluster_vectors = X[cluster_indices]
                        # 計算與該分群的平均相似度
                        similarities = cosine_similarity(noise_vector, cluster_vectors)[0]
                        avg_similarity = np.mean(similarities)
                        
                        if avg_similarity > best_similarity:
                            best_similarity = avg_similarity
                            best_cluster = cluster_label
                
                # 將噪音新聞分配到最相似的分群
                if best_cluster != -1 and best_similarity > 0.3:  # 相似度閾值
                    normal_clusters[best_cluster].append(news_items[noise_idx])
                    print(f"    新聞 {noise_idx+1} 已分配到分支 {best_cluster+1} (相似度: {best_similarity:.3f})")
                else:
                    # 如果相似度太低，創建新的單獨分支
                    new_label = max(normal_clusters.keys()) + 1 if normal_clusters else 0
                    normal_clusters[new_label] = [news_items[noise_idx]]
                    print(f"    新聞 {noise_idx+1} 創建新分支 {new_label+1}")
        
        # 處理所有分群（現在不會有噪音點了）
        for label, grouped_news in normal_clusters.items():
            print(f"  正在處理分支 {label+1} ({len(grouped_news)} 則新聞)...")
            title, summary = self._generate_event_title_and_summary_for_group(grouped_news)
            event_groups.append({
                'event_id': str(uuid.uuid4()),
                'event_title': title,
                'event_summary': summary,
                'news_count': len(grouped_news),
                'news_items': grouped_news
            })
            
        return event_groups

    def _find_best_clustering(self, X, n_samples):
        """嘗試多種分群演算法並選擇最佳結果 - 偏好更細緻的分群"""
        print("正在測試多種分群演算法...")
        
        algorithms = []
        # 調整參數以產生更多細緻分群
        max_clusters = min(8, max(3, n_samples // 1.5))  # 增加最大分群數，降低最小樣本要求
        
        # 1. 階層式分群 (Agglomerative) - 測試更多分群數
        print("  測試階層式分群...")
        for n_clusters in range(2, int(max_clusters) + 1):
            try:
                agg = AgglomerativeClustering(
                    n_clusters=n_clusters, 
                    metric='cosine', 
                    linkage='average'
                )
                labels = agg.fit_predict(X)
                score = self._evaluate_clustering(X, labels)
                algorithms.append(('Agglomerative', labels, score, n_clusters))
                print(f"    n_clusters={n_clusters}: 分群評分={score:.3f}")
            except Exception as e:
                print(f"    n_clusters={n_clusters}: 失敗 ({e})")
        
        # 2. 改良型 DBSCAN - 使用更嚴格的參數產生更多分群
        print("  測試改良型 DBSCAN...")
        eps_values = [0.03, 0.05, 0.07, 0.08, 0.1, 0.12, 0.15]  # 加入更小的 eps 值
        for eps in eps_values:
            try:
                dbscan = DBSCAN(eps=eps, min_samples=2, metric='cosine')
                labels = dbscan.fit_predict(X)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                if n_clusters >= 2 and n_clusters <= max_clusters:
                    score = self._evaluate_clustering(X, labels)
                    algorithms.append(('DBSCAN', labels, score, eps))
                    print(f"    eps={eps}: {n_clusters}個分支, 分群評分={score:.3f}")
            except Exception as e:
                print(f"    eps={eps}: 失敗 ({e})")
        
        # 3. K-means++ - 測試更多分群數
        print("  測試 K-means++...")
        for n_clusters in range(2, int(max_clusters) + 1):
            try:
                kmeans = KMeans(
                    n_clusters=n_clusters, 
                    init='k-means++', 
                    n_init=20,
                    random_state=42
                )
                labels = kmeans.fit_predict(X)
                score = self._evaluate_clustering(X, labels)
                algorithms.append(('K-means++', labels, score, n_clusters))
                print(f"    n_clusters={n_clusters}: 分群評分={score:.3f}")
            except Exception as e:
                print(f"    n_clusters={n_clusters}: 失敗 ({e})")
        
        # 4. 語義相似度閾值分群 - 使用更嚴格的閾值
        print("  測試語義相似度閾值分群...")
        try:
            labels = self._semantic_threshold_clustering(X)
            if labels is not None:
                n_clusters = len(set(labels))
                if n_clusters >= 2:
                    score = self._evaluate_clustering(X, labels)
                    algorithms.append(('SemanticThreshold', labels, score, 'adaptive'))
                    print(f"    自適應閾值: {n_clusters}個分支, 分群評分={score:.3f}")
        except Exception as e:
            print(f"    語義閾值分群失敗: {e}")
        
        # 5. 新增：多層次階層分群 - 產生更細緻的分群
        print("  測試多層次階層分群...")
        try:
            labels = self._hierarchical_refined_clustering(X)
            if labels is not None:
                n_clusters = len(set(labels))
                if n_clusters >= 2:
                    score = self._evaluate_clustering(X, labels)
                    algorithms.append(('HierarchicalRefined', labels, score, 'multi-level'))
                    print(f"    多層次分群: {n_clusters}個分支, 分群評分={score:.3f}")
        except Exception as e:
            print(f"    多層次階層分群失敗: {e}")
        
        # 選擇最佳演算法
        if not algorithms:
            print("  所有演算法都失敗，使用簡單分群")
            return list(range(n_samples)), "Simple", 0.0
        
        # 根據評分選擇最佳結果，但偏好更多分群的結果
        best_algo, best_labels, best_score, best_param = max(algorithms, key=lambda x: x[2])
        print(f"✓ 最佳演算法：{best_algo} (參數: {best_param}), 評分: {best_score:.3f}")
        
        return best_labels, f"{best_algo}(param={best_param})", best_score
    
    def _evaluate_clustering(self, X, labels):
        """評估分群品質 - 偏好精細但有意義的分群"""
        try:
            unique_labels = set(labels)
            n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
            
            if n_clusters < 2:
                return 0.0
            
            # 計算噪音點比例，並給予懲罰
            noise_ratio = list(labels).count(-1) / len(labels) if len(labels) > 0 else 0
            noise_penalty = 1.0 - noise_ratio * 0.4  # 降低噪音懲罰，允許一些噪音點
            
            # 移除噪音點進行評估
            if -1 in labels:
                mask = labels != -1
                if np.sum(mask) < 2:
                    return 0.0
                X_clean = X[mask]
                labels_clean = labels[mask]
            else:
                X_clean = X
                labels_clean = labels
            
            # 輪廓係數 (Silhouette Score) - 衡量分群內緊密度與分群間分離度
            sil_score = silhouette_score(X_clean, labels_clean, metric='cosine')
            
            # Calinski-Harabasz 指數 - 衡量分群間差異與分群內差異的比值
            ch_score = calinski_harabasz_score(X_clean, labels_clean)
            ch_score_normalized = min(ch_score / 1000, 1.0)  # 標準化到 0-1
            
            # 調整分群數量偏好 - 偏好更多分群但不過度
            total_samples = len(X)
            if total_samples <= 8:
                ideal_min, ideal_max = 3, 5
            elif total_samples <= 15:
                ideal_min, ideal_max = 4, 7
            else:
                ideal_min, ideal_max = 5, 8
            
            if ideal_min <= n_clusters <= ideal_max:
                cluster_bonus = 1.1  # 在理想範圍內給予加分
            elif n_clusters > ideal_max:
                cluster_bonus = 1.0 - (n_clusters - ideal_max) * 0.05  # 過多分群輕微懲罰
            else:
                cluster_bonus = 0.8  # 分群太少重重懲罰
            
            # 分群大小多樣性 - 允許大小不一的分群，但避免極端不平衡
            cluster_sizes = [np.sum(labels_clean == label) for label in set(labels_clean)]
            min_size, max_size = min(cluster_sizes), max(cluster_sizes)
            if min_size == 0:
                size_diversity = 0.5
            else:
                size_ratio = max_size / min_size
                if size_ratio <= 3:  # 允許3倍的大小差異
                    size_diversity = 1.0
                else:
                    size_diversity = max(0.3, 1.0 - (size_ratio - 3) * 0.1)
            
            # 內群緊密度 - 計算每個分群內部的平均相似度
            intra_cluster_scores = []
            for label in set(labels_clean):
                cluster_mask = labels_clean == label
                cluster_vectors = X_clean[cluster_mask]
                if len(cluster_vectors) > 1:
                    cluster_sim_matrix = cosine_similarity(cluster_vectors)
                    # 取上三角（排除對角線）的平均相似度
                    upper_triangle = cluster_sim_matrix[np.triu_indices_from(cluster_sim_matrix, k=1)]
                    if len(upper_triangle) > 0:
                        intra_cluster_scores.append(np.mean(upper_triangle))
                else:
                    intra_cluster_scores.append(1.0)  # 單個樣本的分群給滿分
            
            intra_cohesion = np.mean(intra_cluster_scores) if intra_cluster_scores else 0.5
            
            # 綜合評分 - 重新調整權重以偏好精細分群
            final_score = (
                sil_score * 0.3 +           # 降低輪廓係數權重
                ch_score_normalized * 0.15 + # 降低 CH 指數權重
                cluster_bonus * 0.25 +       # 增加分群數量偏好權重
                noise_penalty * 0.15 +       # 保持噪音懲罰
                size_diversity * 0.1 +       # 新增大小多樣性
                intra_cohesion * 0.15        # 新增內群緊密度
            )
            return max(0.0, min(1.5, final_score))  # 允許超過1.0的分數
            
        except Exception:
            return 0.0
    
    def _semantic_threshold_clustering(self, X):
        """基於語義相似度閾值的自定義分群演算法 - 確保沒有孤立點"""
        try:
            # 計算餘弦相似度矩陣
            similarity_matrix = cosine_similarity(X)
            
            # 嘗試多個閾值，找到產生最佳分群的閾值
            upper_triangle = similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]
            percentiles = [60, 65, 70, 75, 80]  # 嘗試多個百分位數
            
            best_labels = None
            best_score = -1
            
            for p in percentiles:
                threshold = np.percentile(upper_triangle, p)
                labels = self._graph_clustering_with_merge(similarity_matrix, threshold)
                
                if labels is not None:
                    # 評估這個分群結果
                    n_clusters = len(set(labels))
                    if 2 <= n_clusters <= 6:  # 合理的分群數量範圍
                        score = self._evaluate_clustering(X, labels)
                        if score > best_score:
                            best_score = score
                            best_labels = labels
            
            return best_labels
            
        except Exception:
            return None
    
    def _graph_clustering_with_merge(self, similarity_matrix, threshold):
        """圖論分群並合併小分群以避免孤立點"""
        try:
            # 建立相似度圖
            adjacency = similarity_matrix > threshold
            n = len(similarity_matrix)
            
            # 使用深度優先搜索找連通分量
            visited = [False] * n
            components = []
            
            def dfs(node, component):
                visited[node] = True
                component.append(node)
                for neighbor in range(n):
                    if adjacency[node][neighbor] and not visited[neighbor]:
                        dfs(neighbor, component)
            
            # 找所有連通分量
            for i in range(n):
                if not visited[i]:
                    component = []
                    dfs(i, component)
                    components.append(component)
            
            # 合併過小的分群到最相似的大分群中
            large_components = [comp for comp in components if len(comp) >= 2]
            small_components = [comp for comp in components if len(comp) == 1]
            
            # 將小分群合併到最相似的大分群
            for small_comp in small_components:
                node = small_comp[0]
                best_target = 0
                best_similarity = -1
                
                for i, large_comp in enumerate(large_components):
                    # 計算與大分群的平均相似度
                    similarities = [similarity_matrix[node][target] for target in large_comp]
                    avg_sim = np.mean(similarities)
                    
                    if avg_sim > best_similarity:
                        best_similarity = avg_sim
                        best_target = i
                
                # 將小分群合併到最相似的大分群
                if large_components and best_similarity > 0.2:  # 最低相似度閾值
                    large_components[best_target].extend(small_comp)
                else:
                    # 如果相似度太低，就合併到最近的大分群
                    if large_components:
                        large_components[0].extend(small_comp)
            
            # 生成最終標籤
            labels = [-1] * n
            for i, component in enumerate(large_components):
                for node in component:
                    labels[node] = i
            
            return np.array(labels)
            
        except Exception:
            return None
    
    def _hierarchical_refined_clustering(self, X, n_clusters=None):
        """
        層次精細化分群 - 先用較鬆的條件分群，再細分每個大群
        """
        try:
            n_samples = len(X)
            if n_samples < 4:
                return np.zeros(n_samples, dtype=int)
            
            # 第一層：較寬鬆的分群
            initial_clusters = min(4, n_samples // 2)
            
            # 使用 K-means++ 做初步分群
            kmeans_initial = KMeans(
                n_clusters=initial_clusters, 
                init='k-means++', 
                random_state=42, 
                n_init=10
            )
            initial_labels = kmeans_initial.fit_predict(X)
            
            final_labels = np.copy(initial_labels)
            current_max_label = np.max(initial_labels)
            
            # 第二層：對每個初步分群進行細分
            for cluster_id in range(initial_clusters):
                cluster_mask = initial_labels == cluster_id
                cluster_points = X[cluster_mask]
                
                if len(cluster_points) >= 4:  # 只對有足夠點數的群組進行細分
                    # 計算群組內的相似度分佈
                    similarity_matrix = cosine_similarity(cluster_points)
                    avg_similarity = np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])
                    
                    # 如果群組內相似度較低，嘗試細分
                    if avg_similarity < 0.7:  # 相似度閾值
                        # 使用 AgglomerativeClustering 進行細分
                        n_sub_clusters = min(3, len(cluster_points) // 2)
                        if n_sub_clusters > 1:
                            agg_clustering = AgglomerativeClustering(
                                n_clusters=n_sub_clusters,
                                metric='cosine',
                                linkage='average'
                            )
                            sub_labels = agg_clustering.fit_predict(cluster_points)
                            
                            # 將細分結果映射回原始標籤
                            for i, (original_idx, sub_label) in enumerate(zip(np.where(cluster_mask)[0], sub_labels)):
                                if sub_label > 0:  # 保留第一個子群的原始標籤
                                    final_labels[original_idx] = current_max_label + sub_label
                            
                            current_max_label += np.max(sub_labels)
            
            return final_labels
            
        except Exception as e:
            print(f"層次精細化分群錯誤: {e}")
            # 降級到簡單 K-means
            n_clusters = min(n_clusters or 5, len(X) // 2) if n_clusters else min(5, len(X) // 2)
            if n_clusters < 2:
                return np.zeros(len(X), dtype=int)
            
            kmeans = KMeans(n_clusters=n_clusters, init='k-means++', random_state=42, n_init=10)
            return kmeans.fit_predict(X)

    def _generate_event_title_and_summary_for_group(self, news_group):
        """為一個已分群的新聞組生成標題和摘要"""
        if not self.use_ai:
            return f"綜合事件", f"包含 {len(news_group)} 則新聞的事件"

        news_summaries = []
        for news in news_group[:5]: # 最多取前5則新聞做參考
            summary = f"標題: {news['news_title']}\n內容: {news['content'][:200]}..."
            news_summaries.append(summary)

        prompt = f"""
請分析以下屬於同一個事件的新聞摘要，為這個核心事件生成一個精煉的標題和總結。

新聞摘要:
{"-"*20}\n{chr(10).join(news_summaries)}\n{"-"*20}

請嚴格按照以下 JSON 格式輸出：
{{
  "event_title": "精煉且具體的事件標題 (10字以內)",
  "event_summary": "對整個事件的簡潔摘要 (80字以內)"
}}

**重要**: 只回傳 JSON 物件，不要包含任何額外的解釋或 markdown 格式。
"""
        try:
            response = self.genai_client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt
            )
            result_text = response.text.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text[7:-3].strip()
            
            result = json.loads(result_text)
            title = result.get('event_title', f"綜合事件 ({len(news_group)}則)")
            summary = result.get('event_summary', "此事件的綜合報導。")
            return title, summary
        except Exception as e:
            print(f"  ✗ AI 生成標題摘要時出錯: {e}")
            fallback_title = news_group[0]['news_title'] if news_group else "綜合事件"
            return fallback_title[:15], f"包含 {len(news_group)} 則相關新聞的事件"
            
    def simple_group_news(self, news_items):
        """簡單的新聞分組（不使用 AI 時的備用方案）"""
        return [{
            'event_id': str(uuid.uuid4()),
            'event_title': '綜合新聞事件',
            'event_summary': f'包含 {len(news_items)} 則相關新聞的綜合事件',
            'news_count': len(news_items),
            'news_items': news_items
        }]
    
    def save_to_database(self, event_groups, save_mode="both"):
        """將事件分支和新聞映射存入資料庫"""
        try:
            print(f"\n開始資料庫儲存流程 (模式: {save_mode})...")
            topic_branch_news_map_data, topic_branch_data = [], []
            for topic_group in event_groups:
                topic_id = topic_group.get('topic_id')
                for sub_event in topic_group.get('sub_events', []):
                    topic_branch_id = sub_event.get('event_id')
                    if topic_id and topic_branch_id and sub_event.get('event_title'):
                        topic_branch_data.append({
                            'topic_id': topic_id,
                            'topic_branch_id': topic_branch_id,
                            'topic_branch_title': sub_event.get('event_title'),
                            'topic_branch_content': sub_event.get('event_summary', '')
                        })
                        for news_item in sub_event.get('news_items', []):
                            if news_item.get('story_id'):
                                topic_branch_news_map_data.append({
                                    'topic_branch_id': topic_branch_id,
                                    'story_id': news_item.get('story_id')
                                })
            
            print(f"準備資料: {len(topic_branch_data)} 個分支, {len(topic_branch_news_map_data)} 筆新聞對應")
            if save_mode in ["preview", "both"]:
                self._save_database_preview(topic_branch_data, topic_branch_news_map_data)
            if save_mode in ["database", "both"]:
                self._save_to_actual_database(topic_branch_data, topic_branch_news_map_data)
        except Exception as e:
            print(f"✗ 資料庫儲存流程發生錯誤: {e}")
    
    def _save_database_preview(self, topic_branch_data, topic_branch_news_map_data):
        """儲存資料庫預覽檔案"""
        try:
            print("\n--- 生成資料庫預覽檔案 ---")
            for name, data in [("topic_branch", topic_branch_data), ("topic_branch_news_map", topic_branch_news_map_data)]:
                filename = f"database_preview_{name}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✓ {name} 預覽已儲存: {filename} ({len(data)} 筆)")
        except Exception as e:
            print(f"✗ 生成預覽檔案時發生錯誤: {e}")
    
    def _save_to_actual_database(self, topic_branch_data, topic_branch_news_map_data):
        """分批儲存到實際資料庫"""
        print("\n--- 開始儲存到實際資料庫 ---")
        for table_name, data, batch_size in [("topic_branch", topic_branch_data, 50), ("topic_branch_news_map", topic_branch_news_map_data, 100)]:
            print(f"儲存 {table_name} 資料...")
            if not data:
                print(f"  {table_name} 無資料需儲存。")
                continue

            success_count = 0
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                try:
                    self.supabase.table(table_name).upsert(batch).execute()
                    success_count += len(batch)
                    print(f"  ✓ {table_name} 第 {i//batch_size + 1} 批 ({len(batch)} 筆) 成功")
                except Exception as e:
                    print(f"  ✗ {table_name} 第 {i//batch_size + 1} 批發生錯誤: {e}")
            print(f"  → {table_name} 總計成功儲存: {success_count}/{len(data)} 筆")
        print("\n✅ 資料庫儲存完成！")

    def save_to_json(self, data, output_path):
        """將結果儲存到 JSON 檔案"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ 處理結果已儲存至: {output_path}")
        except Exception as e:
            print(f"✗ 儲存 JSON 檔案時發生錯誤: {e}")
    
    def process_from_topic_map(self, output_path, save_to_db=True):
        """主要處理流程：從 topic_news_map 開始"""
        print("=" * 60)
        print("新聞事件分組器 - 處理流程啟動")
        print("=" * 60)
        
        topic_news_map = self.fetch_topic_news_map_from_supabase()
        if not topic_news_map: return
        
        topic_groups = self.group_by_topic_id(topic_news_map)
        if not topic_groups: return
        
        all_topic_events = []
        for topic_id, story_ids in topic_groups.items():
            print(f"\n{'='*20} 處理主題 {topic_id} ({len(story_ids)} 則新聞) {'='*20}")
            news_items = self.fetch_news_from_supabase(story_ids)
            if not news_items:
                print(f"✗ 主題 {topic_id}: 未獲取到有效新聞內容，跳過此主題")
                continue
            
            topic_title, _ = self._generate_event_title_and_summary_for_group(news_items)
            print(f"✓ 主題 {topic_id} AI命名為: {topic_title}")
            
            if len(news_items) <= 3: # 新聞數量少，不需細分
                _, topic_summary = self._generate_event_title_and_summary_for_group(news_items)
                sub_events = [{
                    'event_id': str(uuid.uuid4()), 'event_title': topic_title,
                    'event_summary': topic_summary, 'news_count': len(news_items),
                    'news_items': news_items
                }]
                print(f"  → 新聞量少，視為單一分支")
            else: # 新聞數量多，進行AI細分
                print(f"  → 新聞量多，正在進行 AI 細分 (向量化+分群)...")
                sub_events = self.group_news_by_vectors(news_items)
            
            all_topic_events.append({
                'topic_id': topic_id, 'topic_title': topic_title, 'sub_events': sub_events
            })
            print(f"  → 主題 {topic_id} 已細分為 {len(sub_events)} 個分支")
        
        self.save_to_json(all_topic_events, output_path)
        self.save_to_database(all_topic_events, "both" if save_to_db else "preview")
        
        # 輸出最終統計資訊
        self._print_summary_stats(topic_groups, all_topic_events)
        return all_topic_events

    def _print_summary_stats(self, topic_groups, all_topic_events):
        print("\n" + "=" * 60)
        print("處理完成 - 最終統計資訊")
        print("=" * 60)
        total_sub_events = sum(len(t['sub_events']) for t in all_topic_events)
        total_news = sum(sum(se['news_count'] for se in t['sub_events']) for t in all_topic_events)
        print(f"原始主題數量: {len(topic_groups)}")
        print(f"成功處理的主題: {len(all_topic_events)}")
        print(f"產生的總分支數量: {total_sub_events}")
        print(f"納入分支的總新聞數: {total_news}")
        for i, topic in enumerate(all_topic_events, 1):
            print(f"\n主題 {i}: {topic['topic_title']} (ID: {topic['topic_id']})")
            for j, sub_event in enumerate(topic['sub_events'], 1):
                print(f"  分支 {j}: {sub_event['event_title']} ({sub_event['news_count']} 則新聞)")

def main():
    """主程式入口"""
    print("🚀 新聞事件分組器 - 啟動中...")
    
    # 檢查命令列參數
    test_mode = False
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command in ['test', '--test', '-t']:
            test_mode = True
            print("🧪 測試模式：只生成預覽檔案，不寫入資料庫")
        elif command in ['help', '--help', '-h']:
            print("\n使用方式:")
            print("  python new_complete_news_grouper.py           # 正常模式（寫入資料庫）")
            print("  python new_complete_news_grouper.py test      # 測試模式（只生成預覽）")
            print("  python new_complete_news_grouper.py --help    # 顯示此幫助")
            return
    
    if not test_mode:
        print("💾 模式：從 topic_news_map 讀取資料，AI分組後儲存到資料庫")
    
    print("=" * 60)
    
    try:
        grouper = NewsEventGrouper()
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"topic_grouped_news_{timestamp}.json"
    print(f"📄 結果將儲存到: {output_path}")
    
    if test_mode:
        print("📋 將只生成預覽檔案，不會寫入資料庫")
    else:
        print("💾 將同時生成預覽檔案並儲存到資料庫")
    print()
    
    try:
        result = grouper.process_from_topic_map(output_path, save_to_db=(not test_mode))
        if result:
            if test_mode:
                print("\n🎉 測試完成！請檢查預覽檔案:")
                print("  - database_preview_topic_branch.json")
                print("  - database_preview_topic_branch_news_map.json")
                print(f"  - {output_path}")
            else:
                print("\n🎉 全部處理完成！")
        else:
            print("\n⚠️ 處理未完成或無資料，請檢查上方輸出訊息。")
    except KeyboardInterrupt:
        print("\n\n⏹️ 使用者中斷程式執行。")
    except Exception as e:
        print(f"\n❌ 執行過程中發生未預期錯誤: {e}")
    
    print("\n程式結束。")

if __name__ == "__main__":
    main()