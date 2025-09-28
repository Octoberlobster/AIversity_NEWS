import requests

def main():
    # API 的 URL
    api_url = "http://127.0.0.1:8000/translate_array/"

    # 要翻譯的文字陣列
    texts_to_translate = [
        "Hello, world!",
        "How are you?"
    ]
    target_language = "zh-TW"  # 目標語言：繁體中文

    # 發送 POST 請求
    payload = {
        "texts": texts_to_translate,
        "target_language": target_language
    }
    response = requests.post(api_url, json=payload)

    # 處理回應
    if response.status_code == 200:
        translated_texts = response.json().get("translated_texts", [])
        print("翻譯後的文字陣列：")
        print(translated_texts)
    else:
        print(f"翻譯失敗，狀態碼: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()