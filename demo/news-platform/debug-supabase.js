// Supabase 資料載入除錯腳本
// 這個腳本幫助我們了解從 Supabase 獲得的資料結構

import { FiveW1HVisualization } from './src/components/FiveW1HVisualization.js';

// 創建一個測試實例
const debugViz = new FiveW1HVisualization('debug', {
  width: 800,
  height: 600,
  isHeaderMode: false
});

// 模擬 Supabase 資料結構
const mockSupabaseData = {
  topic_title: "大罷免",
  mind_map_detail: {
    center_node: {
      id: "center",
      label: "大罷免事件概述",
      description: "2025年台灣發生了針對多位國民黨立委的罷免案，以及核三重啟公投。"
    },
    main_nodes: [
      {
        id: "who",
        label: "相關人物",
        description: "包括被罷免的國民黨立委、發起罷免的公民團體等。"
      },
      {
        id: "what",
        label: "事件本質",
        description: "主要包含針對國民黨立委的罷免投票及核三重啟公投。"
      }
    ],
    detailed_nodes: {
      who_nodes: [
        {
          id: "who1",
          label: "江啟臣",
          description: "國民黨立法院副院長，是此次罷免案的主要目標之一。"
        }
      ]
    }
  }
};

// 測試資料轉換
console.log('🧪 開始測試資料轉換...');
console.log('📋 模擬 Supabase 資料:', mockSupabaseData);

try {
  // 測試 transformSupabaseData 方法
  const transformedData = debugViz.transformSupabaseData(mockSupabaseData.mind_map_detail);
  console.log('✅ 資料轉換成功:');
  console.log('  📊 節點數量:', transformedData.nodes.length);
  console.log('  🔗 連接數量:', transformedData.links.length);
  console.log('  📋 節點資料:', transformedData.nodes);
  console.log('  🔗 連接資料:', transformedData.links);
  
  // 測試預設資料
  const defaultData = debugViz.getDefaultData();
  console.log('✅ 預設資料結構:');
  console.log('  📊 節點數量:', defaultData.nodes.length);
  console.log('  🔗 連接數量:', defaultData.links.length);
  
} catch (error) {
  console.error('❌ 測試失敗:', error);
}

// 測試字串格式的 JSON
console.log('\n🧪 測試字串格式的 JSON...');
const stringJsonData = JSON.stringify(mockSupabaseData.mind_map_detail);
console.log('📋 字串格式的 JSON:', stringJsonData);

try {
  const parsedData = JSON.parse(stringJsonData);
  console.log('✅ JSON 解析成功:', parsedData);
  
  const transformedData2 = debugViz.transformSupabaseData(parsedData);
  console.log('✅ 字串 JSON 轉換成功:');
  console.log('  📊 節點數量:', transformedData2.nodes.length);
  
} catch (error) {
  console.error('❌ 字串 JSON 測試失敗:', error);
}

// 導出測試函數
export function testSupabaseDataLoading() {
  console.log('🚀 開始測試 Supabase 資料載入...');
  
  // 這裡可以添加更多測試邏輯
  return {
    mockData: mockSupabaseData,
    debugViz: debugViz
  };
}

// 如果直接執行此腳本
if (typeof window !== 'undefined') {
  window.testSupabaseDataLoading = testSupabaseDataLoading;
  console.log('🌐 Supabase 除錯腳本已載入到全域範圍');
  console.log('使用方法: testSupabaseDataLoading()');
}
