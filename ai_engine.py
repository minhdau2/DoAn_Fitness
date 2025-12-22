import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Cấu hình kết nối
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Khởi tạo Client
client = genai.Client(api_key=API_KEY)

# Tên model "chân ái" của bạn
MODEL_NAME = "gemini-flash-latest" 

def generate_workout_plan(user_data):
    """
    Hàm này nhận thông tin người dùng (user_data) 
    và trả về lịch tập dạng JSON.
    """
    
    # 2. Tạo Prompt (Kịch bản cho AI)
    # Phần System: Ép AI đóng vai PT và trả về đúng định dạng JSON
    system_instruction = """
    Bạn là Huấn luyện viên thể hình (PT) chuyên nghiệp.
    Nhiệm vụ: Tạo lịch tập dựa trên thông tin người dùng cung cấp.
    QUY TẮC CHUYÊN MÔN (BẮT BUỘC):
    1. Nếu chia lịch Upper/Lower (4 buổi): Ngày Upper phải tập TOÀN BỘ thân trên (cả Ngực, Lưng, Vai, Tay). Tiêu đề ngày tập phải ghi đúng các nhóm cơ này.
    2. Nếu chia lịch Push/Pull/Legs (6 buổi): Mới được tách riêng Ngực/Vai/Tay Sau.
    3. Đảm bảo cân bằng giữa bài Đẩy (Push) và Kéo (Pull) để tránh lệch cơ.

    YÊU CẦU BẮT BUỘC:
    1. Output phải là chuẩn JSON. Không được có markdown (```json).
    2. Cấu trúc JSON phải gồm:
       - "plan_name": Tên lịch tập (String)
       - "summary": Nhận xét tổng quan (String)
       - "schedule": Danh sách các ngày tập (Array). Mỗi ngày gồm:
            + "day": Số ngày (Int)
            + "focus": Nhóm cơ tập trung (String)
            + "exercises": Danh sách bài tập (Array). Mỗi bài gồm: "name", "sets", "reps", "note".
    3. Ngôn ngữ: Tiếng Việt.
    """

    # Phần User: Dữ liệu thật từ người dùng
    user_prompt = f"""
    Thông tin học viên:
    - Giới tính: {user_data['gender']}
    - Cân nặng: {user_data['weight']}kg, Chiều cao: {user_data['height']}cm
    - Mục tiêu: {user_data['goal']}
    - Số buổi tập/tuần: {user_data['frequency']}
    - Nơi tập: {user_data['location']}
    """

    print(f"💪 AI đang suy nghĩ lịch tập cho {user_data['gender']}, {user_data['goal']}...")

    try:
        # 3. Gọi Gemini với cấu hình trả về JSON
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=system_instruction + "\n\n" + user_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json" # <-- Ép trả về JSON
            )
        )
        
        # 4. Xử lý kết quả
        # Lấy text ra và chuyển thành Dictionary (Object) của Python
        plan_json = json.loads(response.text)
        return plan_json

    except Exception as e:
        print(f"❌ Lỗi khi gọi AI: {e}")
        return None

# --- PHẦN CHẠY THỬ (TEST) ---
# Khi nào chạy file này trực tiếp thì nó mới chạy đoạn dưới
if __name__ == "__main__":
    # Giả lập 1 người dùng nhập liệu từ Web
    mock_user = {
        "gender": "Nam",
        "weight": 74,
        "height": 180,
        "goal": "Tăng cơ bắp (Hypertrophy)",
        "frequency": 5, 
        "location": "Phòng Gym (Có đầy đủ máy)"
    }

    # Gọi hàm
    result = generate_workout_plan(mock_user)

    if result:
        print("\n=== 🎉 KẾT QUẢ AI TRẢ VỀ (Đã xử lý) ===")
        print(f"📌 Tên lịch: {result.get('plan_name')}")
        print(f"📝 Nhận xét: {result.get('summary')}")
        print("-" * 30)
        
        # In thử lịch ngày đầu tiên
        first_day = result['schedule'][0]
        print(f"📅 Ngày {first_day['day']}: {first_day['focus']}")
        for ex in first_day['exercises']:
            print(f"   - {ex['name']} | {ex['sets']} sets x {ex['reps']}")
        
        print("-" * 30)
        print("✅ Dữ liệu này đã sẵn sàng để lưu vào Database!")