import * as d3 from 'd3';
import { supabase } from './supabase';

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
    // this.topicTitle = options.topicTitle || "俄烏戰爭";
    this.topicTitle = "大罷免";
  }

  async loadData() {
    try {
      // 優先從Supabase獲取資料
      console.log('正在從Supabase載入資料，主題:', this.topicTitle);
      
      // 檢查Supabase連接
      if (!supabase) {
        console.error('❌ Supabase客戶端未初始化');
        this.data = this.getDefaultData();
        return;
      }
      
      console.log('🔍 開始Supabase查詢...');
      const { data, error } = await supabase
        .from("topic")
        .select("mind_map_detail")
        .eq("topic_title", this.topicTitle);

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
      
      if (data[0] && data[0].mind_map_detail) {
        try {
          console.log("🔄 開始轉換資料...");
          this.data = this.transformSupabaseData(data[0].mind_map_detail);
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
        description: mindMapData.center_node.description || `${this.topicTitle}的核心議題分析`,
        x: 190, 
        y: 140
      });
    } else {
      console.warn('⚠️ 沒有找到中心節點資料');
    }

    // 添加主要節點 (5W1H)
    if (mindMapData.main_nodes && Array.isArray(mindMapData.main_nodes)) {
      console.log('🔗 處理主要節點，數量:', mindMapData.main_nodes.length);
      mindMapData.main_nodes.forEach((node, index) => {
        console.log(`  📌 節點 ${index}:`, node);
        const category = node.id || node.category; // who, what, when, where, why, how
        nodes.push({
          id: node.id || category,
          label: node.label || node.name || category.toUpperCase(),
          type: '5w1h',
          category: category,
          description: node.description || `涉及${category}相關的內容`
        });
        
        // 連接到中心節點
        links.push({
          source: 'center',
          target: node.id || category
        });
      });
    } else {
      console.warn('⚠️ 沒有找到主要節點資料或格式不正確:', mindMapData.main_nodes);
    }

    // 添加詳細節點
    // if (mindMapData.detailed_nodes && typeof mindMapData.detailed_nodes === 'object') {
    //   Object.keys(mindMapData.detailed_nodes).forEach(categoryKey => {
    //     const categoryNodes = mindMapData.detailed_nodes[categoryKey];
    //     const mainNodeId = categoryKey.replace('_nodes', ''); // who_nodes -> who
        
    //     categoryNodes.forEach(detailNode => {
    //       nodes.push({
    //         ...detailNode,
    //         type: 'detail',
    //         category: mainNodeId
    //       });
          
    //       // 連接到對應的主節點
    //       links.push({
    //         source: mainNodeId,
    //         target: detailNode.id
    //       });
    //     });
    //   });
    // }

    console.log('✅ 轉換完成:');
    console.log('  📊 節點數量:', nodes.length);
    console.log('  🔗 連接數量:', links.length);
    console.log('  📋 節點資料:', nodes);
    console.log('  🔗 連接資料:', links);
    
    return { nodes, links };
  }

  getHeaderModeData() {
    const topicTitle = this.topicTitle || "專題分析";
    
    return {
      nodes: [
        { 
          id: 'center', 
          label: topicTitle, 
          type: 'center', 
          description: `${topicTitle}的核心議題分析`,
          x: 190, y: 140
        },
        { 
          id: 'who', 
          label: 'Who\n誰', 
          type: '5w1h', 
          category: 'who',
          description: '涉及的人物、組織和利益相關者'
        },
        { 
          id: 'what', 
          label: 'What\n什麼', 
          type: '5w1h', 
          category: 'what',
          description: '發生的事件內容和具體行為'
        },
        { 
          id: 'when', 
          label: 'When\n何時', 
          type: '5w1h', 
          category: 'when',
          description: '事件發生的時間軸和重要節點'
        },
        { 
          id: 'where', 
          label: 'Where\n哪裡', 
          type: '5w1h', 
          category: 'where',
          description: '事件發生的地點和範圍'
        },
        { 
          id: 'why', 
          label: 'Why\n為什麼', 
          type: '5w1h', 
          category: 'why',
          description: '事件發生的原因和背景'
        },
        { 
          id: 'how', 
          label: 'How\n如何', 
          type: '5w1h', 
          category: 'how',
          description: '事件的過程和方式'
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
          description: `${this.topicTitle}的核心議題分析`,
          x: 190, y: 140
        },
        { 
          id: 'who', 
          label: 'WHO\n誰', 
          type: '5w1h', 
          category: 'who',
          description: '涉及的人物、組織和利益相關者'
        },
        { 
          id: 'what', 
          label: 'WHAT\n什麼', 
          type: '5w1h', 
          category: 'what',
          description: '發生的事件內容和具體行為'
        },
        { 
          id: 'when', 
          label: 'WHEN\n何時', 
          type: '5w1h', 
          category: 'when',
          description: '事件發生的時間軸和重要節點'
        },
        { 
          id: 'where', 
          label: 'WHERE\n哪裡', 
          type: '5w1h', 
          category: 'where',
          description: '事件發生的地點和範圍'
        },
        { 
          id: 'why', 
          label: 'WHY\n為什麼', 
          type: '5w1h', 
          category: 'why',
          description: '事件發生的原因和背景'
        },
        { 
          id: 'how', 
          label: 'HOW\n如何', 
          type: '5w1h', 
          category: 'how',
          description: '事件的過程和方式'
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
    
    // 應用縮放和平移變換
    const transform = d3.zoomIdentity
      .translate(translateX, translateY)
      .scale(defaultScale);
    
    this.svg.call(zoom.transform, transform);
  }

  // 修改render方法中的節點大小
  render() {
    if (!this.data || !this.data.nodes.length) return;

    const graphContainer = document.getElementById(`fivew1h-graph-${this.containerId}`);
    if (!graphContainer) return;
    
    const width = graphContainer.offsetWidth - 4;
    const height = this.options.height;

    // 根據是否為header模式調整力導向參數
    const isHeaderMode = this.options.isHeaderMode;
    
              this.simulation = d3.forceSimulation(this.data.nodes)
       .force('link', d3.forceLink(this.data.links).id(d => d.id).distance(d => {
         if (d.source.id === 'center' || (typeof d.source === 'object' && d.source.id === 'center')) {
           return isHeaderMode ? 80 : 180; // 增加距離
         }
         if (d.source.type === '5w1h' || (typeof d.source === 'object' && d.source.type === '5w1h')) {
           return isHeaderMode ? 50 : 80; // 增加距離
         }
         return isHeaderMode ? 30 : 50; // 增加距離
       }))
       .force('charge', d3.forceManyBody().strength(d => {
         if (d.type === 'center') return isHeaderMode ? -300 : -600;
         if (d.type === '5w1h') return isHeaderMode ? -100 : -250;
         return isHeaderMode ? -50 : -100;
       }))
       .force('center', d3.forceCenter(width / 2, height / 2))
       .force('collision', d3.forceCollide().radius(d => {
         if (d.type === 'center') return isHeaderMode ? 20 : 40;
         if (d.type === '5w1h') return isHeaderMode ? 18 : 35;
         return isHeaderMode ? 12 : 25;
       }))
       .force('x', d3.forceX(width / 2).strength(0.05)) // 減少X軸拉力
       .force('y', d3.forceY(height / 2).strength(0.05)) // 減少Y軸拉力
       .force('radial', d3.forceRadial(d => {
         // 根據節點類型設置不同的徑向力，讓節點往外擴張
         if (d.type === 'center') return 0; // 中心節點不受徑向力影響
         if (d.type === '5w1h') return isHeaderMode ? 100 : 200; // 5W1H節點往外擴張
         return isHeaderMode ? 60 : 120; // 詳細節點往外擴張
       }, width / 2, height / 2).strength(0.3)); // 徑向力強度

    // 繪製連結
    const link = this.g.append('g')
      .selectAll('line')
      .data(this.data.links)
      .enter().append('line')
      .attr('class', d => {
        const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
        return sourceId === 'center' ? 'link link-center' : 'link';
      });

    // 繪製節點 - 根據模式調整大小
    const node = this.g.append('g')
      .selectAll('circle')
      .data(this.data.nodes)
      .enter().append('circle')
      .attr('class', d => `node node-${d.type} node-${d.category || 'center'}`)
      .attr('r', d => {
        if (isHeaderMode) {
          if (d.type === 'center') return 30; // 從16增加到25
          if (d.type === '5w1h') return 22;  // 從14增加到22
          return 18; // 從10增加到18
        } else {
          if (d.type === 'center') return 40; // 從30增加到40
          if (d.type === '5w1h') return 35;  // 從25增加到35
          return 28; // 從18增加到28
        }
      })
             .on('click', (event, d) => {
         this.showNodeDetail(d, event);
       })
      .call(d3.drag()
        .on('start', this.dragstarted.bind(this))
        .on('drag', this.dragged.bind(this))
        .on('end', this.dragended.bind(this)));

    // 添加文字標籤
    const text = this.g.append('g')
      .selectAll('text')
      .data(this.data.nodes)
      .enter().append('text')
      .attr('class', d => `text text-${d.type}`)
      .text(d => d.label)
             .style('font-size', d => {
         if (isHeaderMode) {
           if (d.type === 'center') return '11px'; // 調整為適合25px半徑
           if (d.type === '5w1h') return '9px';  // 調整為適合20px半徑
           return '8px'; // 調整為適合15px半徑
         } else {
           if (d.type === 'center') return '14px'; // 調整為適合35px半徑
           if (d.type === '5w1h') return '11px';  // 調整為適合30px半徑
           return '9px'; // 調整為適合22px半徑
         }
       });

    // 防止節點拖動時觸發背景拖動
    node.on('mousedown', (event) => {
      event.stopPropagation();
    });

    // 更新位置
    this.simulation.on('tick', () => {
      this.applyBoundaryConstraints(width, height);
      
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

             text
         .attr('x', d => d.x)
         .attr('y', d => {
           if (d.label.includes('\n')) {
             return d.y + 1; // 減少多行文字的垂直偏移
           }
           return d.y + 2; // 減少單行文字的垂直偏移
         })
         .style('opacity', 1); // 確保文字可見
    });
  }

  // 邊界限制
  applyBoundaryConstraints(width, height) {
    const isHeaderMode = this.options.isHeaderMode;
    
    this.data.nodes.forEach(d => {
      let radius;
      if (isHeaderMode) {
        radius = d.type === 'center' ? 25 : d.type === '5w1h' ? 22 : 18;
      } else {
        radius = d.type === 'center' ? 40 : d.type === '5w1h' ? 35 : 28;
      }
      
      const margin = isHeaderMode ? 5 : 10;
      
      d.x = Math.max(radius + margin, Math.min(width - radius - margin, d.x));
      d.y = Math.max(radius + margin, Math.min(height - radius - margin, d.y));
    });
  }

  // 拖動相關方法
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

  // 控制方法
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

  showNodeDetail(node, event) {
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
      max-width: 500px;
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
    const typeLabel = document.createElement('div');
    typeLabel.textContent = this.getNodeTypeLabel(node.type);
    typeLabel.style.cssText = `
      display: inline-block;
      background: ${this.getNodeTypeColor(node.type)};
      color: white;
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      margin-bottom: 20px;
      text-align: center;
    `;
    
    // 節點描述
    const description = document.createElement('p');
    description.textContent = node.description || '暫無詳細描述';
    description.style.cssText = `
      margin: 15px 0;
      color: #555;
      line-height: 1.6;
      font-size: 14px;
    `;
    
    // 組裝視窗內容
    modalContent.appendChild(closeBtn);
    modalContent.appendChild(title);
    modalContent.appendChild(typeLabel);
    modalContent.appendChild(description);
    
    // 點擊背景關閉視窗
    modal.onclick = (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    };
    
    // 添加到頁面
    document.body.appendChild(modal);
  }
  
  getNodeTypeLabel(type) {
    const labels = {
      'center': '核心議題',
      '5w1h': '5W1H要素',
      'detail': '詳細資訊'
    };
    return labels[type] || '未知類型';
  }
  
  getNodeTypeColor(type) {
    const colors = {
      'center': '#e74c3c',
      '5w1h': '#3498db',
      'detail': '#95a5a6'
    };
    return colors[type] || '#95a5a6';
  }

  // 創建HTML結構
  createHTML() {
    const container = document.getElementById(this.containerId);
    
    // Header模式使用簡化版本
    if (this.options.isHeaderMode) {
      container.innerHTML = `
        <style>
          .fivew1h-container {
            font-family: 'Arial', sans-serif;
            width: 100%;
            height: 100%;
            background: transparent;
            border-radius: 0;
            padding: 5px;
            box-shadow: none;
            display: flex;
            flex-direction: column;
          }

          .fivew1h-graph {
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 8px;
            background: radial-gradient(circle at center, #f8f9fa 0%, #e9ecef 100%);
            overflow: hidden;
            cursor: grab;
            flex: 1;
          }

          .fivew1h-graph:active {
            cursor: grabbing;
          }

          .node {
            cursor: pointer;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));
            transition: all 0.3s ease;
          }

          .node:hover {
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.25));
            transform: scale(1.05);
          }

          .node-center { fill: #e74c3c; stroke: #c0392b; stroke-width: 2px; }
          .node-5w1h { stroke: #34495e; stroke-width: 1.5px; }
          .node-who { fill: #3498db; }
          .node-what { fill: #2ecc71; }
          .node-when { fill: #f39c12; }
          .node-where { fill: #9b59b6; }
          .node-why { fill: #e67e22; }
          .node-how { fill: #1abc9c; }
          .node-detail { fill: #ecf0f1; stroke: #bdc3c7; stroke-width: 1px; }

          .link {
            stroke: #7f8c8d;
            stroke-width: 1.5px;
            fill: none;
            opacity: 0.6;
          }

          .link-center { stroke: #e74c3c; stroke-width: 2px; }

          .text {
            font-family: 'Arial', sans-serif;
            font-size: 10px;
            fill: #2c3e50;
            text-anchor: middle;
            pointer-events: none;
            font-weight: 500;
          }

          .text-center { font-size: 12px; font-weight: bold; fill: white; }
          .text-5w1h { font-size: 10px; font-weight: bold; fill: white; }

          .fivew1h-tooltip {
            position: absolute;
            background: rgba(44, 62, 80, 0.95);
            color: white;
            padding: 8px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            max-width: 200px;
            line-height: 1.3;
            z-index: 1000;
          }
        </style>

                 <div class="fivew1h-container">
           <div class="fivew1h-graph" id="fivew1h-graph-${this.containerId}"></div>
         </div>
      `;
    } else {
      // 非header模式使用原本的完整版本
      container.innerHTML = `
        <style>
          .fivew1h-container {
            font-family: 'Arial', sans-serif;
            max-width: 100%;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
          }

          .fivew1h-title {
            text-align: center;
            color: #2c3e50;
            font-size: 2em;
            margin-bottom: 10px;
            font-weight: bold;
          }

          .fivew1h-subtitle {
            text-align: center;
            color: #7f8c8d;
            font-size: 1.1em;
            margin-bottom: 20px;
          }

          .fivew1h-graph {
            width: 100%;
            height: ${this.options.height}px;
            border: 2px solid #e0e6ed;
            border-radius: 15px;
            background: radial-gradient(circle at center, #f8f9fa 0%, #e9ecef 100%);
            overflow: hidden;
            cursor: grab;
          }

          .fivew1h-graph:active {
            cursor: grabbing;
          }

          .node {
            cursor: pointer;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
            transition: all 0.3s ease;
          }

          .node:hover {
            filter: drop-shadow(0 6px 12px rgba(0,0,0,0.3));
            transform: scale(1.05);
          }

          .node-center { fill: #e74c3c; stroke: #c0392b; stroke-width: 3px; }
          .node-5w1h { stroke: #34495e; stroke-width: 2px; }
          .node-who { fill: #3498db; }
          .node-what { fill: #2ecc71; }
          .node-when { fill: #f39c12; }
          .node-where { fill: #9b59b6; }
          .node-why { fill: #e67e22; }
          .node-how { fill: #1abc9c; }
          .node-detail { fill: #ecf0f1; stroke: #bdc3c7; stroke-width: 1px; }

          .link {
            stroke: #7f8c8d;
            stroke-width: 2px;
            fill: none;
            opacity: 0.6;
            transition: all 0.3s ease;
          }

          .link:hover { stroke-width: 3px; opacity: 1; }
          .link-center { stroke: #e74c3c; stroke-width: 3px; }

                     .text {
             font-family: 'Arial', sans-serif;
             font-size: 12px;
             fill: #2c3e50;
             text-anchor: middle;
             pointer-events: none;
             font-weight: 500;
             opacity: 1 !important;
           }

           .text-center { font-size: 16px; font-weight: bold; fill: white; }
           .text-5w1h { font-size: 14px; font-weight: bold; fill: white; }

          .fivew1h-tooltip {
            position: absolute;
            background: rgba(44, 62, 80, 0.95);
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            max-width: 250px;
            line-height: 1.4;
            z-index: 1000;
          }

          .fivew1h-legend {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 15px;
            gap: 10px;
          }

          .fivew1h-legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.8);
            padding: 6px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 500;
          }

          .fivew1h-legend-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 1px solid #34495e;
          }

          .fivew1h-controls {
            text-align: center;
            margin-top: 15px;
          }

          .fivew1h-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            margin: 0 5px;
            transition: background 0.3s ease;
          }

          .fivew1h-btn:hover {
            background: #2980b9;
          }

          .fivew1h-instructions {
            text-align: center;
            margin-top: 10px;
            color: #7f8c8d;
            font-size: 11px;
          }

          .loading {
            text-align: center;
            padding: 30px;
            color: #7f8c8d;
          }
        </style>

                 <div class="fivew1h-container">
           <p class="fivew1h-instructions">💡 可以拖動背景移動圖形、縮放以中心為基準，或拖動個別節點調整位置</p>
           
           <div class="fivew1h-graph" id="fivew1h-graph-${this.containerId}"></div>

           <div class="fivew1h-controls">
             <button class="fivew1h-btn" onclick="window.fivew1hVizInstance?.resetView()">重置</button>
             <button class="fivew1h-btn" onclick="window.fivew1hVizInstance?.centerView()">回中心</button>
             <button class="fivew1h-btn" onclick="window.fivew1hVizInstance?.reloadData()">重新載入</button>
           </div>
         </div>
      `;
    }

    // 設置全域變量以便按鈕訪問
    window.fivew1hVizInstance = this;
  }

  async init() {
    await this.loadData();
    this.createHTML();
    this.setupD3();
    this.render();
  }
}

// 導出一個函數來創建和初始化 header 視覺化
export const createHeaderVisualization = (containerRef, reportTitle, isModal = false) => {
  if (!containerRef.current) return null;

  // 清理舊的內容
  containerRef.current.innerHTML = '';
  
  // 創建容器，為模態框使用不同的ID
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
    topicTitle: reportTitle || "專題分析"
  });
  
  // 確保 D3.js 載入後再初始化
  if (window.d3) {
    vizInstance.init();
  } else {
    // 載入 D3.js
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js';
    script.onload = () => vizInstance.init();
    document.head.appendChild(script);
  }
  
  return vizInstance;
}; 