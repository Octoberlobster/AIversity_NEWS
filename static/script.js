document.getElementById('search-button').addEventListener('click', () => {
    const keyword = document.getElementById('keyword').value.trim();
    if (!keyword) {
        alert('請輸入關鍵字');
        return;
    }

     // 顯示加載動畫
     const loadingSpinner = document.getElementById('loading-spinner');
     loadingSpinner.style.display = 'block';

    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keyword }) // 將輸入的關鍵字傳送到後端
    })
    .then(response => response.json())
    .then(data => {
        loadingSpinner.style.display = 'none';
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
});

function displayNews(newsList) {
    const container = document.getElementById('news-container');
    container.innerHTML = ''; // 清空舊的結果

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
        const newsLink = document.createElement('button');
        newsLink.textContent = '閱讀全文';
        newsLink.addEventListener('click', () => {
            fetch('/news', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(news) // 傳遞整條新聞的資料
            })
            .then(response => response.text())
            .then(html => {
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
}







