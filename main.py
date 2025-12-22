import datetime
from ai_engine import generate_workout_plan  # Lấy hàm từ file AI
from database import get_db                  # Lấy hàm từ file Database

def main():
    # 1. Giả lập thông tin người dùng nhập từ Web/App
    print("--- 🏋️ BẮT ĐẦU TẠO LỊCH TẬP MỚI ---")
    user_input = {
        "name": "Minh Developer",   # Tên người tập
        "gender": "Nam",
        "weight": 68,
        "height": 172,
        "goal": "Tăng cơ, giảm mỡ",
        "frequency": 4,
        "location": "Phòng Gym",
        "created_at": datetime.datetime.now() # Lưu thời gian tạo
    }

    # 2. Gọi AI để tạo lịch (Bước này mất khoảng 5-10 giây)
    print("🤖 Đang nhờ AI thiết kế lịch trình... (Vui lòng đợi)")
    workout_plan = generate_workout_plan(user_input)

    if not workout_plan:
        print("❌ AI gặp lỗi, không tạo được lịch!")
        return

    # 3. Kết nối Database để lưu
    db = get_db()
    if db is None:
        print("❌ Lỗi kết nối Database!")
        return

    # 4. Ghép thông tin user vào lịch tập để lưu chung
    # (Tạo một bản ghi đầy đủ gồm cả Info + Lịch tập)
    full_record = {
        "user_info": user_input,
        "plan": workout_plan
    }

    try:
        # Lưu vào Collection tên là "workouts"
        collection = db["workouts"]
        result = collection.insert_one(full_record)
        
        print("\n" + "="*40)
        print(f"✅ LƯU THÀNH CÔNG! ID của lịch tập: {result.inserted_id}")
        print("="*40)
        print("💡 Bạn có thể lên trang MongoDB Atlas để kiểm tra dữ liệu vừa vào.")
        
    except Exception as e:
        print(f"❌ Lỗi khi lưu: {e}")

# Chạy chương trình
if __name__ == "__main__":
    main()