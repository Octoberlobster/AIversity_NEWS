// FiveW1H 視覺化演示腳本
// 這個腳本展示了如何使用 FiveW1HVisualization 組件

import { FiveW1HVisualization } from './src/components/FiveW1HVisualization.js';

// 演示資料 - 大罷免事件
const demoData = {
  center_node: {
    id: "center",
    label: "大罷免事件概述",
    description: "2025年台灣發生了針對多位國民黨立委的罷免案，以及核三重啟公投。罷免案由公民團體發起，民進黨支持，但最終均未通過。事件反映台灣政治進入朝野勢均力敵的新局面，並引發內閣改組及政黨內部的檢討。"
  },
  main_nodes: [
    {
      id: "what",
      label: "事件本質",
      description: "主要包含針對國民黨立委的罷免投票及核三重啟公投，是檢驗民意和政治力量對比的事件。"
    },
    {
      id: "where",
      label: "事件地點",
      description: "主要集中在台灣中部選區，尤其是國民黨立委集中的區域，以及立法院等政治中心。"
    },
    {
      id: "why",
      label: "事件起因",
      description: "罷免案起因於公民團體對部分立委的不滿，以及民進黨在國會失勢後試圖重塑政治結構。公投則反映了對能源政策及核能使用的不同意見。"
    },
    {
      id: "who",
      label: "相關人物",
      description: "包括被罷免的國民黨立委、發起罷免的公民團體、民進黨及國民黨的政治人物，以及受公投影響的民眾。"
    },
    {
      id: "when",
      label: "發生時間",
      description: "主要發生在2025年8月，包括罷免投票日及前後的政治活動，以及公投的舉行時間。"
    },
    {
      id: "how",
      label: "事件發展",
      description: "通過藍綠陣營的動員、選前衝刺、投票結果及後續的政治反應，展現了事件的發展過程。"
    }
  ],
  detailed_nodes: {
    who_nodes: [
      {
        id: "who1",
        label: "江啟臣",
        description: "國民黨立法院副院長，是此次罷免案的主要目標之一，藍營大咖紛紛為其站台力挺。"
      },
      {
        id: "who2",
        label: "朱立倫",
        description: "國民黨主席，在罷免案中積極為黨籍立委輔選，並在罷免案後點名盧秀燕接任黨魁。"
      },
      {
        id: "who3",
        label: "賴清德",
        description: "台灣總統，面對罷免案及公投結果，宣布內閣改組，並重申尊重司法獨立。"
      },
      {
        id: "who4",
        label: "柯文哲",
        description: "民眾黨前主席，在罷免案後，國民黨呼籲釋放柯文哲，引發朝野對司法獨立的爭論。"
      },
      {
        id: "who5",
        label: "盧秀燕",
        description: "台中市長，國民黨在罷免案後點名盧秀燕接任黨魁，但盧秀燕以市政為重，明確婉拒。"
      }
    ],
    what_nodes: [
      {
        id: "what1",
        label: "立委罷免案選前動員",
        description: "選前藍綠陣營紛紛動員，國民黨大咖齊聚為江啟臣站台，民進黨則批評江啟臣未有效發展地方，雙方陣營全力衝刺。"
      },
      {
        id: "what2",
        label: "罷免案結果與政局",
        description: "罷免案全數未通過，顯示民進黨過去優勢不再，台灣政治進入朝野勢均力敵的新局面，朝小野大僵局持續。"
      },
      {
        id: "what3",
        label: "政黨內外挑戰與應變",
        description: "罷免案後，民進黨面臨檢討反省壓力，國民黨則面臨黨主席繼任難題，賴清德內閣將改組，朝野政黨各自應對。"
      }
    ],
    when_nodes: [
      {
        id: "when1",
        label: "2025年8月22日",
        description: "罷免投票前夕，藍綠陣營加緊動員，蔣萬安南下輔選，罷免團體進行最後衝刺。"
      },
      {
        id: "when2",
        label: "2025年8月23日",
        description: "台灣舉行第二輪立委罷免投票，共有七名國民黨立委接受考驗，罷免案及核三重啟公投均未通過。"
      },
      {
        id: "when3",
        label: "2025年8月26日",
        description: "罷免公投落幕後，賴清德宣布內閣將改組，朱立倫呼籲釋放柯文哲，民進黨團幹部請辭。"
      }
    ],
    where_nodes: [
      {
        id: "where1",
        label: "台中豐原",
        description: "江啟臣的選區，是罷免案的核心地區，藍綠陣營在此展開激烈的選前動員。"
      },
      {
        id: "where2",
        label: "台灣中部",
        description: "此次罷免案的選區主要集中在中部，是藍綠政治勢力角逐的重要地區。"
      },
      {
        id: "where3",
        label: "立法院",
        description: "罷免案及公投結果影響立法院的政治格局，朝野政黨在此進行法案審查及政治角力。"
      }
    ],
    why_nodes: [
      {
        id: "why1",
        label: "政治鬥爭與權力重塑",
        description: "民進黨在國會失勢後，試圖通過罷免案重塑政治結構，挑戰國民黨的勢力。然而，罷免案的正當性受到質疑，被批評為濫用民主、充滿仇恨。罷免案也被視為2026台中市長選舉的前哨戰，可能影響盧秀燕聲望。最終，罷免案的失利反映了民意的轉變和對政治鬥爭的厭倦，朝野政黨都需要重新思考其政治策略和論述，以回應民意期待。"
      }
    ],
    how_nodes: [
      {
        id: "how1",
        label: "藍綠動員與選前衝刺",
        description: "國民黨總動員，邀請蔣萬安、李四川接力掃街輔選，呼籲選民投下「不同意罷免」票。民進黨則採取低調策略，將重點放在選後內閣改組。雙方陣營在投票前黃金週全力衝刺，展開最後較勁。"
      },
      {
        id: "how2",
        label: "內閣改組與人事調整",
        description: "賴清德宣布內閣將於下週啟動改組，以「經濟優先、民生優先」為施政核心。民進黨團幹事長吳思瑤、書記長陳培瑜等五位幹部宣布不續任，引發黨內改組聲浪。"
      },
      {
        id: "how3",
        label: "朝野協商與法案審查",
        description: "朝野協商已就韌性特別條例修正草案、災後重建特別預算案及追加預算案達成共識，將於下週院會處理，顯示國會新會期即將展開重要法案審查。"
      }
    ]
  }
};

