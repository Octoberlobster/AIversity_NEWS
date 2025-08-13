import os
import json
from io import BytesIO
from PIL import Image
from tqdm import tqdm
# 確保您已安裝所需套件: pip install Pillow tqdm

def _ensure_dir(path: str):
    """【修正】確保目錄存在。"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def _save_png_from_bytes(img_bytes: bytes, out_path: str) -> bool:
    """將二進制數據解碼並儲存為 PNG 圖片。"""
    try:
        # 將二進制數據讀入記憶體
        image_stream = BytesIO(img_bytes)
        # 使用 Pillow 開啟
        image = Image.open(image_stream)
        # 確保目標資料夾存在
        _ensure_dir(os.path.dirname(out_path))
        # 儲存為 PNG 檔案
        image.save(out_path, format="PNG", optimize=True)
        return True
    except Exception as e:
        # 如果二進制數據不是有效的圖片格式，Pillow會報錯
        print(f"Error decoding/saving {os.path.basename(out_path)}: {e}")
        return False

def decode_from_metadata(metadata_path: str, base_dir: str):
    """讀取 metadata.json，找到所有 .bin 檔案，並將它們轉換為 .png。"""
    if not os.path.exists(metadata_path):
        print(f"Error: Metadata file not found at {metadata_path}")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    images_to_process = metadata.get("images", [])
    if not images_to_process:
        print("No images found in metadata file.")
        return
    
    print(f"Found {len(images_to_process)} images to decode.")
    
    succeeded = 0
    for image_info in tqdm(images_to_process, desc="Decoding images", ncols=100):
        bin_rel_path = image_info.get("binary_path")
        if not bin_rel_path: continue
            
        bin_full_path = os.path.join(base_dir, bin_rel_path)
        png_full_path = os.path.splitext(bin_full_path)[0] + ".png"
        
        if not os.path.exists(bin_full_path):
            print(f"Warning: Binary file not found, skipping: {bin_full_path}")
            continue

        with open(bin_full_path, "rb") as f:
            img_bytes = f.read()
            
        if _save_png_from_bytes(img_bytes, png_full_path):
            succeeded += 1
            
    print(f"\nDecoding complete. Successfully created {succeeded} of {len(images_to_process)} PNG images.")

if __name__ == '__main__':
    output_directory = "output_bin"
    metadata_file = os.path.join(output_directory, "image_metadata.json")
    decode_from_metadata(metadata_path=metadata_file, base_dir=output_directory)

