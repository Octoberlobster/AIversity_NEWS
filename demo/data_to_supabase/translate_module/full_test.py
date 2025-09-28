import requests

def main():
    # API 的 URL
    api_url = "http://127.0.0.1:8000/translate_array/"

    # 要翻譯的文字陣列
    texts_to_translate = [
        "Pamela Anderson has nothing against makeup.",
        "It’s just that she’s been there, done that in her younger years.",
        "That’s why now, at 58, she’s attending fashion shows and film premieres with a blissfully bare face."
    ]
    target_language = "ja"  # 目標語言：日文

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