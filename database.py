import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi 

load_dotenv()
uri = os.getenv("MONGO_URI")

db = None

try:
    if not uri:
        print("❌ LỖI: Chưa tìm thấy 'MONGO_URI' trong file .env")
    else:

        try:
            ca = certifi.where()
            client = MongoClient(uri, tlsCAFile=ca)
        except:
            print("⚠️ Đang dùng chế độ kết nối không kiểm tra SSL (Debug Mode)...")
            client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
        
        client.admin.command('ping')
        
        print("✅ Kết nối MongoDB thành công! (Sẵn sàng ghi dữ liệu)")

        db = client["fitness_db"]

except Exception as e:
    print(f"❌ Lỗi kết nối MongoDB: {e}")

def get_db():
    return db

if __name__ == "__main__":
    pass