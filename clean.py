import pandas as pd
import re
    
def remove_special_chars(text):
        """
        去除字串中的特殊符號。
        Returns:
            清理後的字串。
        """    
        
        if isinstance(text, list):  # 如果是列表，將其合併為字符串
            text = " ".join(map(str, text))
        return re.sub(r'[^\w\s]', '', text)  # 只保留字母、數字、底線和空格
    
def clean_data(input_df):
    """
    清理新聞數據中的特殊符號，並移除包含空白欄位的資料行。
    Args:
        input_df (DataFrame): 輸入的數據。
    Returns:
        DataFrame: 清理後的數據。
    """
    
    # 讀取 CSV 檔案
    df = input_df

    df['Title'] = df['Title'].apply(remove_special_chars)
    df['Content'] = df['Content'].apply(remove_special_chars)
    
    # 移除包含空白欄位的資料行
    df = df[df['Title'].str.strip().astype(bool)]
    df = df[df['Content'].str.strip().astype(bool)]
    
    # 儲存清理後的資料
    df.to_csv('cleaned_news_data.csv', index=False)
    return df
        