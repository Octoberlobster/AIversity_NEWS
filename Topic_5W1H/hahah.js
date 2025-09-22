// supabase.js
import { createClient } from '@supabase/supabase-js';

// Supabase 配置
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'YOUR_SUPABASE_URL';
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'YOUR_SUPABASE_ANON_KEY';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// 5W1H 視覺化類別
class FiveW1HVisualization {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            width: options.width || 1200,
            height: options.height || 600,
            dragLimit: options.dragLimit || 50,
            ...options
        };
        
        this.data = null;
        this.svg = null;
        this.g = null;
        this.simulation = null;
        this.transform = { x: 0, y: 0, k: 1 };
        
        this.init();
    }

    async init() {
        await this.loadData();
        this.createHTML();
        this.setupD3();
        this.render();
    }

    // 從 Supabase 載入資料
    async loadData() {
        try {
            const { data, error } = await supabase
                .from('topic')  // 假設資料表名稱為 five_w1h_data
                .select('mind_map_detail')
                .eq("topic_title", "俄烏戰爭").execute();

            if (error) throw error;

            this.data = this.transformSupabaseData(data);
        } catch (error) {
            console.error('載入資料失敗:', error);
            // 使用預設資料作為備案
            this.data = this.getDefaultData();
        }
    }

    // 轉換 Supabase 資料格式
    transformSupabaseData(rawData) {
        const nodes = [];
        const links = [];

        // 中心節點
        nodes.push({
            ...rawData.center_node,
            type: 'center'
        });

        // 5W1H 主節點
        rawData.main_nodes.forEach(node => {
            nodes.push({
                ...node,
                type: '5w1h',
                category: node.id
            });
            
            // 連結到中心節點
            links.push({
                source: 'center',
                target: node.id
            });
        });

        // 詳細節點
        Object.keys(rawData.detailed_nodes).forEach(category => {
            const categoryNodes = rawData.detailed_nodes[category];
            const mainNodeId = category.replace('_nodes', '');
            
            categoryNodes.forEach(node => {
                nodes.push({
                    ...node,
                    type: 'detail',
                    category: mainNodeId
                });
                
                // 連結到對應的主節點
                links.push({
                    source: mainNodeId,
                    target: node.id
                });
            });
        });

        return { nodes, links };
    }

    // 預設資料（備案）
    getDefaultData() {
        return {
            nodes: [
                { id: 'center', label: '資料載入中', type: 'center', description: '正在從資料庫載入資料...' }
            ],
            links: []
        };
    }

    // 創建 HTML 結構
    createHTML() {
        const container = document.getElementById(this.containerId);
        
        container.innerHTML = `
            <style>
                .fivew1h-container {
                    font-family: 'Arial', sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }

                .fivew1h-title {
                    text-align: center;
                    color: #2c3e50;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    font-weight: bold;
                }

                .fivew1h-subtitle {
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 1.2em;
                    margin-bottom: 30px;
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
                    margin-top: 20px;
                    gap: 15px;
                }

                .fivew1h-legend-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    background: rgba(255, 255, 255, 0.8);
                    padding: 8px 12px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 500;
                }

                .fivew1h-legend-color {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    border: 2px solid #34495e;
                }

                .fivew1h-controls {
                    text-align: center;
                    margin-top: 20px;
                }

                .fivew1h-btn {
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 14px;
                    margin: 0 10px;
                    transition: background 0.3s ease;
                }

                .fivew1h-btn:hover {
                    background: #2980b9;
                }

                .fivew1h-instructions {
                    text-align: center;
                    margin-top: 10px;
                    color: #7f8c8d;
                    font-size: 12px;
                }

                .loading {
                    text-align: center;
                    padding: 50px;
                    color: #7f8c8d;
                }
            </style>

            <div class="fivew1h-container">
                <h1 class="fivew1h-title">5W1H 事件分析</h1>
                <p class="fivew1h-subtitle">互動式視覺化分析圖</p>
                <p class="fivew1h-instructions">💡 可以拖動背景來移動整個圖形（限制${this.options.dragLimit}px範圍），縮放以中心節點為基準，或拖動個別節點來調整位置</p>
                
                <div class="fivew1h-graph" id="fivew1h-graph-${this.containerId}"></div>
                
                <div class="fivew1h-legend">
                    <div class="fivew1h-legend-item">
                        <div class="fivew1h-legend-color" style="background-color: #3498db;"></div>
                        <span>Who (誰)</span>
                    </div>
                    <div class="fivew1h-legend-item">
                        <div class="fivew1h-legend-color" style="background-color: #2ecc71;"></div>
                        <span>What (什麼)</span>
                    </div>
                    <div class="fivew1h-legend-item">
                        <div class="fivew1h-legend-color" style="background-color: #f39c12;"></div>
                        <span>When (何時)</span>
                    </div>
                    <div class="fivew1h-legend-item">
                        <div class="fivew1h-legend-color" style="background-color: #9b59b6;"></div>
                        <span>Where (哪裡)</span>
                    </div>
                    <div class="fivew1h-legend-item">
                        <div class="fivew1h-legend-color" style="background-color: #e67e22;"></div>
                        <span>Why (為什麼)</span>
                    </div>
                    <div class="fivew1h-legend-item">
                        <div class="fivew1h-legend-color" style="background-color: #1abc9c;"></div>
                        <span>How (如何)</span>
                    </div>
                </div>

                <div class="fivew1h-controls">
                    <button class="fivew1h-btn" onclick="window.fivew1hViz.resetView()">重置視圖</button>
                    <button class="fivew1h-btn" onclick="window.fivew1hViz.centerView()">回到中心</button>
                    <button class="fivew1h-btn" onclick="window.fivew1hViz.reloadData()">重新載入資料</button>
                </div>
            </div>

            <div class="fivew1h-tooltip" id="fivew1h-tooltip-${this.containerId}"></div>
        `;

        // 設置全域變量以便按鈕訪問
        window.fivew1hViz = this;
    }

    // 設置 D3.js
    setupD3() {
        const graphContainer = document.getElementById(`fivew1h-graph-${this.containerId}`);
        const width = graphContainer.offsetWidth - 4;
        const height = this.options.height;

        this.svg = d3.select(`#fivew1h-graph-${this.containerId}`)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        this.g = this.svg.append('g');
        this.tooltip = d3.select(`#fivew1h-tooltip-${this.containerId}`);

        // 設置縮放和拖動
        this.setupZoomAndDrag(width, height);
    }

    setupZoomAndDrag(width, height) {
        const zoom = d3.zoom()
            .scaleExtent([0.8, 2])
            .on('zoom', (event) => {
                const centerNode = this.data.nodes.find(d => d.id === 'center');
                const centerX = centerNode ? centerNode.x : width / 2;
                const centerY = centerNode ? centerNode.y : height / 2;
                
                const constrainedTransform = this.constrainTransform(event.transform);
                const scale = event.transform.k;
                const translateX = constrainedTransform.x + (centerX * (1 - scale));
                const translateY = constrainedTransform.y + (centerY * (1 - scale));
                
                this.transform = {
                    x: constrainedTransform.x,
                    y: constrainedTransform.y,
                    k: scale
                };
                
                if (event.transform.x !== constrainedTransform.x || event.transform.y !== constrainedTransform.y) {
                    setTimeout(() => {
                        this.svg.call(zoom.transform, d3.zoomIdentity
                            .translate(constrainedTransform.x, constrainedTransform.y)
                            .scale(constrainedTransform.k));
                    }, 0);
                }
                
                this.g.attr('transform', `translate(${translateX}, ${translateY}) scale(${scale})`);
            });

        this.svg.call(zoom);
        this.zoom = zoom;
    }

    constrainTransform(transform) {
        const constrainedX = Math.max(-this.options.dragLimit, Math.min(this.options.dragLimit, transform.x));
        const constrainedY = Math.max(-this.options.dragLimit, Math.min(this.options.dragLimit, transform.y));
        return {
            x: constrainedX,
            y: constrainedY,
            k: transform.k
        };
    }

    // 渲染圖形
    render() {
        if (!this.data || !this.data.nodes.length) return;

        const graphContainer = document.getElementById(`fivew1h-graph-${this.containerId}`);
        const width = graphContainer.offsetWidth - 4;
        const height = this.options.height;

        // 建立力導向模擬
        this.simulation = d3.forceSimulation(this.data.nodes)
            .force('link', d3.forceLink(this.data.links).id(d => d.id).distance(d => {
                if (d.source.id === 'center') return 150;
                if (d.source.type === '5w1h') return 80;
                return 60;
            }))
            .force('charge', d3.forceManyBody().strength(d => {
                if (d.type === 'center') return -800;
                if (d.type === '5w1h') return -300;
                return -150;
            }))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => {
                if (d.type === 'center') return 40;
                if (d.type === '5w1h') return 35;
                return 25;
            }))
            .force('x', d3.forceX(width / 2).strength(0.1))
            .force('y', d3.forceY(height / 2).strength(0.1));

        // 繪製連結
        const link = this.g.append('g')
            .selectAll('line')
            .data(this.data.links)
            .enter().append('line')
            .attr('class', d => d.source === 'center' ? 'link link-center' : 'link');

        // 繪製節點
        const node = this.g.append('g')
            .selectAll('circle')
            .data(this.data.nodes)
            .enter().append('circle')
            .attr('class', d => `node node-${d.type} node-${d.category || 'center'}`)
            .attr('r', d => {
                if (d.type === 'center') return 35;
                if (d.type === '5w1h') return 30;
                return 20;
            })
            .on('mouseover', (event, d) => {
                this.tooltip
                    .style('opacity', 1)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px')
                    .html(`<strong>${d.label.replace(/\n/g, ' ')}</strong><br/>${d.description}`);
            })
            .on('mouseout', () => {
                this.tooltip.style('opacity', 0);
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
                if (d.type === 'center') return '14px';
                if (d.type === '5w1h') return '12px';
                return '10px';
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
                        return d.y + 3;
                    }
                    return d.y + 4;
                });
        });
    }

    // 拖拽函數
    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    // 邊界限制
    applyBoundaryConstraints(width, height) {
        this.data.nodes.forEach(d => {
            const radius = d.type === 'center' ? 35 : d.type === '5w1h' ? 30 : 20;
            const margin = 10;
            
            d.x = Math.max(radius + margin, Math.min(width - radius - margin, d.x));
            d.y = Math.max(radius + margin, Math.min(height - radius - margin, d.y));
        });
    }

    // 控制函數
    resetView() {
        this.data.nodes.forEach(d => {
            d.fx = null;
            d.fy = null;
        });
        this.simulation.alpha(1).restart();
        
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity);
    }

    centerView() {
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity);
    }

    // 重新載入資料
    async reloadData() {
        const loadingDiv = document.querySelector(`#${this.containerId} .loading`);
        if (loadingDiv) loadingDiv.style.display = 'block';
        
        await this.loadData();
        
        // 清除舊的圖形
        this.g.selectAll('*').remove();
        
        // 重新渲染
        this.render();
        
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
}

// 導出類別和初始化函數
export { FiveW1HVisualization };

// 使用範例：
// const viz = new FiveW1HVisualization('my-container', {
//     width: 1200,
//     height: 600,
//     dragLimit: 50
// });