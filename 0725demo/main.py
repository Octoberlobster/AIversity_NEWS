from generate_picture import generate_from_json

if __name__ == "__main__":
    result = generate_from_json(
        input_json="cleaned_final_news.json",
        output_dir="generated_images2",
        # 可選參數：
        # model_id="gemini-2.0-flash-preview-image-generation",
        # max_items=None,  # None 全量
        # max_images_per_article=1,
        # retry_times=3,
        # sleep_between_calls=0.6,
    )
    print(result)
