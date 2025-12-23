import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi # Nếu bạn đã cài certifi thì import, không thì python sẽ tự bỏ qua dòng này nếu lỗi

# 1. Load cấu hình từ file .env
load_dotenv()
uri = os.getenv("MONGO_URI")

# Biến để lưu kết nối
db = None

# 2. Thực hiện kết nối
try:
    if not uri:
        print("❌ LỖI: Chưa tìm thấy 'MONGO_URI' trong file .env")
    else:
        # --- CẤU HÌNH QUAN TRỌNG ĐỂ SỬA LỖI SSL ---
        # Chúng ta thử dùng certifi trước, nếu vẫn lỗi thì dùng cờ "bỏ qua kiểm tra" (tlsAllowInvalidCertificates)
        try:
            ca = certifi.where()
            client = MongoClient(uri, tlsCAFile=ca)
        except:
            # Nếu certifi không được, dùng cách "mạnh tay": Bỏ qua kiểm tra chứng chỉ
            print("⚠️ Đang dùng chế độ kết nối không kiểm tra SSL (Debug Mode)...")
            client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
        
        # Lệnh 'ping' để kiểm tra xem có thông mạng không
        client.admin.command('ping')
        
        print("✅ Kết nối MongoDB thành công! (Sẵn sàng ghi dữ liệu)")
        
        # 3. Chọn Database
        db = client["fitness_db"]

except Exception as e:
    print(f"❌ Lỗi kết nối MongoDB: {e}")

# Hàm này để các file khác gọi lấy database ra dùng
def get_db():
    return db

# Cho phép chạy thử trực tiếp file này để test
if __name__ == "__main__":
    pass