// 創建視覺化實例的函數
export async function createFiveW1HDemo(containerId, options = {}) {
  try {
    console.log('🚀 開始創建 FiveW1H 視覺化演示...');
    
    // 創建視覺化實例
    const viz = new FiveW1HVisualization(containerId, {
      width: options.width || 1200,
      height: options.height || 600,
      isHeaderMode: options.isHeaderMode || false,
      ...options
    });
    
    // 載入資料並渲染
    await viz.loadData();
    viz.setupD3();
    viz.render();
    
    console.log('✅ FiveW1H 視覺化演示創建成功！');
    console.log('📋 功能說明:');
    console.log('  - 點擊中心節點查看事件概述和主要要素');
    console.log('  - 點擊 5W1H 節點查看對應類別的詳細資訊');
    console.log('  - 拖拽節點調整位置');
    console.log('  - 使用滑鼠滾輪縮放視圖');
    
    return viz;
  } catch (error) {
    console.error('❌ 創建 FiveW1H 視覺化演示失敗:', error);
    throw error;
  }
}

// 導出演示資料
export { demoData };

// 如果直接執行此腳本
if (typeof window !== 'undefined') {
  // 瀏覽器環境
  window.createFiveW1HDemo = createFiveW1HDemo;
  window.demoData = demoData;
  
  console.log('🌐 FiveW1H 演示腳本已載入到全域範圍');
  console.log('使用方法: createFiveW1HDemo("container-id", options)');
}

