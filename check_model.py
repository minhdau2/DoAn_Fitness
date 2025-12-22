import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- ĐANG TẢI DANH SÁCH MODEL TỪ GOOGLE ---")

try:
    # Lấy danh sách thô
    all_models = client.models.list()
    
    # In ra tất cả tên model tìm được
    for m in all_models:
        # Chỉ in những cái có chữ 'gemini' cho đỡ rối mắt
        if "gemini" in m.name:
            print(f"👉 {m.name}")

except Exception as e:
    print(f"Lỗi: {e}")