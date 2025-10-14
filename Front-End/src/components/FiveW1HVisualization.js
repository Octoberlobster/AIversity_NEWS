import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';

// 自定義節點組件 - 長方形
const CustomNode = ({ data }) => {
  const getNodeSize = () => {
    if (data.isHeaderMode) {
      if (data.type === 'center') return { width: '120px', height: '50px', fontSize: '12px' };
      if (data.type === '5w1h') return { width: '100px', height: '45px', fontSize: '10px' };
      return { width: '80px', height: '35px', fontSize: '9px' };
    } else {
      if (data.type === 'center') return { width: '160px', height: '65px', fontSize: '15px' };
      if (data.type === '5w1h') return { width: '130px', height: '55px', fontSize: '12px' };
      return { width: '110px', height: '45px', fontSize: '10px' };
    }
  };

  const size = getNodeSize();
  
  const nodeStyle = {
    width: size.width,
    height: size.height,
    borderRadius: '10px',  // 改為圓角長方形
    border: `${data.type === 'center' ? '3px' : '2px'} solid ${data.borderColor || '#34495e'}`,
    backgroundColor: data.color || 'white',
    color: data.textColor || 'white',
    fontSize: size.fontSize,
    fontWeight: data.type === 'center' || data.type === '5w1h' ? 'bold' : 'normal',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    boxShadow: data.type === 'center' ? '0 6px 12px rgba(0, 0, 0, 0.25)' : '0 4px 8px rgba(0, 0, 0, 0.2)',
    fontFamily: 'Arial, sans-serif',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    padding: '8px 12px',
    whiteSpace: 'pre-line',
    lineHeight: '1.3'
  };

  return (
    <div 
      style={nodeStyle}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.05)';
        e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.3)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.boxShadow = data.type === 'center' ? '0 6px 12px rgba(0, 0, 0, 0.25)' : '0 4px 8px rgba(0, 0, 0, 0.2)';
      }}
    >
      {data.label}
    </div>
  );
};

