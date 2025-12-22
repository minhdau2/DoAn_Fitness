import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()
my_key = os.getenv("GEMINI_API_KEY")

if not my_key:
    print("❌ LỖI: Không tìm thấy Key trong file .env")
    exit()

client = genai.Client(api_key=my_key)

# Danh sách các tên model có thể dùng (thử từ cái ổn định nhất)
candidates = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-flash-latest",       # Cái này có trong danh sách của bạn
    "gemini-1.5-flash-8b",       # Bản siêu nhẹ
    "gemini-2.0-flash-exp",      # Bản mới (có thể bị giới hạn)
]

print(f"🔑 Đang dùng Key: {my_key[:5]}... (đã ẩn đuôi)")
print("🚀 Đang dò tìm model phù hợp cho bạn...\n")

success_model = None

for model_name in candidates:
    print(f"👉 Đang thử: {model_name} ... ", end="")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Chào, hãy trả lời 'OK' thật ngắn gọn."
        )
        print("✅ THÀNH CÔNG!")
        print(f"   AI trả lời: {response.text}")
        success_model = model_name
        break # Tìm thấy rồi thì dừng lại ngay
    except Exception as e:
        # Chuyển lỗi thành chuỗi để kiểm tra
        error_msg = str(e)
        if "404" in error_msg:
            print("❌ Không tìm thấy (404)")
        elif "429" in error_msg:
            print("⚠️ Quá tải (429 - Hết lượt dùng)")
        else:
            print(f"❌ Lỗi khác: {error_msg[:50]}...")
        time.sleep(1) # Nghỉ 1 xíu trước khi thử cái tiếp theo

print("-" * 30)
if success_model:
    print(f"🏆 CHÚC MỪNG! Model bạn cần dùng là: \"{success_model}\"")
    print("Hãy dùng tên này cho đồ án của bạn nhé!")
else:
    print("😭 Rất tiếc, không model nào chạy được. Hãy kiểm tra lại API Key.")
print("-" * 30)