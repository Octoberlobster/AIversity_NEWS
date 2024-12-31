import pandas as pd

import re
def   clean_data(news_data):
    

    def remove_special_chars(text):
        """
        去除字串中的特殊符號。

        Args:
            text: 要清理的字串。

        Returns:
            清理後的字串。
        """
        cleaned_text = re.sub(r'[^\w\s]', '', text)  # 只保留字母、數字、底線和空格
        return cleaned_text

    # 讀取 CSV 檔案
    df = pd.read_csv('news_data.csv')

    # 清理 'title' 和 'content' 欄位
    df['Title'] = df['Title'].apply(remove_special_chars)
    df['Content'] = df['Content'].apply(remove_special_chars)

    # 儲存清理後的資料
    df.to_csv('cleaned_news_data.csv', index=False)

    return cleaned_news_data