// 節點詳情模態框組件
const NodeDetailModal = ({ node, onClose, data }) => {
  if (!node) return null;

  const getCategoryColor = (category) => {
    const colors = {
      who: '#3498db',
      what: '#2ecc71',
      when: '#f39c12',
      where: '#9b59b6',
      why: '#e67e22',
      how: '#1abc9c'
    };
    return colors[category] || '#95a5a6';
  };

  const createDetailedContent = () => {
    if (!data.detailed_nodes) return null;

    let detailedNodes = [];
    const category = node.data.category;

    if (category === 'why') {
      const mainNode = data.main_nodes?.find(n => n.id === category);
      if (!mainNode || !mainNode.description) return null;

      return (
        <div style={{ marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
          <p style={{ margin: 0, color: '#555', lineHeight: 1.6, fontSize: '16px' }}>
            {mainNode.description}
          </p>
        </div>
      );
    }

    switch (category) {
      case 'who': detailedNodes = data.detailed_nodes.who_nodes || []; break;
      case 'what': detailedNodes = data.detailed_nodes.what_nodes || []; break;
      case 'when': detailedNodes = data.detailed_nodes.when_nodes || []; break;
      case 'where': detailedNodes = data.detailed_nodes.where_nodes || []; break;
      case 'how': detailedNodes = data.detailed_nodes.how_nodes || []; break;
      default: return null;
    }

    if (detailedNodes.length === 0) return null;

    // 時間軸佈局
    if (category === 'when') {
      return (
        <div style={{ marginTop: '15px', borderTop: '1px solid #eee', paddingTop: '15px' }}>
          <div style={{ position: 'relative', padding: '30px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', minHeight: '80px' }}>
            <div style={{ position: 'absolute', top: '50%', left: '20px', right: '20px', height: '3px', background: '#3498db', borderRadius: '2px', transform: 'translateY(-50%)', zIndex: 1 }} />
            {detailedNodes.map((detailNode, index) => (
              <div key={index} style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2, flex: 1 }}>
                <div style={{ fontWeight: 'bold', color: '#2c3e50', fontSize: '12px', marginBottom: '8px', background: 'white', padding: '4px 8px', borderRadius: '4px', border: '1px solid #ddd' }}>
                  {detailNode.label}
                </div>
                <div style={{ width: '12px', height: '12px', background: '#e74c3c', border: '2px solid white', borderRadius: '50%', boxShadow: '0 2px 4px rgba(0,0,0,0.2)', marginBottom: '8px' }} />
                <div style={{ color: '#555', fontSize: '14px', textAlign: 'center', maxWidth: '120px', lineHeight: 1.3 }}>
                  {detailNode.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // 一般佈局
    return (
      <div style={{ marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
        {detailedNodes.map((detailNode, index) => (
          <div key={index} style={{ marginBottom: '15px', padding: '15px', background: '#f8f9fa', borderRadius: '8px', borderLeft: `4px solid ${getCategoryColor(category)}` }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#2c3e50', fontSize: '1em', fontWeight: 'bold' }}>
              {detailNode.label}
            </h4>
            <p style={{ margin: 0, color: '#555', lineHeight: 1.5, fontSize: '16px' }}>
              {detailNode.description}
            </p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        background: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 10000,
        cursor: 'pointer'
      }}
      onClick={onClose}
    >
      <div 
        style={{
          background: 'white',
          borderRadius: '15px',
          padding: '25px',
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          overflowY: 'auto',
          boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
          cursor: 'default',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '15px',
            right: '20px',
            background: 'none',
            border: 'none',
            fontSize: '24px',
            cursor: 'pointer',
            color: '#666',
            width: '30px',
            height: '30px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
            transition: 'background 0.3s ease'
          }}
          onMouseOver={(e) => e.currentTarget.style.background = '#f0f0f0'}
          onMouseOut={(e) => e.currentTarget.style.background = 'none'}
        >
          ×
        </button>

        <h2 style={{ margin: '0 0 15px 0', color: '#2c3e50', fontSize: '1.5em', fontWeight: 'bold', textAlign: 'center' }}>
          {node.data.label.replace(/\n/g, ' ')}
        </h2>

        {node.data.type === '5w1h' && node.data.category !== 'why' && (
          <p style={{ margin: '15px 0', color: '#555', lineHeight: 1.6, fontSize: '16px' }}>
            {node.data.description || '暫無詳細描述'}
          </p>
        )}

        {createDetailedContent()}
      </div>
    </div>
  );
};

// 顏色輔助函數
const darkenColor = (color, amount) => {
  const hex = color.replace('#', '');
  const r = Math.max(0, parseInt(hex.substr(0, 2), 16) - amount * 255);
  const g = Math.max(0, parseInt(hex.substr(2, 2), 16) - amount * 255);
  const b = Math.max(0, parseInt(hex.substr(4, 2), 16) - amount * 255);
  return `#${Math.round(r).toString(16).padStart(2, '0')}${Math.round(g).toString(16).padStart(2, '0')}${Math.round(b).toString(16).padStart(2, '0')}`;
};

const lightenColor = (color, amount) => {
  const hex = color.replace('#', '');
  const r = Math.min(255, parseInt(hex.substr(0, 2), 16) + amount * 255);
  const g = Math.min(255, parseInt(hex.substr(2, 2), 16) + amount * 255);
  const b = Math.min(255, parseInt(hex.substr(4, 2), 16) + amount * 255);
  return `#${Math.round(r).toString(16).padStart(2, '0')}${Math.round(g).toString(16).padStart(2, '0')}${Math.round(b).toString(16).padStart(2, '0')}`;
};

const getCategoryColor = (category) => {
  const colors = {
    who: '#3498db',
    what: '#2ecc71',
    when: '#f39c12',
    where: '#9b59b6',
    why: '#e67e22',
    how: '#1abc9c'
  };
  return colors[category] || '#95a5a6';
};

// 主組件
const FiveW1HVisualization = ({ 
  topicTitle = "專題分析", 
  topicId = null,
  isHeaderMode = false,
  height = 600,
  supabase = null
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [fullData, setFullData] = useState(null);

  const nodeTypes = useMemo(() => ({
    custom: CustomNode
  }), []);

  useEffect(() => {
    loadData();
  }, [topicTitle, topicId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      console.log('正在載入資料，主題:', topicTitle, '，ID:', topicId);
      
      let mindMapData = null;

      // 從 Supabase 載入資料
      if (supabase) {
        try {
          let data, error;
          
          if (topicId) {
            console.log('🎯 使用 topic_id 查詢:', topicId);
            ({ data, error } = await supabase
              .from("topic")
              .select("mind_map_detail")
              .eq("topic_id", topicId));
          } else {
            console.log('📝 使用 topic_title 查詢:', topicTitle);
            ({ data, error } = await supabase
              .from("topic")
              .select("mind_map_detail")
              .eq("topic_title", topicTitle));
          }

          if (!error && data && data.length > 0 && data[0].mind_map_detail) {
            let dbData = data[0].mind_map_detail;
            if (typeof dbData === 'string') {
              dbData = JSON.parse(dbData);
            }
            mindMapData = dbData;
            console.log('✅ 成功從Supabase載入資料');
          }
        } catch (error) {
          console.error('❌ Supabase 載入失敗:', error);
        }
      }

      // 使用預設資料
      if (!mindMapData) {
        console.log('使用預設資料');
        mindMapData = getDefaultMindMapData();
      }

      setFullData(mindMapData);
      const { nodes: newNodes, edges: newEdges } = transformToReactFlowData(mindMapData, isHeaderMode);
      
      setNodes(newNodes);
      setEdges(newEdges);
      
      console.log('✅ 資料載入完成');
    } catch (error) {
      console.error('❌ 載入資料失敗:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getDefaultMindMapData = () => {
    const defaultCategories = [
      { id: 'who', label: 'WHO\n誰', description: '涉及的人物、組織和利益相關者' },
      { id: 'what', label: 'WHAT\n什麼', description: '發生的事件內容和具體行為' },
      { id: 'when', label: 'WHEN\n何時', description: '事件發生的時間軸和重要節點' },
      { id: 'where', label: 'WHERE\n哪裡', description: '事件發生的地點和範圍' },
      { id: 'why', label: 'WHY\n為什麼', description: '事件發生的原因和背景' },
      { id: 'how', label: 'HOW\n如何', description: '事件的過程和方式' }
    ];

    return {
      center_node: {
        id: 'center',
        label: topicTitle,
        description: `${topicTitle}的核心議題分析`
      },
      main_nodes: defaultCategories,
      detailed_nodes: {}
    };
  };

  const transformToReactFlowData = (supabaseData, isHeaderMode) => {
    const nodes = [];
    const edges = [];
    
    const centerX = 0;
    const centerY = 0;
    
    // 添加中心節點
    const centerNode = supabaseData.center_node || { id: 'center', label: topicTitle };
    nodes.push({
      id: 'center',
      type: 'custom',
      position: { x: centerX, y: centerY },
      data: {
        label: centerNode.label || topicTitle,
        type: 'center',
        description: centerNode.description || `${topicTitle}的核心議題分析`,
        color: '#e74c3c',
        borderColor: '#c0392b',
        textColor: 'white',
        isHeaderMode
      },
      draggable: !isHeaderMode,
      sourcePosition: Position.Right,  // 添加這行
      targetPosition: Position.Left    // 添加這行
    });

    // 添加主要節點 (5W1H)
    const categories = supabaseData.main_nodes || [];
    const radius = isHeaderMode ? 200 : 280;
    const angleStep = (2 * Math.PI) / categories.length;
    
    categories.forEach((node, index) => {
      const category = node.id || node.category;
      const angle = index * angleStep - Math.PI / 2;
      const categoryX = centerX + radius * Math.cos(angle);
      const categoryY = centerY + radius * Math.sin(angle);
      const color = getCategoryColor(category);
      
      nodes.push({
        id: category,
        type: 'custom',
        position: { x: categoryX, y: categoryY },
        data: {
          label: node.label || category.toUpperCase(),
          description: node.description || '',
          type: '5w1h',
          category: category,
          color: color,
          borderColor: '#34495e',
          textColor: 'white',
          isHeaderMode
        },
        draggable: !isHeaderMode,
        sourcePosition: Position.Right,  // 添加這行
        targetPosition: Position.Left    // 添加這行
      });

      // 添加邊 - 確保 source 和 target 的 id 正確
      edges.push({
        id: `e-center-${category}`,
        source: 'center',
        target: category,
        type: 'smoothstep',
        animated: false,
        label: node.description || '',
        labelStyle: { 
          fill: '#2c3e50',
          fontWeight: 500,
          fontSize: isHeaderMode ? '10px' : '12px',
          fontFamily: 'Arial, sans-serif'
        },
        labelBgStyle: { 
          fill: 'white',
          fillOpacity: 0.9
        },
        labelBgPadding: [8, 4],
        style: { 
          stroke: color,
          strokeWidth: isHeaderMode ? 2 : 2.5
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: color,
          width: isHeaderMode ? 18 : 22,
          height: isHeaderMode ? 18 : 22
        }
      });
    });

    console.log('生成的 nodes:', nodes.length);  // 添加除錯訊息
    console.log('生成的 edges:', edges.length);  // 添加除錯訊息
    console.log('edges 詳情:', edges);            // 添加除錯訊息

    return { nodes, edges };
  };

  const handleNodeClick = useCallback((event, node) => {
    if (!isHeaderMode && node.data.type !== 'detail') {
      setSelectedNode(node);
    }
  }, [isHeaderMode]);

  const handleReload = () => {
    loadData();
  };

  if (isLoading) {
    return (
      <div style={{ 
        width: '100%', 
        height: `${height}px`, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: 'radial-gradient(circle at center, #f8f9fa 0%, #e9ecef 100%)',
        borderRadius: isHeaderMode ? '8px' : '15px',
        border: isHeaderMode ? 'none' : '2px solid #e0e6ed'
      }}>
        <div style={{ fontSize: '16px', color: '#7f8c8d' }}>
          載入中...
        </div>
      </div>
    );
  }

  return (
    <>
      <div style={{ 
        width: '100%', 
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          width: '100%',
          height: `${height}px`,
          background: 'radial-gradient(circle at center, #f8f9fa 0%, #e9ecef 100%)',
          borderRadius: isHeaderMode ? '8px' : '15px',
          border: isHeaderMode ? 'none' : '2px solid #e0e6ed',
          overflow: 'hidden'
        }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            attributionPosition="bottom-left"
            proOptions={{ hideAttribution: true }}
            nodesDraggable={!isHeaderMode}
            nodesConnectable={false}
            elementsSelectable={!isHeaderMode}
            panOnDrag={!isHeaderMode}
            zoomOnScroll={!isHeaderMode}
            panOnScroll={false}
            minZoom={0.5}
            maxZoom={2}
            defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          >
            <Background 
              color="#dee2e6" 
              gap={16} 
              size={1}
            />
            {!isHeaderMode && <Controls showInteractive={false} />}
            {!isHeaderMode && (
              <MiniMap 
                nodeColor={(node) => node.data.color || '#95a5a6'}
                maskColor="rgba(0, 0, 0, 0.1)"
                style={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.8)',
                  border: '1px solid #e0e6ed'
                }}
              />
            )}
          </ReactFlow>
        </div>

        {!isHeaderMode && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '15px',
            padding: '0 10px',
            flexWrap: 'wrap',
            gap: '10px'
          }}>
            <p style={{ 
              color: '#7f8c8d', 
              fontSize: '11px', 
              margin: 0,
              flex: 1,
              lineHeight: 1.2
            }}>
              💡 可以拖動背景移動圖形、縮放以中心為基準，或拖動個別節點調整位置
            </p>
            <button
              onClick={handleReload}
              style={{
                background: '#3498db',
                color: 'white',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '20px',
                cursor: 'pointer',
                fontSize: '12px',
                margin: 0,
                transition: 'background 0.3s ease',
                whiteSpace: 'nowrap',
                minWidth: '80px'
              }}
              onMouseOver={(e) => e.target.style.background = '#2980b9'}
              onMouseOut={(e) => e.target.style.background = '#3498db'}
            >
              重新載入
            </button>
          </div>
        )}
      </div>

      {selectedNode && fullData && (
        <NodeDetailModal 
          node={selectedNode} 
          data={fullData}
          onClose={() => setSelectedNode(null)} 
        />
      )}
    </>
  );
};

// 兼容舊版 API 的函數
export const createHeaderVisualization = (containerRef, reportTitle, isModal = false, topicId = null) => {
  if (!containerRef.current) return null;

  containerRef.current.innerHTML = '';
  
  const React = require('react');
  const ReactDOM = require('react-dom/client');
  
  const height = isModal ? 600 : 280;
  const isHeaderMode = !isModal;
  
  const root = ReactDOM.createRoot(containerRef.current);
  root.render(
    React.createElement(FiveW1HVisualization, {
      topicTitle: reportTitle || "專題分析",
      topicId: topicId,
      isHeaderMode: isHeaderMode,
      height: height,
      supabase: window.supabase || null
    })
  );
  
  return {
    destroy: () => {
      root.unmount();
    },
    reloadData: () => {
      root.render(
        React.createElement(FiveW1HVisualization, {
          topicTitle: reportTitle || "專題分析",
          topicId: topicId,
          isHeaderMode: isHeaderMode,
          height: height,
          supabase: window.supabase || null
        })
      );
    }
  };
};

export default FiveW1HVisualization;
