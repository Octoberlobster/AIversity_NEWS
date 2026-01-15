import * as d3 from 'd3';
import { supabase } from './supabase';
import './../css/FiveW1HVisualization.css';

export class FiveW1HVisualization {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.options = {
      width: options.width || 1200,
      height: options.height || 600,
      dragLimit: options.dragLimit || 50,
      isHeaderMode: containerId === 'header-mindmap',
      ...options
    };
    
    this.data = null;
    this.svg = null;
    this.g = null;
    this.simulation = null;
    this.transform = { x: 0, y: 0, k: 1 };
    this.t = options.t || ((key) => key); // 接收翻譯函數，如果沒有則返回 key
    this.getFieldName = options.getFieldName || ((fieldName) => fieldName); // 接收 getFieldName 函數
    this.topicTitle = options.topicTitle || this.t('fiveW1H.defaultTitle');
    this.topicId = options.topicId || null; // 接收 topic_id 參數
  }

  async loadData() {
    try {
      // 優先從Supabase獲取資料
      console.log('正在從Supabase載入資料，主題:', this.topicTitle, '，ID:', this.topicId);
      
      // 檢查Supabase連接
      if (!supabase) {
        console.error('❌ Supabase客戶端未初始化');
        this.data = this.getDefaultData();
        return;
      }
      
      console.log('🔍 開始Supabase查詢...');
      let data, error;
      
      // 獲取當前語言對應的 mind_map_detail 欄位名稱
      const langSpecificField = this.getFieldName('mind_map_detail');
      console.log('📋 使用欄位:', langSpecificField);
      
      // 優先使用 topic_id 查詢，如果沒有則用 topic_title
      if (this.topicId) {
        console.log('🎯 使用 topic_id 查詢:', this.topicId);
        ({ data, error } = await supabase
          .from("topic")
          .select(`mind_map_detail, ${langSpecificField}`)
          .eq("topic_id", this.topicId));
      } else {
        console.log('📝 使用 topic_title 查詢:', this.topicTitle);
        ({ data, error } = await supabase
          .from("topic")
          .select(`mind_map_detail, ${langSpecificField}`)
          .eq("topic_title", this.topicTitle));
      }

      console.log('📊 Supabase查詢結果:', { data, error });

      if (error) {
        console.error("❌ Supabase Error:", error);
        console.error("❌ Supabase Error Details:", JSON.stringify(error, null, 2));
        console.warn('使用預設資料作為備用方案');
        this.data = this.getDefaultData();
        return;
      }
      
      if (!data || data.length === 0) {
        console.warn("⚠️ 沒找到資料，使用預設資料");
        this.data = this.getDefaultData();
        return;
      }
      
      console.log("✅ 查到資料:", data[0]);
      console.log("📋 資料結構:", typeof data[0], data[0] ? Object.keys(data[0]) : 'null');
      
      // 優先使用當前語言的欄位，如果沒有則 fallback 到預設欄位
      const mindMapField = this.getFieldName('mind_map_detail');
      const mindMapDetailData = data[0][mindMapField] || data[0].mind_map_detail;
      
      if (mindMapDetailData) {
        try {
          console.log("🔄 開始轉換資料...");
          console.log("📋 使用欄位:", mindMapField);
          console.log("📋 mind_map_detail 內容:", mindMapDetailData);
          console.log("📋 mind_map_detail 類型:", typeof mindMapDetailData);
          
          // 檢查是否為字串格式的JSON
          let mindMapData = mindMapDetailData;
          if (typeof mindMapData === 'string') {
            try {
              mindMapData = JSON.parse(mindMapData);
              console.log("🔄 成功解析JSON字串:", mindMapData);
            } catch (parseError) {
              console.error('❌ JSON解析失敗:', parseError);
              throw new Error('JSON解析失敗');
            }
          }
          
          this.data = this.transformSupabaseData(mindMapData);
          console.log('✅ 成功從Supabase載入資料:', this.data);
        } catch (transformError) {
          console.error('❌ 資料轉換失敗:', transformError);
          console.error('❌ 轉換錯誤詳情:', JSON.stringify(transformError, null, 2));
          console.warn('使用預設資料作為備用方案');
          this.data = this.getDefaultData();
        }
      } else {
        console.warn('⚠️ Supabase中沒有找到對應的資料，使用預設資料');
        this.data = this.getDefaultData();
      }
    } catch (error) {
      console.error('❌ 載入資料失敗:', error);
      console.error('❌ 錯誤詳情:', JSON.stringify(error, null, 2));
      console.warn('使用預設資料作為備用方案');
      this.data = this.getDefaultData();
    }
  }

  transformSupabaseData(mindMapData) {
    console.log('🔄 開始轉換資料，輸入:', mindMapData);
    console.log('📋 輸入資料類型:', typeof mindMapData);
    console.log('📋 輸入資料鍵值:', mindMapData ? Object.keys(mindMapData) : 'null');
    
    if (!mindMapData || typeof mindMapData !== 'object') {
      console.error('❌ 輸入資料無效:', mindMapData);
      throw new Error('輸入資料無效或為空');
    }
    
    const nodes = [];
    const links = [];

    // 添加中心節點
    if (mindMapData.center_node) {
      console.log('📍 處理中心節點:', mindMapData.center_node);
      nodes.push({
        id: mindMapData.center_node.id || 'center',
        label: mindMapData.center_node.label || this.topicTitle,
        type: 'center',
        description: mindMapData.center_node.description || this.t('fiveW1H.centerDescription', { topicTitle: this.topicTitle }),
        x: 190, 
        y: 140
      });
    } else {
      console.warn('⚠️ 沒有找到中心節點資料，創建預設中心節點');
      nodes.push({
        id: 'center',
        label: this.topicTitle,
        type: 'center',
        description: this.t('fiveW1H.centerDescription', { topicTitle: this.topicTitle }),
        x: 190, 
        y: 140
      });
    }

    // 添加主要節點 (5W1H)
    if (mindMapData.main_nodes && Array.isArray(mindMapData.main_nodes)) {
      console.log('🔗 處理主要節點，數量:', mindMapData.main_nodes.length);
      mindMapData.main_nodes.forEach((node, index) => {
        console.log(`  📌 節點 ${index}:`, node);
        const category = node.id || node.category; // who, what, when, where, why, how
        nodes.push({
          id: node.id || category,
          label: node.id || node.label || node.name || category.toUpperCase(),
          type: '5w1h',
          category: category,
          description: node.description || this.t('fiveW1H.categoryRelatedContent', { category })
        });
        
        // 連接到中心節點
        links.push({
          source: 'center',
          target: node.id || category
        });
      });
    } else {
      console.warn('⚠️ 沒有找到主要節點資料，創建預設5W1H節點');
      // 創建預設的5W1H節點
      const defaultCategories = ['who', 'what', 'when', 'where', 'why', 'how'];
      defaultCategories.forEach(category => {
        nodes.push({
          id: category,
          label: category.toUpperCase(),
          type: '5w1h',
          category: category,
          description: this.t('fiveW1H.categoryRelatedContent', { category })
        });
        
        links.push({
          source: 'center',
          target: category
        });
      });
    }

    console.log('✅ 轉換完成:');
    console.log('  📊 節點數量:', nodes.length);
    console.log('  🔗 連接數量:', links.length);
    console.log('  📋 節點資料:', nodes);
    console.log('  🔗 連接資料:', links);
    
    // 返回完整的資料結構，包括詳細節點資訊
    return {
      nodes,
      links,
      center_node: mindMapData.center_node,
      main_nodes: mindMapData.main_nodes,
      detailed_nodes: mindMapData.detailed_nodes
    };
  }

  getCategoryChineseName(category) {
    return this.t(`fiveW1H.categories.${category}.name`, category);
  }

  getCategoryDescription(category) {
    return this.t(`fiveW1H.categories.${category}.description`, this.t('fiveW1H.categoryRelatedContent', { category }));
  }

  getHeaderModeData() {
    const topicTitle = this.topicTitle || this.t('fiveW1H.defaultTitle');
    
    return {
      nodes: [
        { 
          id: 'center', 
          label: topicTitle, 
          type: 'center', 
          description: this.t('fiveW1H.centerDescription', { topicTitle }),
          x: 190, y: 140
        },
        { 
          id: 'who', 
          label: `Who\n${this.t('fiveW1H.categories.who.name')}`, 
          type: '5w1h', 
          category: 'who',
          description: this.t('fiveW1H.categories.who.description')
        },
        { 
          id: 'what', 
          label: `What\n${this.t('fiveW1H.categories.what.name')}`, 
          type: '5w1h', 
          category: 'what',
          description: this.t('fiveW1H.categories.what.description')
        },
        { 
          id: 'when', 
          label: `When\n${this.t('fiveW1H.categories.when.name')}`, 
          type: '5w1h', 
          category: 'when',
          description: this.t('fiveW1H.categories.when.description')
        },
        { 
          id: 'where', 
          label: `Where\n${this.t('fiveW1H.categories.where.name')}`, 
          type: '5w1h', 
          category: 'where',
          description: this.t('fiveW1H.categories.where.description')
        },
        { 
          id: 'why', 
          label: `Why\n${this.t('fiveW1H.categories.why.name')}`, 
          type: '5w1h', 
          category: 'why',
          description: this.t('fiveW1H.categories.why.description')
        },
        { 
          id: 'how', 
          label: `How\n${this.t('fiveW1H.categories.how.name')}`, 
          type: '5w1h', 
          category: 'how',
          description: this.t('fiveW1H.categories.how.description')
        }
      ],
      links: [
        { source: 'center', target: 'who' },
        { source: 'center', target: 'what' },
        { source: 'center', target: 'when' },
        { source: 'center', target: 'where' },
        { source: 'center', target: 'why' },
        { source: 'center', target: 'how' }
      ]
    };
  }

  getDefaultData() {
    // 預設資料結構，當Supabase查詢失敗時使用
    return {
      nodes: [
        { 
          id: 'center', 
          label: this.topicTitle, 
          type: 'center', 
          description: this.t('fiveW1H.centerDescription', { topicTitle: this.topicTitle }),
          x: 190, y: 140
        },
        { 
          id: 'who', 
          label: `WHO\n${this.t('fiveW1H.categories.who.name')}`, 
          type: '5w1h', 
          category: 'who',
          description: this.t('fiveW1H.categories.who.description')
        },
        { 
          id: 'what', 
          label: `WHAT\n${this.t('fiveW1H.categories.what.name')}`, 
          type: '5w1h', 
          category: 'what',
          description: this.t('fiveW1H.categories.what.description')
        },
        { 
          id: 'when', 
          label: `WHEN\n${this.t('fiveW1H.categories.when.name')}`, 
          type: '5w1h', 
          category: 'when',
          description: this.t('fiveW1H.categories.when.description')
        },
        { 
          id: 'where', 
          label: `WHERE\n${this.t('fiveW1H.categories.where.name')}`, 
          type: '5w1h', 
          category: 'where',
          description: this.t('fiveW1H.categories.where.description')
        },
        { 
          id: 'why', 
          label: `WHY\n${this.t('fiveW1H.categories.why.name')}`, 
          type: '5w1h', 
          category: 'why',
          description: this.t('fiveW1H.categories.why.description')
        },
        { 
          id: 'how', 
          label: `HOW\n${this.t('fiveW1H.categories.how.name')}`, 
          type: '5w1h', 
          category: 'how',
          description: this.t('fiveW1H.categories.how.description')
        }
      ],
      links: [
        { source: 'center', target: 'who' },
        { source: 'center', target: 'what' },
        { source: 'center', target: 'when' },
        { source: 'center', target: 'where' },
        { source: 'center', target: 'why' },
        { source: 'center', target: 'how' }
      ]
    };
  }

  /**
   * [新增] 輔助函式：根據節點類型獲取矩形大小
   */
  getNodeSize(d, isHeaderMode) {
    if (isHeaderMode) {
      if (d.type === 'center') return { width: 100, height: 50 }; // 中心節點
      if (d.type === '5w1h') return { width: 70, height: 40 };   // 5W1H 節點
      return { width: 60, height: 30 }; // 詳細節點
    } else {
      if (d.type === 'center') return { width: 120, height: 60 };
      if (d.type === '5w1h') return { width: 80, height: 45 };
      return { width: 70, height: 35 }; // 詳細節點
    }
  }

  setupD3() {
    const graphContainer = document.getElementById(`fivew1h-graph-${this.containerId}`);
    if (!graphContainer) return;

    const width = graphContainer.offsetWidth - 4;
    const height = this.options.height;
    const defaultScale = 1.2;

    // 清除舊的 SVG
    d3.select(`#fivew1h-graph-${this.containerId}`).selectAll("*").remove();

    this.svg = d3.select(`#fivew1h-graph-${this.containerId}`)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    this.g = this.svg.append('g');

         const zoom = d3.zoom()
       .scaleExtent([1.2, 1.5])
       .on('zoom', (event) => {
         this.transform = event.transform;
         this.g.attr('transform', event.transform);
       });

     this.svg.call(zoom);
     
     // 設置中心節點在原始坐標系統中的位置
     if (this.data && this.data.nodes) {
       const centerNode = this.data.nodes.find(node => node.type === 'center');
       if (centerNode) {
         centerNode.x = width / 2;
         centerNode.y = height / 2;
         centerNode.fx = width / 2;
         centerNode.fy = height / 2;
       }
     }

    // 計算需要的平移量以保持中心節點在視覺中心
    const translateX = (width / 2) * (1 - defaultScale);
    const translateY = (height / 2) * (1 - defaultScale);
     
     // 如果不是 header 模式，整體往上移動 50 像素
     const yOffset = this.options.isHeaderMode ? 0 : -90;
    
    // 應用縮放和平移變換
    const transform = d3.zoomIdentity
       .translate(translateX, translateY + yOffset)
      .scale(defaultScale);
    
    this.svg.call(zoom.transform, transform);
  }

  // 修改render方法中的節點大小
  render() {
    if (!this.data) return;
    
    // 確保有節點資料，如果沒有則使用預設資料
    if (!this.data.nodes || !this.data.nodes.length) {
      console.warn('⚠️ 沒有找到節點資料，使用預設資料');
      this.data = this.getDefaultData();
    }

    const graphContainer = document.getElementById(`fivew1h-graph-${this.containerId}`);
    if (!graphContainer) return;
    
    const width = graphContainer.offsetWidth - 4;
    const height = this.options.height;

    // 根據是否為header模式調整力導向參數
    const isHeaderMode = this.options.isHeaderMode;
    
    // --- [動畫修改 1] 調整力導向參數 ---
    this.simulation = d3.forceSimulation(this.data.nodes)
       .velocityDecay(0.6) // [新增] 增加阻尼 (0.4 -> 0.6)，減少彈跳
       .force('link', d3.forceLink(this.data.links).id(d => d.id).distance(d => {
         // 距離保持不變
         if (d.source.id === 'center' || (typeof d.source === 'object' && d.source.id === 'center')) {
           return isHeaderMode ? 80 : 100; 
         }
         if (d.source.type === '5w1h' || (typeof d.source === 'object' && d.source.type === '5w1h')) {
           return isHeaderMode ? 50 : 80;
         }
         return isHeaderMode ? 30 : 50;
       }))
       .force('charge', d3.forceManyBody().strength(d => {
         // [修改] 減弱排斥力，減少 "爆炸" 效果
         if (d.type === 'center') return isHeaderMode ? -250 : -500; // 原: -300 / -600
         if (d.type === '5w1h') return isHeaderMode ? -80 : -200; // 原: -100 / -250
         return isHeaderMode ? -40 : -80; // 原: -50 / -100
       }))
       .force('center', d3.forceCenter(width / 2, height / 2))
       .force('collision', d3.forceCollide().radius(d => {
         // 碰撞半徑保持不變
         if (isHeaderMode) {
           if (d.type === 'center') return 50; 
           if (d.type === '5w1h') return 35; 
           return 30;
         } else {
           if (d.type === 'center') return 60;
           if (d.type === '5w1h') return 40;
           return 35;
         }
       }))
       .force('x', d3.forceX(width / 2).strength(0.08)) // [修改] 稍微增強X軸拉力
       .force('y', d3.forceY(height / 2).strength(0.08)) // [修改] 稍微增強Y軸拉力
       .force('radial', d3.forceRadial(d => {
         if (d.type === 'center') return 0;
         if (d.type === '5w1h') return isHeaderMode ? 100 : 200;
         return isHeaderMode ? 60 : 120;
       }, width / 2, height / 2).strength(0.15)); // [修改] 減弱徑向力 (0.3 -> 0.15)
    // --- [動畫修改 1] 結束 ---


    // 繪製連結 (保持不變)
    const link = this.g.append('g')
      .selectAll('line')
      .data(this.data.links)
      .enter().append('line')
      .attr('class', d => {
        const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
        return sourceId === 'center' ? 'link link-center' : 'link';
      });

    // --- [結構修改 2] 創建節點群組 <g> ---
    // 我們不再直接創建 rect，而是創建 <g>
    const nodeGroup = this.g.append('g')
      .selectAll('g.node-group')
      .data(this.data.nodes)
      .enter().append('g')
      .attr('class', 'node-group') // 為群組添加一個class
       .on('click', (event, d) => { // 將點擊事件綁定到群組
         this.showNodeDetail(d, event);
       })
      .call(d3.drag() // 將拖動事件綁定到群組
        .on('start', this.dragstarted.bind(this))
        .on('drag', this.dragged.bind(this))
        .on('end', this.dragended.bind(this)));

    // [結構修改 3] 將 'rect' (方框) 附加到群組
    const node = nodeGroup.append('rect')
      .attr('class', d => `node node-${d.type} node-${d.category || 'center'}`)
      .attr('width', d => this.getNodeSize(d, isHeaderMode).width)
      .attr('height', d => this.getNodeSize(d, isHeaderMode).height)
      .attr('rx', 8) // 圓角
      .attr('ry', 8) // 圓角
      // [修改] 設置相對於群組中心的 x/y
      .attr('x', d => -this.getNodeSize(d, isHeaderMode).width / 2)
      .attr('y', d => -this.getNodeSize(d, isHeaderMode).height / 2);

    // [結構修改 4] 將 'text' (文字) 附加到群組
    const text = nodeGroup.append('text')
      .attr('class', d => `text text-${d.type}`)
      .text(d => d.label)
      .style('font-size', d => {
         if (isHeaderMode) {
           if (d.type === 'center') return '11px'; 
           if (d.type === '5w1h') return '9px';  
           return '8px';
         } else {
           if (d.type === 'center') return '14px';
           if (d.type === '5w1h') return '11px';
           return '9px';
         }
       })
      // [修改] 設置相對於群組中心的 y (x 由 text-anchor: middle 處理)
      // 保持原有的垂直偏移邏輯，以匹配CSS中沒有 dominant-baseline 的情況
       .attr('y', d => {
           // 如果有CSS的 'dominant-baseline: middle'，這裡可以設為 0
           // 如果沒有，我們保留原來的微調
           // 假設我們在 CSS 中添加了 dominant-baseline: middle
           if (d.label.includes('\n')) {
             // 對於多行文字，稍微向上移動 (因為 dominant-baseline 會以中心為準)
             const lines = d.label.split('\n').length;
             // 經驗值：-0.5em * (行數 - 1) / 2 左右，這裡簡化
             return lines > 1 ? '-0.2em' : '0.1em';
           }
           return '0.1em'; // 單行文字的微調 (配合 dominant-baseline: middle)
       });
       
    // [修改] 應對多行文字 (tspan)
    text.filter(d => d.label.includes('\n'))
        .text(null) // 清空原文字
        .each(function(d) {
            const lines = d.label.split('\n');
            const lineHeight = 1.1; // em
            // 計算起始Y偏移，使其垂直居中
            const startY = -(lines.length - 1) * lineHeight / 2;
            
            d3.select(this)
                .selectAll('tspan')
                .data(lines)
                .enter()
                .append('tspan')
                .attr('x', 0) // 水平居中 (依賴 text-anchor)
                .attr('dy', (line, i) => (i === 0) ? `${startY}em` : `${lineHeight}em`)
                .text(line => line);
        });
    // --- [結構修改] 結束 ---


    // 防止節點拖動時觸發背景拖動
    nodeGroup.on('mousedown', (event) => { // [修改] 綁定到 nodeGroup
      event.stopPropagation();
    });

    // 更新位置
    this.simulation.on('tick', () => {
      this.applyBoundaryConstraints(width, height);
      
      // 連結位置更新 (保持不變)
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      // --- [結構修改 5] ---
      // 刪除舊的 node 和 text 位置更新
      // node.attr('x', ...).attr('y', ...); // 刪除
      // text.attr('x', ...).attr('y', ...); // 刪除

      // [新增] 只需要更新群組的 transform
      nodeGroup
        .attr('transform', d => `translate(${d.x}, ${d.y})`);
      // --- [結構修改 5] 結束 ---
    });
  }

  // [修改] 邊界限制 - 使用矩形寬高 (保持不變)
  applyBoundaryConstraints(width, height) {
    const isHeaderMode = this.options.isHeaderMode;
    
    this.data.nodes.forEach(d => {
      const { width: nodeWidth, height: nodeHeight } = this.getNodeSize(d, isHeaderMode);
      const margin = isHeaderMode ? 5 : 10;
      
      d.x = Math.max(nodeWidth / 2 + margin, Math.min(width - nodeWidth / 2 - margin, d.x));
      d.y = Math.max(nodeHeight / 2 + margin, Math.min(height - nodeHeight / 2 - margin, d.y));
    });
  }

  // 拖動相關方法 (保持不變)
  dragstarted(event, d) {
    if (!event.active) this.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  dragged(event, d) {
    const dragLimit = this.options.dragLimit;
    d.fx = Math.max(-dragLimit, Math.min(this.options.width + dragLimit, event.x));
    d.fy = Math.max(-dragLimit, Math.min(this.options.height + dragLimit, event.y));
  }

  dragended(event, d) {
    if (!event.active) this.simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  // 控制方法 (保持不變)
  resetView() {
    if (!this.svg) return;
    this.svg.transition().duration(750).call(
      d3.zoom().transform,
      d3.zoomIdentity
    );
  }

  centerView() {
    if (!this.svg || !this.data) return;
    const width = this.options.width;
    const height = this.options.height;
    this.svg.transition().duration(750).call(
      d3.zoom().transform,
      d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
    );
  }

  async reloadData() {
    await this.loadData();
    if (this.svg) {
      this.svg.selectAll("*").remove();
    }
    this.setupD3();
    this.render();
  }

  // 重置 5W1H 節點到固定位置 (保持不變)
  resetFiveW1HPositions() {
    if (!this.data || !this.data.nodes) return;
    
    const centerNode = this.data.nodes.find(node => node.type === 'center');
    if (!centerNode) return;
    
    const fivew1hNodes = this.data.nodes.filter(node => node.type === '5w1h');
    const isHeaderMode = this.options.isHeaderMode;
    const radius = isHeaderMode ? 80 : 120;
    
    fivew1hNodes.forEach((node, index) => {
      const angle = (index * 2 * Math.PI) / fivew1hNodes.length;
      const targetX = centerNode.x + radius * Math.cos(angle);
      const targetY = centerNode.y + radius * Math.sin(angle);
      
      node.x = targetX;
      node.y = targetY;
      node.fx = targetX;
      node.fy = targetY;
    });
    
    // 重新啟動力導向模擬
    if (this.simulation) {
      this.simulation.alphaTarget(0.1).restart();
      setTimeout(() => {
        if (this.simulation) {
          this.simulation.alphaTarget(0);
        }
      }, 200);
    }
  }

  // 清理資源 (保持不變)
  destroy() {
    if (this.cleanupResize) {
      this.cleanupResize();
    }
    if (this.svg) {
      this.svg.selectAll("*").remove();
    }
    if (this.simulation) {
      this.simulation.stop();
    }
  }

  // --- [showNodeDetail 及其子函數保持不變] ---
  // ... (從 showNodeDetail 到 getNodeTypeColor 的所有
  //     程式碼都與原檔案相同，這裡省略以節省篇幅)
  // ...
  showNodeDetail(node, event) {
    try {
      console.log('🔍 開始顯示節點詳情:', node);
      
    // 防止事件冒泡
    event.stopPropagation();
    
    // 移除現有的詳情視窗
    const existingModal = document.getElementById('node-detail-modal');
    if (existingModal) {
      existingModal.remove();
    }
    
    // 創建詳情視窗
    const modal = document.createElement('div');
    modal.id = 'node-detail-modal';
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 10000;
      cursor: pointer;
    `;
    
    // 創建視窗內容
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
      background: white;
      border-radius: 15px;
      padding: 25px;
        max-width: 600px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
      box-shadow: 0 20px 40px rgba(0,0,0,0.3);
      cursor: default;
      position: relative;
    `;
    
    // 關閉按鈕
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = `
      position: absolute;
      top: 15px;
      right: 20px;
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: #666;
      width: 30px;
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      transition: background 0.3s ease;
    `;
    
    closeBtn.onmouseover = () => {
      closeBtn.style.background = '#f0f0f0';
    };
    
    closeBtn.onmouseout = () => {
      closeBtn.style.background = 'none';
    };
    
    closeBtn.onclick = () => {
      modal.remove();
    };
    
    // 節點標題
    const title = document.createElement('h2');
    title.textContent = node.label.replace(/\n/g, ' ');
    title.style.cssText = `
      margin: 0 0 15px 0;
      color: #2c3e50;
      font-size: 1.5em;
      font-weight: bold;
      text-align: center;
    `;
    
    // 節點類型標籤

    
    // 節點描述
    const description = document.createElement('p');
    description.textContent = node.description || '暫無詳細描述';
    description.style.cssText = `
      margin: 15px 0;
      color: #555;
      line-height: 1.6;
      font-size: 16px;
    `;
    
    // 根據節點類型顯示詳細資訊
    let detailedContent = '';
    
    if (node.type === 'center') {
      // 中心節點顯示概述
      detailedContent = this.createDetailedContent('center_node', node);
    } else if (node.type === '5w1h') {
      // 5W1H 節點顯示主要資訊和詳細節點
      detailedContent = this.createDetailedContent(node.category, node);
    } else if (node.type === 'detail') {
      // 詳細節點顯示具體資訊
      detailedContent = this.createDetailedContent('detail', node);
    }
    
    // 組裝視窗內容
    modalContent.appendChild(closeBtn);
    modalContent.appendChild(title);

    if(node.type === '5w1h' && node.category !== 'why') {
      modalContent.appendChild(description);
    }
    
    if (detailedContent) {
      modalContent.appendChild(detailedContent);
    }
    
    // 點擊背景關閉視窗
    modal.onclick = (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    };
    
    // 將內容添加到模態視窗
    modal.appendChild(modalContent);
    
    // 添加到頁面
    document.body.appendChild(modal);
    
    console.log('✅ 節點詳情視窗創建成功');
  } catch (error) {
    console.error('❌ 創建節點詳情視窗失敗:', error);
    // 如果創建失敗，至少顯示一個簡單的提示
    alert(`顯示節點詳情失敗: ${node.label || '未知節點'}`);
  }
}
  
createDetailedContent(category, node) {
  // 檢查是否有詳細資料
  if (!this.data.detailed_nodes) return null;
  
  let detailedNodes = [];
  
  // 根據類別獲取對應的詳細節點
  switch (category) {
    case 'who':
      detailedNodes = this.data.detailed_nodes.who_nodes || [];
      break;
    case 'what':
      detailedNodes = this.data.detailed_nodes.what_nodes || [];
      break;
    case 'when':
      detailedNodes = this.data.detailed_nodes.when_nodes || [];
      break;
    case 'where':
      detailedNodes = this.data.detailed_nodes.where_nodes || [];
      break;
    case 'why':
      detailedNodes = this.data.detailed_nodes.why_nodes || [];
      break;
    case 'how':
      detailedNodes = this.data.detailed_nodes.how_nodes || [];
      break;
    case 'center_node':
      // 中心節點顯示所有主要節點的概述
      return this.createMainNodesOverview();
    default:
      return null;
  }
  
  if (detailedNodes.length === 0) return null;
  
  // 如果是時間節點，使用時間軸佈局
  if (category === 'when') {
    return this.createTimelineLayout(detailedNodes);
  }
  
  // 如果是 why 類別，只顯示 main_node 的 description
  if (category === 'why') {
    const mainNode = this.data.main_nodes?.find(node => node.id === category);
    if (!mainNode || !mainNode.description) {
      return null; // 如果沒有 main_node 的 description，不顯示任何內容
    }
    
    const container = document.createElement('div');
    container.style.cssText = `
      margin-top: 20px;
      border-top: 1px solid #eee;
      padding-top: 20px;
    `;
    
    const description = document.createElement('p');
    description.textContent = mainNode.description;
    description.style.cssText = `
      margin: 0;
      color: #555;
      line-height: 1.6;
      font-size: 16px;
    `;
    
    container.appendChild(description);
    return container;
  }
  
  // 其他類別使用原本的佈局
  const container = document.createElement('div');
  container.style.cssText = `
    margin-top: 20px;
    border-top: 1px solid #eee;
    padding-top: 20px;
  `;
  
  // 創建詳細節點列表
  
  detailedNodes.forEach(detailNode => {
    const detailItem = document.createElement('div');
    detailItem.style.cssText = `
      margin-bottom: 15px;
      padding: 15px;
      background: #f8f9fa;
      border-radius: 8px;
      border-left: 4px solid ${this.getNodeTypeColor('detail')};
    `;
    
    const detailTitle = document.createElement('h4');
    detailTitle.textContent = detailNode.label;
    detailTitle.style.cssText = `
      margin: 0 0 8px 0;
      color: #2c3e50;
      font-size: 1em;
      font-weight: bold;
    `;
    
    const detailDesc = document.createElement('p');
    detailDesc.textContent = detailNode.description;
    detailDesc.style.cssText = `
      margin: 0;
      color: #555;
      line-height: 1.5;
      font-size: 16px;
    `;
    
    detailItem.appendChild(detailTitle);
    detailItem.appendChild(detailDesc);
    container.appendChild(detailItem);
  });
  
  return container;
}

createTimelineLayout(detailedNodes) {
  const container = document.createElement('div');
  container.style.cssText = `
    margin-top: 15px;
    border-top: 1px solid #eee;
    padding-top: 15px;
  `;
  
  // 創建時間軸容器
  const timelineContainer = document.createElement('div');
  timelineContainer.style.cssText = `
    position: relative;
    padding: 30px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-height: 80px;
  `;
  
  // 創建時間軸線
  const timelineLine = document.createElement('div');
  timelineLine.style.cssText = `
    position: absolute;
    top: 50%;
    left: 20px;
    right: 20px;
    height: 3px;
    background: #3498db;
    border-radius: 2px;
    transform: translateY(-50%);
    z-index: 1;
  `;
  
  timelineContainer.appendChild(timelineLine);
  
  // 創建時間點
  detailedNodes.forEach((detailNode, index) => {
    const timelineItem = document.createElement('div');
    timelineItem.style.cssText = `
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      z-index: 2;
      flex: 1;
    `;
    
    // 時間標籤（點上面）
    const timeLabel = document.createElement('div');
    timeLabel.textContent = detailNode.label;
    timeLabel.style.cssText = `
      font-weight: bold;
      color: #2c3e50;
      font-size: 12px;
      margin-bottom: 8px;
      background: white;
      padding: 4px 8px;
      border-radius: 4px;
      border: 1px solid #ddd;
    `;
    
    // 時間點圓圈
    const timePoint = document.createElement('div');
    timePoint.style.cssText = `
      width: 12px;
      height: 12px;
      background: #e74c3c;
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
      margin-bottom: 8px;
    `;
    
    // 標題（點下面）
    const title = document.createElement('div');
    title.textContent = detailNode.description;
    title.style.cssText = `
      color: #555;
      font-size: 14px;
      text-align: center;
      max-width: 120px;
      line-height: 1.3;
    `;
    
    timelineItem.appendChild(timeLabel);
    timelineItem.appendChild(timePoint);
    timelineItem.appendChild(title);
    timelineContainer.appendChild(timelineItem);
  });
  
  container.appendChild(timelineContainer);
  
  return container;
}

createMainNodesOverview() {
  if (!this.data.main_nodes) return null;
  
  const container = document.createElement('div');
  container.style.cssText = `
    margin-top: 20px;
    border-top: 1px solid #eee;
    padding-top: 20px;
  `;
  
  this.data.main_nodes.forEach(mainNode => {
    const mainItem = document.createElement('div');
    mainItem.style.cssText = `
      margin-bottom: 15px;
      padding: 15px;
      background: #f8f9fa;
      border-radius: 8px;
      border-left: 4px solid ${this.getNodeTypeColor('5w1h')};
    `;
    
    const mainTitle = document.createElement('h4');
    mainTitle.textContent = mainNode.label;
    mainTitle.style.cssText = `
      margin: 0 0 8px 0;
      color: #2c3e50;
      font-size: 1em;
      font-weight: bold;
    `;
    
    const mainDesc = document.createElement('p');
    mainDesc.textContent = mainNode.description;
    mainDesc.style.cssText = `
      margin: 0;
      color: #555;
      line-height: 1.5;
      font-size: 16px;
    `;
    
    mainItem.appendChild(mainTitle);
    mainItem.appendChild(mainDesc);
    container.appendChild(mainItem);
  });
  
  return container;
}

  
  getNodeTypeColor(type) {
    const colors = {
      'center': '#e74c3c',
      '5w1h': '#3498db',
      'detail': '#95a5a6'
    };
    return colors[type] || '#95a5a6';
  }

  // 創建HTML結構 (保持不變)
  createHTML() {
    const container = document.getElementById(this.containerId);
    
    // [修改] 根據 isHeaderMode 添加 'header-mode' 或 'default-mode' class
    const modeClass = this.options.isHeaderMode ? 'header-mode' : 'default-mode';

    // Header模式使用簡化版本
    if (this.options.isHeaderMode) {
      container.innerHTML = `
         <div class="fivew1h-container ${modeClass}">
           <div class="fivew1h-graph" id="fivew1h-graph-${this.containerId}"></div>
         </div>
      `;
    } else {
      // 非header模式使用原本的完整版本
      container.innerHTML = `
         <div class="fivew1h-container ${modeClass}">
           <div class="fivew1h-graph" id="fivew1h-graph-${this.containerId}"></div>
           <div class="fivew1h-bottom-row">
             <p class="fivew1h-instructions">${this.t('fiveW1H.instructions')}</p>
             <button class="fivew1h-btn" onclick="window.fivew1hVizInstance?.reloadData()">${this.t('fiveW1H.reloadButton')}</button>
           </div>
         </div>
      `;
    }

    // 設置全域變量以便按鈕訪問
    window.fivew1hVizInstance = this;
    
    // 添加響應式調整
    if (!this.options.isHeaderMode) {
      this.addResizeListener();
    }
  }

  // addResizeListener (保持不變)
  addResizeListener() {
    // 監聽視窗大小變化
    const resizeHandler = () => {
      if (this.svg && this.data) {
        this.setupD3();
        this.render();
      }
    };
    
    window.addEventListener('resize', resizeHandler);
    
    // 保存清理函數
    this.cleanupResize = () => {
      window.removeEventListener('resize', resizeHandler);
    };
  }

  // init (保持不變)
  async init() {
    console.log('🚀 開始初始化 5W1H 視覺化');
    await this.loadData();
    console.log('📊 資料載入完成，資料狀態:', {
      hasData: !!this.data,
      nodesCount: this.data?.nodes?.length || 0,
      linksCount: this.data?.links?.length || 0
    });
    this.createHTML();
    this.setupD3();
    this.render();
    console.log('✅ 5W1H 視覺化初始化完成');
  }
}

// 導出一個函數來創建和初始化 header 視覺化 (保持不變)
export const createHeaderVisualization = (containerRef, reportTitle, isModal = false, topicId = null, t = (key) => key, getFieldName = (fieldName) => fieldName) => {
  if (!containerRef.current) return null;

  // 清理舊的內容
  containerRef.current.innerHTML = '';
  
  // 創建容器,為模態框使用不同的ID
  const containerId = isModal ? 'expanded-mindmap' : 'header-mindmap';
  const mindmapContainer = document.createElement('div');
  mindmapContainer.id = containerId;
  mindmapContainer.style.cssText = 'width: 100%; height: 100%;';
  containerRef.current.appendChild(mindmapContainer);
  
  // 根據是否為模態框設置不同的尺寸
  const width = isModal ? 800 : 380;
  const height = isModal ? 600 : 280;
  
  // 初始化視覺化
  const vizInstance = new FiveW1HVisualization(containerId, {
    width: width,
    height: height,
    dragLimit: isModal ? 50 : 20,
    isHeaderMode: !isModal, // 模態框不使用header模式，顯示完整功能
    topicTitle: reportTitle || t('fiveW1H.defaultTitle'),
    topicId: topicId, // 新增：傳遞 topic_id
    t: t, // 傳遞翻譯函數
    getFieldName: getFieldName // 傳遞 getFieldName 函數
  });
  
  // 確保 D3.js 載入後再初始化
  if (typeof d3 !== 'undefined') {
    console.log('✅ D3.js 已載入，開始初始化視覺化');
    vizInstance.init();
  } else {
    console.log('⏳ D3.js 未載入，正在載入...');
    // 載入 D3.js
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js';
    script.onload = () => {
      console.log('✅ D3.js 載入完成，開始初始化視覺化');
      // 直接調用初始化，因為 D3.js 現在在 window 上可用
      vizInstance.init();
    };
    script.onerror = () => {
      console.error('❌ D3.js 載入失敗');
    };
    document.head.appendChild(script);
  }
  
  return vizInstance;
};