import os
from pymongo import MongoClient
from dotenv import load_dotenv

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
        # Kết nối tới MongoDB Atlas
        client = MongoClient(uri)
        
        # Lệnh 'ping' để kiểm tra xem có thông mạng không
        client.admin.command('ping')
        
        print("✅ Kết nối MongoDB thành công! (Sẵn sàng ghi dữ liệu)")
        
        # 3. Chọn Database (Tự đặt tên là fitness_db)
        db = client["fitness_db"]

except Exception as e:
    print(f"❌ Lỗi kết nối MongoDB: {e}")

# Hàm này để các file khác gọi lấy database ra dùng
def get_db():
    return db

# Cho phép chạy thử trực tiếp file này để test
if __name__ == "__main__":
    # Nếu chạy file này mà thấy dòng ✅ là ngon
    pass