/**
 * 防自殺聲明配置文件
 * 這段文字會直接附加在新聞內容的最後
 * 用空行分段,會被 renderArticleText 自動轉成 <p> 標籤
 */

export const SUICIDE_WARNING_TEXT = {
  'zh-TW': `

如果您或您認識的人正在經歷心理困擾或自殺念頭,請立即尋求幫助。以下資源可為您提供支持:\n

📞 安心專線：1925 (依舊愛我)\n
📞 張老師專線：1980\n
📞 生命線專線：1995\n

勇敢求救並非弱者,生命求救一定會找到出路`,

  'en': `

If you or someone you know is experiencing mental distress or suicidal thoughts, please seek help immediately. The following resources are available to support you:\n

📞 1925 Suicide Prevention Hotline\n
📞 Teacher Zhang Hotline: 1980\n
📞 Lifeline: 1995\n

Asking for help is not a sign of weakness, reaching out can save a life`,

  'jp': `

もしあなたやあなたの知り合いが精神的な苦痛や自殺念慮を抱えている場合は、すぐに助けを求めてください。以下のリソースがサポートを提供できます:\n

📞 安心専線：1925\n
📞 張老師専線：1980\n
📞 生命線：1995\n

助けを求めることは弱さではありません、命の救いは必ず見つかります`,

  'id': `

Jika Anda atau seseorang yang Anda kenal mengalami kesulitan mental atau pikiran untuk bunuh diri, segera cari bantuan. Sumber daya berikut dapat memberikan dukungan:\n

📞 Saluran Darurat: 1925\n
📞 Saluran Guru Zhang: 1980\n
📞 Saluran Kehidupan: 1995\n

Meminta bantuan bukanlah tanda kelemahan, mencari pertolongan pasti akan menemukan jalan keluar`
};

export const getSuicideWarningText = (language = 'zh-TW') => {
  return SUICIDE_WARNING_TEXT[language] || SUICIDE_WARNING_TEXT['zh-TW'];
};

