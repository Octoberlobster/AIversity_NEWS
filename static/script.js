let newsData = [];

function handleSearch() {
    const keyword = document.getElementById('keyword').value.trim();
    if (!keyword) {
        alert('請輸入關鍵字');
        return;
    }

    alert('正在搜索新聞，請稍後...');

    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keyword }) // 將輸入的關鍵字傳送到後端
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(data.news);
            displayNews(data.news); // 顯示後端返回的新聞資料
        } else {
            alert('搜尋失敗');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

document.getElementById('keyword').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        handleSearch();
    }
});

document.getElementById('summary-button').addEventListener('click', () => {
    if(newsData.length === 0 ) {
        alert('請先搜索新聞');
        return;
    }

    //把newsData轉成列表
    const news_list = newsData.map(news => ({
        content: news.Content || '',
        title: news.Title || ''
    }));

    console.log("news_list:", JSON.stringify(news_list));

    fetch('/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({news_list })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const summaryContainer = document.getElementById('summary-container');
            const summaryBox = document.getElementById('summary-box');

            // 插入摘要內容
            summaryBox.innerHTML = data.summary;

            // 顯示摘要框
            summaryContainer.style.display = 'block';
        } else {
            alert('生成摘要失敗');
        }
    });
});


function generateReport(content) {
    fetch('/read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ clean_news: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 將分析報告顯示在頁面上
            const analysisContainer = document.getElementById('analysis-container');
            analysisContainer.innerHTML = `
                <h2>因果分析報告</h2>
                <p>${data.analysis.replace(/\n/g, "<br>")}</p> <!-- 支持分段換行 -->
            `;
        } else {
            alert('生成分析報告失敗: ' + data.message);
        }
    })
    .catch(error => {
        console.error('生成分析報告時出錯:', error);
        alert('無法生成分析報告，請稍後再試。');
    });
}


function displayNews(newsList) {
    newsData = newsList; // 保存新聞資料
    const container = document.getElementById('news-container');
    container.innerHTML = ''; // 清空舊的結果

    const summaryContainer = document.getElementById('summary-container');
    summaryContainer.style.display = 'none'; // 隱藏摘要框

    if (!newsList || newsList.length === 0) {
        container.innerHTML = '<p>沒有找到相關新聞</p>';
        return;
    }

    newsList.forEach(news => {
        const newsItem = document.createElement('div');
        newsItem.classList.add('news-item');

        // 檢查 `Title` 是否存在
        if (news.Title) {
            const newsTitle = document.createElement('h3');
            newsTitle.textContent = news.Title; // 顯示新聞標題
            newsItem.appendChild(newsTitle);
        } else {
            console.warn('Missing title for news:', news);
        }

        // 「閱讀全文」按鈕
        /*const newsLink = document.createElement('a');
        newsLink.textContent = '閱讀全文';
        newsLink.target = '_blank';
        newsLink.href = '/news';*/

        const newsLink = document.createElement('button');
        newsLink.textContent = '閱讀全文';

        newsLink.addEventListener('click', () => {
            event.preventDefault(); // 阻止默認行為
            fetch('/news', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(news) // 傳遞整條新聞的資料
            })
            .then(response => response.text())
            .then(html => {
                /*const newWindow = window.open();
                newWindow.document.open();
                newWindow.document.write(html); // 將 HTML 寫入新分頁
                newWindow.document.close();*/
                document.open();
                document.write(html);
                document.close();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('無法加載新聞內容');
            });
        });

        newsItem.appendChild(newsLink);

        container.appendChild(newsItem);
    });
    const summaryButton = document.getElementById('summary-button');
    if (newsList && newsList.length > 0) {
        summaryButton.style.display = 'block';
        summaryButton.disabled = false; // 啟用按鈕
    } else {
        summaryButton.style.display = 'none';
    }
}







