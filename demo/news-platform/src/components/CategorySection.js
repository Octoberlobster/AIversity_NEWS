import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './../css/UnifiedNewsCard.css';
import UnifiedNewsCard from './UnifiedNewsCard';

// 分類配置
const categories = {
  '政治': { id: 'politics', name: '政治', color: '#ef4444' },
  '社會': { id: 'society', name: '社會', color: '#10b981' },
  '科學與科技': { id: 'scienceandtech', name: '科學與科技', color: '#8b5cf6' },
  '國際': { id: 'international', name: '國際', color: '#f59e0b' },
  '生活': { id: 'life', name: '生活', color: '#06b6d4' },
  '運動': { id: 'sports', name: '運動', color: '#059669' },
  '娛樂': { id: 'entertainment', name: '娛樂', color: '#ec4899' },
  '財經': { id: 'finance', name: '財經', color: '#10b981' },
  '醫療保健': { id: 'health', name: '醫療保健', color: '#ef4444' }
};

// 模擬新聞資料
const newsData = {
  politics: [
    {
      id: 1,
      title: "立法院通過重要法案",
      description: "立法院今日通過多項重要法案，包括經濟發展和社會福利相關政策。",
      time: "2024-01-15 14:30",
      views: "1.5k"
    },
    {
      id: 2,
      title: "總統府發布最新政策聲明",
      description: "政府針對當前經濟情勢發布最新政策方針，強調穩定發展的重要性。",
      time: "2024-01-15 12:45",
      views: "2.1k"
    },
    {
      id: 3,
      title: "政黨協商達成共識",
      description: "各政黨在重要議題上達成共識，展現民主政治的成熟發展。",
      time: "2024-01-15 10:20",
      views: "1.8k"
    },
    {
      id: 4,
      title: "地方選舉準備工作",
      description: "各地方政府積極準備即將到來的選舉，確保選舉公正透明。",
      time: "2024-01-15 09:15",
      views: "2.3k"
    },
    {
      id: 5,
      title: "外交政策新方向",
      description: "政府宣布新的外交政策方向，加強與國際社會的合作關係。",
      time: "2024-01-15 08:30",
      views: "1.9k"
    },
    {
      id: 6,
      title: "國防政策調整",
      description: "國防部宣布新的國防政策調整，提升國家安全防護能力。",
      time: "2024-01-15 07:45",
      views: "2.7k"
    },
    {
      id: 7,
      title: "立法院委員會審議",
      description: "立法院各委員會積極審議重要法案，提升立法效率。",
      time: "2024-01-15 06:20",
      views: "1.6k"
    },
    {
      id: 8,
      title: "政府施政報告",
      description: "行政院長向立法院提出施政報告，說明政府各項政策進展。",
      time: "2024-01-15 05:10",
      views: "2.0k"
    }
  ],
  society: [
    {
      id: 9,
      title: "社會福利政策新進展",
      description: "政府推出新的社會福利政策，旨在改善弱勢群體的生活品質。",
      time: "2024-01-15 15:45",
      views: "3.2k"
    },
    {
      id: 10,
      title: "教育改革新方向",
      description: "教育部宣布新的教育改革方案，強調素質教育和創新教學的重要性。",
      time: "2024-01-15 13:20",
      views: "2.8k"
    },
    {
      id: 11,
      title: "社區營造新計畫",
      description: "政府推出新的社區營造計畫，鼓勵居民參與社區發展。",
      time: "2024-01-15 11:30",
      views: "1.6k"
    },
    {
      id: 12,
      title: "環保意識提升",
      description: "民眾環保意識持續提升，綠色生活成為新趨勢。",
      time: "2024-01-15 10:15",
      views: "2.1k"
    },
    {
      id: 13,
      title: "交通安全新措施",
      description: "交通部推出新的交通安全措施，降低交通事故發生率。",
      time: "2024-01-15 09:40",
      views: "1.9k"
    },
    {
      id: 14,
      title: "文化傳承活動",
      description: "各地舉辦傳統文化傳承活動，保護珍貴的文化遺產。",
      time: "2024-01-15 08:25",
      views: "1.4k"
    },
    {
      id: 15,
      title: "社會公益活動",
      description: "民間團體舉辦多項社會公益活動，關懷弱勢族群。",
      time: "2024-01-15 07:50",
      views: "1.8k"
    },
    {
      id: 16,
      title: "志願服務推廣",
      description: "政府積極推廣志願服務，鼓勵民眾參與社會服務。",
      time: "2024-01-15 06:35",
      views: "1.3k"
    }
  ],
  scienceandtech: [
    {
      id: 17,
      title: "量子物理研究新突破",
      description: "科學家發現新的量子現象，可能為未來科技發展帶來革命性影響。",
      time: "2024-01-15 16:20",
      views: "4.1k"
    },
    {
      id: 18,
      title: "基因編輯技術進展",
      description: "CRISPR技術在治療遺傳疾病方面取得重大進展，為醫學發展開闢新道路。",
      time: "2024-01-15 14:50",
      views: "2.9k"
    },
    {
      id: 19,
      title: "天文學重大發現",
      description: "天文學家發現新的系外行星，為尋找外星生命提供新線索。",
      time: "2024-01-15 12:30",
      views: "3.5k"
    },
    {
      id: 20,
      title: "材料科學新突破",
      description: "科學家開發出新型超導材料，在低溫下實現零電阻傳導。",
      time: "2024-01-15 11:15",
      views: "2.3k"
    },
    {
      id: 21,
      title: "生物技術新應用",
      description: "生物技術在農業領域取得新進展，提高作物產量和抗病能力。",
      time: "2024-01-15 10:40",
      views: "1.8k"
    },
    {
      id: 22,
      title: "氣候科學研究",
      description: "科學家發布最新的氣候變遷研究報告，揭示全球暖化趨勢。",
      time: "2024-01-15 09:25",
      views: "2.7k"
    },
    {
      id: 23,
      title: "神經科學進展",
      description: "科學家在腦部研究方面取得新進展，了解大腦運作機制。",
      time: "2024-01-15 08:10",
      views: "2.1k"
    },
    {
      id: 24,
      title: "化學研究新發現",
      description: "化學家發現新的分子結構，為藥物研發提供新方向。",
      time: "2024-01-15 07:35",
      views: "1.9k"
    },
    {
      id: 25,
      title: "AI 技術突破性進展",
      description: "人工智慧在自然語言處理方面取得重大突破，應用範圍進一步擴大。",
      time: "2024-01-15 17:30",
      views: "5.3k"
    },
    {
      id: 26,
      title: "5G網路建設新進展",
      description: "全國5G網路覆蓋率持續提升，為智慧城市建設奠定基礎。",
      time: "2024-01-15 15:45",
      views: "3.7k"
    },
    {
      id: 27,
      title: "區塊鏈技術應用",
      description: "區塊鏈技術在金融和供應鏈領域的應用日益廣泛，提升交易安全性。",
      time: "2024-01-15 13:20",
      views: "3.2k"
    },
    {
      id: 28,
      title: "物聯網發展趨勢",
      description: "物聯網設備數量持續增長，智慧家居和智慧城市應用普及。",
      time: "2024-01-15 11:50",
      views: "2.8k"
    },
    {
      id: 29,
      title: "雲端運算新服務",
      description: "各大科技公司推出新的雲端運算服務，降低企業數位化成本。",
      time: "2024-01-15 10:25",
      views: "2.1k"
    },
    {
      id: 30,
      title: "虛擬實境技術",
      description: "VR/AR技術在教育、娛樂和商業領域的應用越來越廣泛。",
      time: "2024-01-15 09:10",
      views: "1.9k"
    },
    {
      id: 31,
      title: "機器學習應用",
      description: "機器學習技術在各行業的應用日益廣泛，提升工作效率。",
      time: "2024-01-15 08:35",
      views: "2.4k"
    },
    {
      id: 32,
      title: "網路安全技術",
      description: "網路安全技術不斷創新，保護數位資產和個人隱私。",
      time: "2024-01-15 07:20",
      views: "2.0k"
    }
  ],
  international: [
    {
      id: 33,
      title: "國際貿易新協議",
      description: "多國簽署新的貿易協議，促進全球經濟合作與發展。",
      time: "2024-01-15 18:15",
      views: "2.5k"
    },
    {
      id: 34,
      title: "聯合國氣候峰會",
      description: "各國領導人齊聚聯合國氣候峰會，討論全球氣候變遷應對策略。",
      time: "2024-01-15 16:40",
      views: "3.8k"
    },
    {
      id: 35,
      title: "國際安全合作",
      description: "多國加強國際安全合作，共同應對全球安全挑戰。",
      time: "2024-01-15 14:55",
      views: "2.9k"
    },
    {
      id: 36,
      title: "全球經濟復甦",
      description: "全球經濟出現復甦跡象，各國經濟指標逐步改善。",
      time: "2024-01-15 13:20",
      views: "3.1k"
    },
    {
      id: 37,
      title: "國際教育合作",
      description: "各國加強教育領域合作，促進文化交流和人才培養。",
      time: "2024-01-15 11:45",
      views: "1.7k"
    },
    {
      id: 38,
      title: "全球衛生合作",
      description: "國際社會加強衛生領域合作，共同應對公共衛生挑戰。",
      time: "2024-01-15 10:30",
      views: "2.3k"
    },
    {
      id: 39,
      title: "國際科技合作",
      description: "各國加強科技領域合作，共同推動創新發展。",
      time: "2024-01-15 09:15",
      views: "2.0k"
    },
    {
      id: 40,
      title: "國際文化交流",
      description: "國際文化交流活動頻繁，促進各國文化理解。",
      time: "2024-01-15 08:00",
      views: "1.6k"
    }
  ],
  life: [
    {
      id: 41,
      title: "健康生活新趨勢",
      description: "現代人越來越重視健康生活，運動和飲食習慣正在改變。",
      time: "2024-01-15 19:00",
      views: "1.8k"
    },
    {
      id: 42,
      title: "旅遊業復甦跡象",
      description: "隨著疫情趨緩，國內旅遊業出現明顯復甦跡象，各地景點人潮回流。",
      time: "2024-01-15 17:25",
      views: "2.2k"
    },
    {
      id: 43,
      title: "美食文化新發展",
      description: "台灣美食文化持續發展，傳統與創新結合創造新風味。",
      time: "2024-01-15 15:50",
      views: "1.5k"
    },
    {
      id: 44,
      title: "時尚產業新趨勢",
      description: "永續時尚成為新趨勢，環保材質和循環經濟受到重視。",
      time: "2024-01-15 14:15",
      views: "1.9k"
    },
    {
      id: 45,
      title: "寵物經濟興起",
      description: "寵物經濟快速發展，相關產業和服務日益完善。",
      time: "2024-01-15 12:40",
      views: "1.6k"
    },
    {
      id: 46,
      title: "居家生活新方式",
      description: "疫情改變居家生活方式，遠距工作和居家娛樂成為常態。",
      time: "2024-01-15 11:05",
      views: "2.0k"
    },
    {
      id: 47,
      title: "休閒娛樂新選擇",
      description: "民眾休閒娛樂選擇多樣化，戶外活動和室內娛樂並重。",
      time: "2024-01-15 09:30",
      views: "1.7k"
    },
    {
      id: 48,
      title: "生活品質提升",
      description: "整體生活品質持續提升，民眾對生活環境要求更高。",
      time: "2024-01-15 08:55",
      views: "1.4k"
    }
  ],
  sports: [
    {
      id: 49,
      title: "奧運選手備戰情況",
      description: "我國奧運選手積極備戰，各項運動項目都有優秀表現。",
      time: "2024-01-15 20:30",
      views: "3.1k"
    },
    {
      id: 50,
      title: "職業運動新賽季",
      description: "各大職業運動聯賽新賽季即將開始，各隊積極備戰。",
      time: "2024-01-15 18:45",
      views: "2.7k"
    },
    {
      id: 51,
      title: "足球聯賽精彩對決",
      description: "國內足球聯賽上演精彩對決，球迷熱情支持本土球隊。",
      time: "2024-01-15 17:10",
      views: "2.3k"
    },
    {
      id: 52,
      title: "籃球運動發展",
      description: "籃球運動在台灣持續發展，年輕選手表現亮眼。",
      time: "2024-01-15 15:35",
      views: "1.8k"
    },
    {
      id: 53,
      title: "田徑比賽新紀錄",
      description: "國內田徑比賽創下新紀錄，選手實力持續提升。",
      time: "2024-01-15 14:00",
      views: "1.5k"
    },
    {
      id: 54,
      title: "游泳運動推廣",
      description: "游泳運動推廣計畫成效顯著，參與人數持續增加。",
      time: "2024-01-15 12:25",
      views: "1.2k"
    },
    {
      id: 55,
      title: "棒球運動熱潮",
      description: "棒球運動在台灣持續受到歡迎，各級聯賽精彩可期。",
      time: "2024-01-15 10:50",
      views: "2.1k"
    },
    {
      id: 56,
      title: "運動產業發展",
      description: "運動產業蓬勃發展，相關設備和服務日益完善。",
      time: "2024-01-15 09:15",
      views: "1.6k"
    }
  ],
  entertainment: [
    {
      id: 57,
      title: "電影產業新發展",
      description: "國產電影在國際影展中獲得佳績，展現台灣電影產業的實力。",
      time: "2024-01-15 21:45",
      views: "2.9k"
    },
    {
      id: 58,
      title: "音樂產業數位化",
      description: "音樂產業加速數位化轉型，串流平台成為主要收入來源。",
      time: "2024-01-15 20:10",
      views: "1.6k"
    },
    {
      id: 59,
      title: "電視劇製作新趨勢",
      description: "台灣電視劇製作水準提升，題材多樣化受到觀眾歡迎。",
      time: "2024-01-15 18:35",
      views: "2.1k"
    },
    {
      id: 60,
      title: "綜藝節目創新",
      description: "綜藝節目形式創新，結合新媒體技術提升觀眾體驗。",
      time: "2024-01-15 17:00",
      views: "1.7k"
    },
    {
      id: 61,
      title: "網路劇興起",
      description: "網路劇成為新興娛樂形式，年輕觀眾收視習慣改變。",
      time: "2024-01-15 15:25",
      views: "1.4k"
    },
    {
      id: 62,
      title: "藝人發展新方向",
      description: "藝人發展多元化，跨領域合作成為新趨勢。",
      time: "2024-01-15 13:50",
      views: "1.8k"
    },
    {
      id: 63,
      title: "遊戲產業發展",
      description: "遊戲產業快速發展，國產遊戲在國際市場表現亮眼。",
      time: "2024-01-15 12:15",
      views: "2.3k"
    },
    {
      id: 64,
      title: "表演藝術新趨勢",
      description: "表演藝術形式創新，結合科技元素提升觀眾體驗。",
      time: "2024-01-15 10:40",
      views: "1.5k"
    }
  ],
  finance: [
    {
      id: 65,
      title: "股市創新高",
      description: "台股指數創下歷史新高，投資人信心持續提升。",
      time: "2024-01-15 22:30",
      views: "4.5k"
    },
    {
      id: 66,
      title: "央行利率政策",
      description: "央行維持利率不變，強調穩定物價和經濟發展的重要性。",
      time: "2024-01-15 20:55",
      views: "3.2k"
    },
    {
      id: 67,
      title: "外匯市場波動",
      description: "國際外匯市場出現波動，影響全球經濟和貿易。",
      time: "2024-01-15 19:20",
      views: "2.8k"
    },
    {
      id: 68,
      title: "房地產市場趨勢",
      description: "房地產市場出現新趨勢，價格和需求結構發生變化。",
      time: "2024-01-15 17:45",
      views: "3.5k"
    },
    {
      id: 69,
      title: "金融科技發展",
      description: "金融科技快速發展，改變傳統金融服務模式。",
      time: "2024-01-15 16:10",
      views: "2.2k"
    },
    {
      id: 70,
      title: "保險業新政策",
      description: "保險業推出新政策，提升服務品質和風險管理。",
      time: "2024-01-15 14:35",
      views: "1.9k"
    },
    {
      id: 71,
      title: "投資理財新趨勢",
      description: "投資理財方式多元化，民眾理財觀念持續提升。",
      time: "2024-01-15 13:00",
      views: "2.6k"
    },
    {
      id: 72,
      title: "企業財報表現",
      description: "各大企業財報表現亮眼，反映經濟復甦趨勢。",
      time: "2024-01-15 11:25",
      views: "2.1k"
    }
  ],
  health: [
    {
      id: 73,
      title: "醫療科技新突破",
      description: "新型醫療技術在治療癌症方面取得重大進展，為患者帶來新希望。",
      time: "2024-01-15 23:15",
      views: "3.8k"
    },
    {
      id: 74,
      title: "公共衛生新政策",
      description: "政府推出新的公共衛生政策，加強疾病預防和健康促進。",
      time: "2024-01-15 21:40",
      views: "2.4k"
    },
    {
      id: 75,
      title: "心理健康關注",
      description: "社會對心理健康的重視程度提升，相關服務和資源增加。",
      time: "2024-01-15 20:05",
      views: "2.1k"
    },
    {
      id: 76,
      title: "疫苗研發進展",
      description: "新型疫苗研發取得進展，為疾病預防提供新選擇。",
      time: "2024-01-15 18:30",
      views: "2.7k"
    },
    {
      id: 77,
      title: "遠距醫療發展",
      description: "遠距醫療技術快速發展，提升醫療服務的可及性。",
      time: "2024-01-15 16:55",
      views: "1.8k"
    },
    {
      id: 78,
      title: "營養健康新觀念",
      description: "營養健康觀念更新，科學飲食成為健康生活的重要組成。",
      time: "2024-01-15 15:20",
      views: "1.5k"
    },
    {
      id: 79,
      title: "中醫藥發展",
      description: "中醫藥現代化發展，傳統醫學與現代科技結合。",
      time: "2024-01-15 13:45",
      views: "2.0k"
    },
    {
      id: 80,
      title: "醫療設備創新",
      description: "醫療設備技術創新，提升診斷和治療效果。",
      time: "2024-01-15 12:10",
      views: "1.7k"
    }
  ]
};

