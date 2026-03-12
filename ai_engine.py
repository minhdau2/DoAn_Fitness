import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time
from google.api_core import exceptions
import base64
import io
from PIL import Image

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite-preview"

def generate_workout_plan(user_data):

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

    system_instruction = """
    Bạn là Huấn luyện viên thể hình chuyên nghiệp.
    Nhiệm vụ: Tạo lịch tập cho TUẦN TIẾP THEO dựa trên lịch cũ.
    
    QUY TẮC BẤT DI BẤT DỊCH (PROGRESSIVE OVERLOAD):
    1. GIỮ NGUYÊN 90% CÁC BÀI TẬP CŨ: Để người dùng thuần thục kỹ thuật.
    2. TĂNG ĐỘ KHÓ (INTENSITY): 
       - Tăng số Reps (Ví dụ: 8-10 reps -> 10-12 reps).
       - Hoặc tăng số Sets (3 sets -> 4 sets).
       - Hoặc ghi chú: "Tăng mức tạ thêm 5-10% so với tuần trước".
    3. CHỈ ĐỔI BÀI TẬP KHI: Bài cũ gây chấn thương hoặc user yêu cầu đổi.

    OUTPUT FORMAT: Trả về JSON y hệt cấu trúc cũ.
    """


    schedule_data = []
    old_plan_name = "Gym Plan"

    if isinstance(current_plan_json, list):
        schedule_data = current_plan_json
    elif isinstance(current_plan_json, dict):
        schedule_data = current_plan_json.get('schedule', [])
        old_plan_name = current_plan_json.get('plan_name', "Gym Plan")
    
    old_schedule_str = json.dumps(schedule_data, ensure_ascii=False)

    user_prompt = f"""
    LỊCH TẬP TUẦN VỪA RỒI: {old_schedule_str}
    PHẢN HỒI: "{user_feedback}"
    Yêu cầu: Viết lịch tuần mới (Progressive Overload).
    """


    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Đang gọi AI nâng cấp (Lần {attempt + 1})...")
            
            response = client.models.generate_content(
                model=MODEL_NAME, 
                contents=system_instruction + "\n\n" + user_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            new_plan = json.loads(response.text)

            import re
            match = re.search(r'Tuần (\d+)', old_plan_name)
            if match:
                current_week = int(match.group(1))
                next_week = current_week + 1
                base_name = re.sub(r'\s*-\s*Tuần \d+', '', old_plan_name).strip()
            else:
                base_name = old_plan_name.replace("(Level Up 🔥)", "").strip()
                next_week = 2

            new_name = f"{base_name} - Tuần {next_week}"

            final_plan = {}
            
            if isinstance(new_plan, list):
                final_plan = {
                    "plan_name": new_name,
                    "schedule": new_plan,
                    "summary": f"Chào mừng bạn đến với {new_name}! Cố gắng tăng tạ nhé."
                }
            elif isinstance(new_plan, dict):
                final_plan = new_plan
                final_plan['plan_name'] = new_name
            else:
                raise ValueError("AI trả về dữ liệu không đúng định dạng")

            return final_plan 

        except Exception as e:
            print(f"⚠️ Lỗi lần {attempt + 1}: {e}")
            
            if attempt == max_retries - 1:
                print("❌ Đã thử hết số lần nhưng thất bại.")
                return None

            wait_time = (attempt + 1) * 5 
            print(f"⏳ Đang nghỉ {wait_time} giây để hồi phục...")
            time.sleep(wait_time)
def evolve_workout_plan(current_plan_json, user_feedback="Không có chấn thương, cảm thấy tốt"):
    schedule_data = []
    old_plan_name = "Gym Plan"

    if isinstance(current_plan_json, list):
        schedule_data = current_plan_json
    elif isinstance(current_plan_json, dict):
        schedule_data = current_plan_json.get('schedule', [])
        old_plan_name = current_plan_json.get('plan_name', "Gym Plan")
    
    old_schedule_str = json.dumps(schedule_data, ensure_ascii=False)

    system_instruction = """
    Bạn là Huấn luyện viên thể hình chuyên nghiệp.
    Nhiệm vụ: Tạo lịch tập cho TUẦN TIẾP THEO dựa trên lịch cũ.
    
    QUY TẮC BẤT DI BẤT DỊCH (PROGRESSIVE OVERLOAD):
    1. GIỮ NGUYÊN 90% CÁC BÀI TẬP CŨ: Để người dùng thuần thục kỹ thuật.
    2. TĂNG ĐỘ KHÓ (INTENSITY): 
       - Tăng số Reps (Ví dụ: 8-10 reps -> 10-12 reps).
       - Hoặc tăng số Sets (3 sets -> 4 sets).
       - Hoặc ghi chú: "Tăng mức tạ thêm 5-10% so với tuần trước".
    3. CHỈ ĐỔI BÀI TẬP KHI: Bài cũ gây chấn thương hoặc user yêu cầu đổi.

    QUAN TRỌNG: Chỉ trả về duy nhất chuỗi JSON thuần túy. Không được viết thêm lời dẫn, không dùng Markdown ```json.
    """

    user_prompt = f"""
    LỊCH CŨ: {old_schedule_str}
    PHẢN HỒI: "{user_feedback}"
    Yêu cầu: Viết lịch mới dưới dạng JSON.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🔄 Đang gọi Gemma 3 27B (Lần {attempt + 1})...")
            
            
            response = client.models.generate_content(
                model="gemma-3-27b-it", 
                contents=system_instruction + "\n\n" + user_prompt
            )

            raw_text = response.text
            cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            new_plan = json.loads(cleaned_text)

            import re
            match = re.search(r'Tuần (\d+)', old_plan_name)
            if match:
                current_week = int(match.group(1))
                next_week = current_week + 1
                base_name = re.sub(r'\s*-\s*Tuần \d+', '', old_plan_name).strip()
            else:
                base_name = old_plan_name.replace("(Level Up 🔥)", "").strip()
                next_week = 2

            new_name = f"{base_name} - Tuần {next_week}"

            final_plan = {}
            if isinstance(new_plan, list):
                final_plan = {
                    "plan_name": new_name,
                    "schedule": new_plan,
                    "summary": f"Tuần {next_week}: Gemma đã nâng cao cường độ cho bạn!"
                }
            elif isinstance(new_plan, dict):
                final_plan = new_plan
                final_plan['plan_name'] = new_name
            
            return final_plan

        except Exception as e:
            print(f"⚠️ Gemma lỗi (Lần {attempt + 1}): {e}")
            time.sleep(2) 
    
    return None
def generate_nutrition_plan(user_data):
    system_instruction = """
    Bạn là Chuyên gia Dinh dưỡng & Đầu bếp thể hình (Fitness Chef).
    Nhiệm vụ: Tính toán Calories/Macros và gợi ý thực đơn 1 ngày kèm CÔNG THỨC CHI TIẾT.
    
    INPUT: Tuổi, Giới tính, Chiều cao, Cân nặng, Mức độ vận động (frequency), Mục tiêu.
    
    CÔNG THỨC TÍNH:
    1. TDEE = BMR * Activity Multiplier.
    2. Target Calories = TDEE +/- (300~500) tùy mục tiêu.
    3. Macros: Protein (4cal), Carb (4cal), Fat (9cal).
    4. NƯỚC UỐNG: Khuyến nghị khoảng 40ml - 50ml cho mỗi kg trọng lượng cơ thể (Ví dụ 70kg * 40ml = 2.8 Lít), cộng thêm 500ml nếu tập luyện. Đừng khuyến nghị quá 4 lít trừ khi vận động viên chuyên nghiệp.

    OUTPUT FORMAT (JSON ONLY - Cấm markdown, Cấm chú thích thêm):
    {
      "calories": 2500,
      "macros": { "protein": "180g", "carbs": "250g", "fats": "70g" },
      "advice": "Lời khuyên ngắn...",
      "menu": [
        { 
          "meal": "Bữa sáng", 
          "dish": "Phở bò ít béo", 
          "calories": "500 kcal",
          "ingredients": [ "150g Bánh phở", "100g Thịt bò thăn", "Hành tây, gừng, quế" ],
          "recipe": "1. Chần bánh phở qua nước sôi.\\n2. Thịt bò thái mỏng, chần tái.\\n3. Chan nước dùng ninh từ xương (đã vớt bọt béo)."
        },
        ... (Tiếp tục các bữa khác)
      ]
    }
    """

    user_prompt = f"""
    HỒ SƠ:
    - {user_data['age']} tuổi, {user_data['gender']}
    - {user_data['height']}cm, {user_data['weight']}kg
    - Tần suất tập: {user_data['frequency']} buổi/tuần
    - Mục tiêu: {user_data['goal']}
    
    Yêu cầu: Lên thực đơn món Việt dễ nấu, kèm công thức chi tiết.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=system_instruction + "\n\n" + user_prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Lỗi Nutrition: {e}")
        return None

def consult_nutritionist(current_plan, user_question):
    system_instruction = """
    Bạn là Chuyên gia dinh dưỡng riêng. Bạn đang nắm giữ thực đơn của khách hàng.
    Nhiệm vụ: Trả lời ngắn gọn, thân thiện các yêu cầu thay đổi món ăn hoặc tư vấn của khách.
    
    LƯU Ý:
    - Nếu khách muốn đổi món, hãy gợi ý món mới có Calories/Macros tương đương.
    - Trả lời ngắn gọn (dưới 3 câu), đi thẳng vào vấn đề.
    - Giọng điệu: Vui vẻ, khuyến khích (kiểu PT chuyên nghiệp).
    """

    menu_context = json.dumps(current_plan.get('menu', []), ensure_ascii=False)
    
    user_prompt = f"""
    THỰC ĐƠN HIỆN TẠI CỦA TÔI:
    {menu_context}

    CÂU HỎI CỦA TÔI:
    "{user_question}"
    
    Hãy tư vấn hoặc đổi món giúp tôi.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=system_instruction + "\n\n" + user_prompt
        )
        return response.text
    except Exception as e:
        return "Xin lỗi, hiện tại tôi đang bận. Bạn hỏi lại sau nhé!"
def review_meal_text(user_input):
    """Phân tích bữa ăn phạm quy qua mô tả văn bản"""
    system_instruction = """
    Bạn là chuyên gia dinh dưỡng AI. 
    Nhiệm vụ: Phân tích bữa ăn "phạm quy" của người dùng, ước tính calo và gợi ý bữa tối bù lại.
    
    YÊU CẦU OUTPUT JSON thuần túy (Không viết lời dẫn, không ```json):
    {
        "estimated_calories": "Con số ước tính (kcal)",
        "analysis": "Phân tích nhanh về món đã ăn",
        "compensate_dinner": "Gợi ý bữa tối cụ thể để bù đắp",
        "expert_advice": "Lời khuyên ngắn gọn"
    }
    """

    try:
        # Sử dụng Gemma 3 27B để có 14.4K lượt dùng mỗi ngày
        response = client.models.generate_content(
            model="gemma-3-27b-it", 
            contents=system_instruction + "\n\nNgười dùng nói: " + user_input
        )
        
        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Lỗi Review Văn Bản: {e}")
        return None

# --- 2. HÀM REVIEW BỮA ĂN QUA HÌNH ẢNH/CAMERA (Dùng Gemma 3 27B Vision) ---
def review_meal_vision(image_base64, user_note=""):
    """Nhận diện món ăn qua ảnh và tính toán calo"""
    system_instruction = """
    Bạn là Chuyên gia Dinh dưỡng và Ẩm thực Việt Nam hàng đầu, sở hữu khả năng thị giác máy tính (Computer Vision) xuất sắc.
    Nhiệm vụ của bạn là nhận diện chính xác món ăn qua ảnh, đánh giá khẩu phần, ước tính lượng Calo/Macros và gợi ý cách bù đắp dinh dưỡng.

    🚨 QUY TẮC NHẬN DIỆN MÓN ĂN VIỆT NAM (BẮT BUỘC ÁP DỤNG):
    1. PHÂN TÍCH NƯỚC DÙNG (BROTH): 
       - Trong vắt hoặc hơi đục nhẹ: Thường là Hủ tiếu, Bún mọc, Bún nước lèo, Phở.
       - Đỏ cam/Có váng mỡ: Thường là Bún bò Huế, Bún riêu. (TUYỆT ĐỐI KHÔNG đoán "Bún riêu" nếu không thấy rõ tảng gạch cua và nước màu cà chua).
       - Nâu sẫm/Đục đặc: Thường là Bún mắm.
    2. PHÂN TÍCH SỢI VÀ TOPPING:
       - Sợi bún trắng nhỏ + Thịt heo luộc/Heo quay/Cá/Tôm + Hành phi/Tỏi phi vàng trên mặt: Đây là đặc trưng của các loại Bún miền Tây như "Bún nước lèo", "Bún cá". Rất dễ nhầm tỏi phi/hành phi với gạch cua, hãy nhìn thật kỹ.
    3. ƯU TIÊN GHI CHÚ CỦA NGƯỜI DÙNG (TỐI QUAN TRỌNG):
       - NẾU người dùng có cung cấp "Ghi chú" (ví dụ họ ghi sẵn tên món), BẠN PHẢI TIN TƯỞNG 100% VÀO TÊN ĐÓ. 
       - Khi đó, chỉ dùng hình ảnh để đánh giá KHẨU PHẦN (tô lớn/nhỏ, nhiều bún hay ít bún, nhiều mỡ hay thịt nạc) để tính toán Calo chính xác, tuyệt đối không tự ý đổi tên món thành món khác.

    YÊU CẦU ĐẦU RA (OUTPUT):
    - TRẢ VỀ DUY NHẤT CHUỖI JSON HỢP LỆ.
    - KHÔNG sử dụng markdown (không có ```json hay ``` ở đầu/cuối).
    - KHÔNG thêm bất kỳ lời giải thích nào bên ngoài JSON.

    ĐỊNH DẠNG JSON CHUẨN:
    {
        "dish_name": "Tên món ăn (Càng chi tiết càng tốt, vd: Bún nước lèo Sóc Trăng cỡ vừa)",
        "estimated_calories": "Chỉ chứa con số (vd: 450)",
        "analysis": "Phân tích 1-2 câu về tỉ lệ dinh dưỡng trong ảnh. (vd: Tô này có khá nhiều tinh bột từ bún, nạp đủ protein từ thịt luộc, nhưng chú ý lượng chất béo từ tỏi phi dính trên mặt).",
        "compensate_dinner": "Gợi ý 1 bữa tối cụ thể, nhẹ bụng để bù lại năng lượng.",
        "expert_advice": "1 câu lời khuyên thiết thực (vd: Lần sau nên xin thêm rau trụng và giảm đi một nửa lượng bún để giảm tinh bột)."
    }
    """

    try:
        # Giải mã ảnh từ Base64 do phía PHP/JS gửi lên
        image_data = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(image_data))

        # Gemma 3 27B hỗ trợ đa phương thức (hình ảnh + văn bản)
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=[system_instruction + "\nGhi chú thêm: " + user_note, img]
        )
        
        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Lỗi Vision AI: {e}")
        return None
def evaluate_workout_form(exercise_name, total_reps, bad_reps):
    """Phân tích tư thế tập luyện bằng Gemma 3 27B"""
    system_instruction = f"""
    Bạn là Huấn luyện viên thể hình ảo cực kỳ chuyên nghiệp và nghiêm khắc.
    Học viên của bạn vừa kết thúc bài tập: {exercise_name}.
    
    QUY TẮC NHẬN XÉT (Ngắn gọn tối đa 3 câu):
    - Nếu tổng số rep (total_reps) = 0: Trách móc nhẹ nhàng vì bật máy lên mà không tập.
    - Nếu bad_reps = 0: Khen ngợi nhiệt tình vì chuẩn form.
    - Nếu bad_reps > 0: 
      + Với bài Squat: Nhắc nhở ngồi xuống sâu hơn (gập gối dưới 90 độ), giữ lưng thẳng.
      + Với bài Push-up (Hít đất): Nhắc nhở gập sâu cùi chỏ và gồng chặt cơ bụng để không võng lưng.
    
    CHỈ TRẢ VỀ TEXT BÌNH THƯỜNG, ĐÓNG VAI PT ĐỂ NÓI CHUYỆN (Tuyệt đối không dùng JSON, không giải thích).
    """
    
    user_prompt = f"Tôi vừa tập xong. Tổng số rep: {total_reps}. Số rep bị máy quét báo lỗi kỹ thuật: {bad_reps}."
    
    try:
        print(f"🔄 Đang gọi Gemma 3 27B để nhận xét bài {exercise_name}...")
        # Đổi sang Gemma 3 27B để xài tẹt ga 14.4K Quota
        response = client.models.generate_content(
            model="gemma-3-27b-it", 
            contents=system_instruction + "\n\n" + user_prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi AI Tracker: {e}")
        return "Tập tốt lắm! Nhưng máy chủ AI đang bận chút, bạn nghỉ ngơi uống nước đi nhé!"
def generate_exercise_rule(exercise_name):
    """Dùng Gemma 3 27B để tự động sinh quy tắc đo góc cho bài tập mới"""
    
    system_instruction = """
    Bạn là một Chuyên gia Sinh cơ học (Biomechanics) và Lập trình viên Computer Vision.
    Nhiệm vụ: Tạo quy tắc đo góc (Rule) cho thư viện Google Mediapipe Pose (33 điểm).

    TỪ ĐIỂN XƯƠNG KHỚP CƠ BẢN (Dùng bên trái cho chuẩn):
    - Tay & Vai: 11 (Vai trái), 13 (Cùi chỏ trái), 15 (Cổ tay trái)
    - Thân & Chân: 23 (Hông trái), 25 (Đầu gối trái), 27 (Cổ chân trái)
    
    HƯỚNG DẪN TƯ DUY CHO AI:
    1. Xác định bài tập người dùng yêu cầu chuyển động khớp nào là chính.
    2. Chọn 3 điểm tạo thành góc đó (Ví dụ Gập gối thì lấy Hông 23 - Gối 25 - Cổ chân 27).
    3. Ước tính góc mở tối đa (angleUp - lúc giãn cơ) và góc gập tối thiểu (angleDown - lúc thắt cơ).
    
    CHỈ TRẢ VỀ JSON THUẦN TÚY KHÔNG CÓ MARKDOWN:
    {
        "exercise": "Tên bài tập bằng tiếng Anh",
        "joints": [Điểm A, Điểm B, Điểm C],
        "angleUp": 160,
        "angleDown": 90,
        "msgUp": "Câu khẩu lệnh khi góc lớn (VD: Đứng thẳng / Thả tay)",
        "msgDown": "Câu khẩu lệnh khi gập (VD: Đạt chuẩn / Tốt lắm)"
    }
    """
    
    try:
        print(f"🧠 AI đang phân tích sinh cơ học cho bài tập: {exercise_name}...")
        response = client.models.generate_content(
            model="gemma-3-27b-it", 
            contents=system_instruction + f"\n\nHãy tạo quy tắc cho bài tập: {exercise_name}"
        )
        
        # Làm sạch chuỗi JSON
        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Lỗi tạo luật: {e}")
        return None
if __name__ == "__main__":
    mock_user = {
        "gender": "Nam",
        "age": 45,                  
        "weight": 80,
        "height": 175,
        "goal": "Giảm mỡ & Tăng sức khỏe tim mạch",
        "experience": "Mới tập (Sedentary)", 
        "health_condition": "Thoát vị đĩa đệm nhẹ, hay đau thắt lưng", 
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
                    
                    print(f"   • {ex['name']} ({ex['sets']}x{ex['reps']}) - Note: {ex['note']}")
            else:
                print("   💤 Nghỉ ngơi")
            print("-" * 30)
