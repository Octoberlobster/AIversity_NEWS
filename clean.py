import pandas as pd
import re

def clean_data(input_file, output_file):
    """
    清理新聞數據中的特殊符號，並移除包含空白欄位的資料行。

    Args:
        input_file: 原始 CSV 檔案的路徑。
        output_file: 清理後的 CSV 檔案的路徑。

    Returns:
        DataFrame: 清理後的數據。
    """
    def remove_special_chars(text):
        """
        去除字串中的特殊符號。

        Args:
            text: 要清理的字串。

        Returns:
            清理後的字串。
        """
        if pd.isna(text):  # 檢查是否為空值
            return text
        return re.sub(r'[^\w\s]', '', text)  # 只保留字母、數字、底線和空格

    try:
        # 讀取 CSV 檔案
        df = pd.read_csv(input_file)

        # 確保有 'Title' 和 'Content' 欄位
        if 'Title' not in df.columns or 'Content' not in df.columns:
            raise ValueError("CSV 文件中缺少 'Title' 或 'Content' 欄位")

        # 清理 'Title' 和 'Content' 欄位
        df['Title'] = df['Title'].apply(remove_special_chars)
        df['Content'] = df['Content'].apply(remove_special_chars)

        # 移除任意欄位為空的行
        df = df.dropna(subset=['Title', 'Content'])

        # 儲存清理後的資料
        df.to_csv(output_file, index=False)
        print(f"清理完成，結果已儲存到 {output_file}")
        return df
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None