function CategorySection({ category }) {
  const [showAllNews, setShowAllNews] = useState(false);
  const currentCategory = categories[category];
  const currentNews = newsData[currentCategory?.id] || [];

  if (!currentCategory) {
    return (
      <section className="catSec">
        <div className="catSec__header">
          <h2 className="catSec__title">分類新聞</h2>
        </div>
        <div className="catSec__empty">找不到該分類的新聞</div>
      </section>
    );
  }

  // 轉成 UnifiedNewsCard 所需格式（沿用你的轉換邏輯）
  const convertedNewsData = currentNews.map((news) => ({
    id: news.id,
    title: news.title,
    category: currentCategory.name,
    date: news.time,
    author: '記者',
    sourceCount: 3,
    shortSummary: news.description,
    longSummary: `${news.description}\n\n${news.description}`,
    relatedNews: [],
    views: news.views,
    comments: '0',
    likes: '0',
    keywords: [currentCategory.name],
    terms: [],
  }));

  const displayNews = showAllNews
    ? convertedNewsData
    : convertedNewsData.slice(0, 8);

  return (
    <section className="catSec">
      <div className="catSec__header">
        <h2 className="catSec__title">{category}新聞</h2>
        {/* 若之後要放「查看全部」可直接用這個連結樣式 */}
        {/* <Link className="catSec__viewAll" to={`/category/${currentCategory.id}`}>查看全部</Link> */}
      </div>

      <UnifiedNewsCard limit={displayNews.length} customData={displayNews} />

      {!showAllNews && currentNews.length > 8 && (
        <div className="catSec__moreWrap">
          <button className="btnPrimary" onClick={() => setShowAllNews(true)}>
            閱讀更多新聞
          </button>
        </div>
      )}
    </section>
  );
}

export default CategorySection;