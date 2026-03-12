from flask import Flask, request, jsonify
from flask_cors import CORS  
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash

from ai_engine import evaluate_workout_form, generate_exercise_rule, generate_workout_plan, generate_nutrition_plan, consult_nutritionist, client, evolve_workout_plan,review_meal_text, review_meal_vision
from datetime import datetime

app = Flask(__name__)
CORS(app) 

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    fullname = data.get('fullname')

    db = get_db()
    users = db['users']

    if users.find_one({"username": username}):
        return jsonify({"status": "error", "message": "Tên đăng nhập đã tồn tại!"}), 400

    hashed_password = generate_password_hash(password)

    new_user = {
        "username": username,
        "password": hashed_password,
        "fullname": fullname
    }
    
    users.insert_one(new_user)
    
    return jsonify({
        "status": "success", 
        "message": "Đăng ký thành công!",
        "user": {
            "username": username,
            "fullname": fullname
        }
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    db = get_db()
    user = db['users'].find_one({"username": username})

    if not user:
        return jsonify({"status": "error", "message": "Sai tên đăng nhập!"}), 401

    if check_password_hash(user['password'], password):
        return jsonify({
            "status": "success", 
            "user": {
                "username": user['username'],
                "fullname": user['fullname']
            }
        })
    else:
        return jsonify({"status": "error", "message": "Sai mật khẩu!"}), 401

@app.route('/api/create-plan', methods=['POST'])
def create_plan():
    try:
        data = request.json
        username = data.get('username')

        name = data.get('name')
        age = data.get('age', 'N/A')
        print(f"📩 Nhận yêu cầu tạo lịch mới: {name} | User: {username}")

        db = get_db()
        db["workouts"].update_many(
            {"username": username, "status": "active"},
            {"$set": {"status": "archived"}}
        )

        plan = generate_workout_plan(data)
        
        if not plan:
            return jsonify({"status": "error", "message": "AI không phản hồi"}), 500

        record = {
            "username": username, 
            "user_info": data, 
            "plan": plan,
            "created_at": datetime.now(), 
            "status": "active",           
            "current_day": 1,             
            "progress_log": []            
        }
        db["workouts"].insert_one(record)

        return jsonify({"status": "success", "data": plan})
    except Exception as e:
        print(f"❌ Lỗi Server: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/evolve-plan', methods=['POST'])
def evolve_plan():
    try:
        data = request.json
        username = data.get('username')
        
        db = get_db()
        last_plan = db.workouts.find_one(
            {"username": username},
            sort=[("created_at", -1)] 
        )

        if not last_plan:
            return jsonify({"status": "error", "message": "Không tìm thấy lịch cũ"}), 404

        print(f"💪 Đang nâng cấp lịch cho: {username}...")
        new_plan_content = evolve_workout_plan(last_plan['plan'])
        
        if not new_plan_content:
            return jsonify({"status": "error", "message": "AI không phản hồi"}), 500


        db.workouts.update_many(
            {"username": username, "status": "active"},
            {"$set": {"status": "archived"}}
        )

        new_record = {
            "username": username, 
            "user_info": last_plan.get('user_info'), 
            "plan": new_plan_content,
            "created_at": datetime.now(),
            "status": "active",
            "current_day": 1,
            "progress_log": []
        }
        db.workouts.insert_one(new_record)

        return jsonify({"status": "success", "message": "Đã nâng cấp lịch tập!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get-dashboard', methods=['POST'])
def get_dashboard():
    try:
        data = request.json
        username = data.get('username')
        db = get_db()

        active_plan = db.workouts.find_one(
            {"username": username, "status": "active"},
            {"_id": 0} 
        )

        if active_plan:
            if 'created_at' in active_plan:
                active_plan['created_at'] = str(active_plan['created_at'])
            if 'progress_log' in active_plan:
                active_plan['progress_log'] = [str(d) for d in active_plan['progress_log']]

            return jsonify({"status": "has_plan", "data": active_plan})
        else:
            return jsonify({"status": "no_plan"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/complete-day', methods=['POST'])
def complete_day():
    try:
        data = request.json
        username = data.get('username')
        logs = data.get('logs', []) 
        
        db = get_db()

        log_entry = {
            "date": str(datetime.now()),
            "exercises": logs 
        }

        db.workouts.update_one(
            {"username": username, "status": "active"},
            {
                "$inc": {"current_day": 1},
                "$push": {
                    "progress_log": str(datetime.now()), 
                    "exercise_history": log_entry        
                }
            }
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get-history', methods=['POST'])
def get_history():
    try:
        data = request.json
        username = data.get('username')

        db = get_db()
        history = list(db.workouts.find(
            {"username": username}, 
            {"_id": 0} 
        ).sort("created_at", -1))

        for h in history:
            if 'created_at' in h: h['created_at'] = str(h['created_at'])
            if 'progress_log' in h: h['progress_log'] = [str(d) for d in h['progress_log']]

        return jsonify({"status": "success", "data": history})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/api/nutrition', methods=['POST'])
def get_nutrition():
    try:
        data = request.json
        username = data.get('username')
        db = get_db()

        active_plan = db.workouts.find_one({"username": username, "status": "active"})
        
        if not active_plan:
            return jsonify({"status": "error", "message": "Bạn cần tạo Lịch tập trước!"}), 400

        if "nutrition_plan" in active_plan:
            return jsonify({"status": "success", "data": active_plan["nutrition_plan"]})

        user_info = active_plan['user_info']
        print(f"🥦 Đang tính toán dinh dưỡng cho: {username}...")
        
        nutrition_data = generate_nutrition_plan(user_info)
        
        if not nutrition_data:
            return jsonify({"status": "error", "message": "AI Dinh dưỡng không phản hồi"}), 500

        db.workouts.update_one(
            {"_id": active_plan["_id"]},
            {"$set": {"nutrition_plan": nutrition_data}}
        )

        return jsonify({"status": "success", "data": nutrition_data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/review-meal', methods=['POST'])
def api_review_meal():
    try:
        data = request.json
        content = data.get('content')
        
        print(f"🥗 Đang phân tích bữa ăn qua văn bản: {content}")
        result = review_meal_text(content)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "AI không phản hồi"}), 500
    except Exception as e:
        print(f"❌ LỖI SERVER: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/review-meal-vision', methods=['POST'])
def api_review_meal_vision():
    try:
        data = request.json
        image_base64 = data.get('image')
        note = data.get('note', '')
        
        print(f"📸 Đang phân tích bữa ăn qua CAMERA (Vision)...")
        result = review_meal_vision(image_base64, note)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "AI không thể phân tích ảnh"}), 500
    except Exception as e:
        print(f"❌ LỖI SERVER: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/nutrition-chat', methods=['POST'])
def nutrition_chat():
    try:
        data = request.json
        username = data.get('username')
        message = data.get('message')
        
        db = get_db()

        active_plan = db.workouts.find_one({"username": username, "status": "active"})
        
        if not active_plan or "nutrition_plan" not in active_plan:
            return jsonify({"status": "error", "reply": "Bạn cần tạo thực đơn trước khi hỏi nhé!"})

        current_nutrition = active_plan["nutrition_plan"]
        ai_reply = consult_nutritionist(current_nutrition, message)

        chat_entry = [
            {"role": "user", "content": message, "time": str(datetime.now())},
            {"role": "ai", "content": ai_reply, "time": str(datetime.now())}
        ]

        db.workouts.update_one(
            {"_id": active_plan["_id"]},
            {"$push": {"nutrition_chat_history": {"$each": chat_entry}}}
        )
        
        return jsonify({"status": "success", "reply": ai_reply})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/get-nutrition-chat', methods=['POST'])
def get_nutrition_chat_history():
    try:
        data = request.json
        username = data.get('username')
        db = get_db()
        
        active_plan = db.workouts.find_one({"username": username, "status": "active"})
        
        history = []
        if active_plan and "nutrition_chat_history" in active_plan:
            history = active_plan["nutrition_chat_history"]
            
        return jsonify({"status": "success", "data": history})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/workout-chat', methods=['POST'])
def workout_chat():
    try:
        data = request.json
        username = data.get('username')
        message = data.get('message')
        
        db = get_db()
        active_plan = db.workouts.find_one({"username": username, "status": "active"})
        
        if not active_plan:
            return jsonify({"status": "error", "reply": "Bạn chưa có lịch tập nào cả!"})

        plan_info = active_plan.get('plan', {})
        current_day = active_plan.get('current_day', 1)

        today_schedule = "Nghỉ ngơi"
        if 'schedule' in plan_info:
            for day in plan_info['schedule']:
                if day.get('day') == current_day:
                    today_schedule = str(day)
                    break

        system_instruction = f"""
        Bạn là Huấn luyện viên thể hình AI (AI Fitness Coach).
        Người dùng đang tập giáo án: {plan_info.get('plan_name')}
        Hôm nay là ngày thứ: {current_day}
        Bài tập hôm nay: {today_schedule}
        
        Nhiệm vụ: Trả lời ngắn gọn, chuyên nghiệp về kỹ thuật tập, chấn thương, hoặc thay đổi bài tập.
        """

        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=system_instruction + "\n\nUser hỏi: " + message,
            )
            ai_reply = response.text
            
        except Exception as e:
            print(f"❌ LỖI GEMINI: {str(e)}")

            ai_reply = f"Lỗi kết nối AI: {str(e)}"

        chat_entry = [
            {"role": "user", "content": message, "time": str(datetime.now())},
            {"role": "ai", "content": ai_reply, "time": str(datetime.now())}
        ]
        
        db.workouts.update_one(
            {"_id": active_plan["_id"]},
            {"$push": {"workout_chat_history": {"$each": chat_entry}}}
        )
        
        return jsonify({"status": "success", "reply": ai_reply})

    except Exception as e:
        print(f"❌ LỖI SERVER: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get-workout-chat', methods=['POST'])
def get_workout_chat_history():
    try:
        data = request.json
        username = data.get('username')
        db = get_db()
        active_plan = db.workouts.find_one({"username": username, "status": "active"})
        
        history = []
        if active_plan and "workout_chat_history" in active_plan:
            history = active_plan["workout_chat_history"]
            
        return jsonify({"status": "success", "data": history})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/api/evaluate-tracker', methods=['POST'])
def api_evaluate_tracker():
    try:
        data = request.json
        exercise_name = data.get('exercise_name', 'Squat')
        total_reps = data.get('total_reps', 0)
        bad_reps = data.get('bad_reps', 0)
        
        print(f"🏋️ AI Tracker: Nhận báo cáo {exercise_name} | Tổng: {total_reps} | Lỗi: {bad_reps}")
        
        advice = evaluate_workout_form(exercise_name, total_reps, bad_reps)
        return jsonify({"status": "success", "advice": advice})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/api/admin/generate-rule', methods=['POST'])
def api_generate_rule():
    try:
        data = request.json
        exercise_name = data.get('exercise_name')
        
        if not exercise_name:
            return jsonify({"status": "error", "message": "Thiếu tên bài tập"}), 400
            
        rule = generate_exercise_rule(exercise_name)
        
        if rule:
            return jsonify({"status": "success", "data": rule})
        else:
            return jsonify({"status": "error", "message": "AI không thể sinh luật"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# --- API LƯU BÀI TẬP TỪ ADMIN ---
@app.route('/api/admin/save-rule', methods=['POST'])
def api_save_rule():
    try:
        new_rule = request.json
        db = get_db()
        
        # Cập nhật nếu đã có (dựa vào tên bài tập), hoặc tạo mới nếu chưa có (upsert=True)
        db.exercises.update_one(
            {"exercise": new_rule.get("exercise")},
            {"$set": new_rule},
            upsert=True
        )
        return jsonify({"status": "success", "message": "Đã lưu bài tập vào Database!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- API LẤY DANH SÁCH BÀI TẬP CHO TRANG TRACKER ---
@app.route('/api/get-exercises', methods=['GET'])
def api_get_exercises():
    try:
        db = get_db()
        # Lấy tất cả bài tập, bỏ cột _id của Mongo đi
        exercises = list(db.exercises.find({}, {"_id": 0}))
        
        # Nếu DB trống, trả về 2 bài mặc định để app không bị lỗi
        if not exercises:
            exercises = [
                {
                    "exercise": "Squat", "joints": [23, 25, 27], 
                    "angleUp": 160, "angleDown": 90, 
                    "msgUp": "ĐỨNG THẲNG", "msgDown": "SQUAT ĐẠT!"
                },
                {
                    "exercise": "Push-up", "joints": [11, 13, 15], 
                    "angleUp": 160, "angleDown": 90, 
                    "msgUp": "CHỐNG THẲNG TAY", "msgDown": "HÍT ĐẠT!"
                }
            ]
        return jsonify({"status": "success", "data": exercises})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
if __name__ == '__main__':
    print("🚀 API Python đang chạy tại http://127.0.0.1:5000")
    app.run(port=5000, debug=True)