import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Cấu hình
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-flash-latest"

def generate_workout_plan(user_data):
    # 2. Tạo Prompt nâng cao
    system_instruction = """
    Bạn là Huấn luyện viên thể hình (PT) chuyên nghiệp và TẬN TÂM.
    Nhiệm vụ: Tạo lịch tập 7 ngày dựa trên hồ sơ cá nhân của học viên.

    QUY TẮC AN TOÀN & CÁ NHÂN HÓA (RẤT QUAN TRỌNG):
    1. TUỔI TÁC: Nếu > 40 tuổi, ưu tiên khởi động kỹ, cường độ vừa phải, bảo vệ khớp.
    2. TRÌNH ĐỘ: 
       - "Mới tập": Tập trung vào bài cơ bản (Machine, Dumbbell), hướng dẫn kỹ thuật, ít Sets.
       - "Lâu năm": Có thể dùng Free Weight (Barbell), kỹ thuật nâng cao (Superset, Dropset).
    3. CHẤN THƯƠNG: Kiểm tra kỹ trường "health_condition".
       - Ví dụ: Đau gối -> Bỏ Squat/Lunges -> Thay bằng Leg Extension/Leg Press nhẹ.
       - Đau lưng -> Bỏ Deadlift/Bent-over Row -> Thay bằng bài có điểm tựa lưng.
    
    QUY TẮC CẤU TRÚC TUẦN (7 NGÀY):
    - Output "schedule" phải là mảng đủ 7 phần tử (Day 1 - Day 7).
    - Dựa vào `frequency` để xếp ngày tập chính.
    - Ngày nghỉ điền: "Nghỉ ngơi" hoặc "Cardio nhẹ/Giãn cơ".

    OUTPUT FORMAT (JSON ONLY):
    {
      "plan_name": "Tên lịch tập (Đặt tên nghe kêu, vd: Beginner Strength)",
      "summary": "Lời khuyên tổng quan dựa trên tuổi và tình trạng sức khỏe",
      "schedule": [
        {
          "day": 1,
          "focus": "String",
          "exercises": [ { "name": "String", "sets": "String", "reps": "String", "note": "Lưu ý kỹ thuật/An toàn" } ]
        }
      ]
    }
    """

    user_prompt = f"""
    HỒ SƠ HỌC VIÊN:
    - Tuổi: {user_data['age']} | Giới tính: {user_data['gender']}
    - Body: {user_data['height']}cm, {user_data['weight']}kg
    - Trình độ: {user_data['experience']} (Mới tập/Đã tập 1 năm/...)
    - Tình trạng sức khỏe/Chấn thương: {user_data['health_condition']}
    - Mục tiêu: {user_data['goal']}
    - Lịch tập: {user_data['frequency']} buổi/tuần
    - Nơi tập: {user_data['location']}
    
    Yêu cầu: Thiết kế lịch tập phù hợp nhất với thể trạng và tránh chấn thương cho học viên này.
    """

    print(f"💪 AI đang phân tích hồ sơ: {user_data['age']} tuổi, {user_data['experience']}, vấn đề: {user_data['health_condition']}...")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=system_instruction + "\n\n" + user_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

# --- CHẠY THỬ ---
if __name__ == "__main__":
    # Giả lập học viên trung niên, bị đau lưng
    mock_user = {
        "gender": "Nam",
        "age": 45,                  # <--- Thêm tuổi
        "weight": 80,
        "height": 175,
        "goal": "Giảm mỡ & Tăng sức khỏe tim mạch",
        "experience": "Mới tập (Sedentary)", # <--- Thêm trình độ
        "health_condition": "Thoát vị đĩa đệm nhẹ, hay đau thắt lưng", # <--- Thêm bệnh lý
        "frequency": 3,
        "location": "Phòng Gym"
    }

    result = generate_workout_plan(mock_user)

    if result:
        print("\n" + "="*50)
        print(f"🎉 KẾ HOẠCH: {result.get('plan_name')}")
        print(f"👨‍⚕️ LỜI KHUYÊN PT: {result.get('summary')}")
        print("="*50 + "\n")
        
        for day in result['schedule']:
            print(f"📅 DAY {day['day']}: {day['focus']}")
            if day['exercises']:
                for ex in day['exercises']:
                    # In ra để kiểm tra xem AI có né bài đau lưng không
                    print(f"   • {ex['name']} ({ex['sets']}x{ex['reps']}) - Note: {ex['note']}")
            else:
                print("   💤 Nghỉ ngơi")
            print("-" * 30)