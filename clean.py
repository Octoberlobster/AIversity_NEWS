import csv
import re

def clean_data_to_list(input_file):
    """
    從 CSV 檔案讀取數據，清理特殊符號，移除包含空白欄位的資料行，並以列表形式返回。

    Args:
        input_file: 原始 CSV 檔案的路徑。

    Returns:
        list: 清理後的數據，每一行作為一個子列表（包含標題）。
    """
    def remove_special_chars(text):
        """
        去除字串中的特殊符號。

        Args:
            text: 要清理的字串。

        Returns:
            清理後的字串或 None（若原始字串為空）。
        """
        if text is None or text.strip() == "":  # 檢查是否為空值或空字串
            return None
        return re.sub(r'[^\w\s]', '', text)  # 只保留字母、數字、底線和空格

    try:
        # 讀取 CSV 檔案並轉換為列表
        with open(input_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)  # 讀取標題列
            data_list = [row for row in reader]  # 轉換為列表格式

        # 清理數據
        cleaned_list = []
        for row in data_list:
            # 清理每行的欄位資料
            cleaned_row = [remove_special_chars(cell) for cell in row]

            # 若任何欄位為空（即 None），則跳過該行
            if None in cleaned_row:
                continue

            cleaned_list.append(cleaned_row)

        print("清理完成，資料已轉換為清理後的列表格式")
        return [headers] + cleaned_list  # 返回包含標題的清理後數據
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None
