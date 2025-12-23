from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- [MỚI] Import thư viện này
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from ai_engine import generate_workout_plan
from datetime import datetime

app = Flask(__name__)
CORS(app) # <--- [MỚI] Dòng này cực quan trọng: Cho phép mọi kết nối (để Javascript không bị chặn)

# ... (Các phần code bên dưới giữ nguyên không cần sửa) ...

# --- 1. API ĐĂNG KÝ (Giữ nguyên) ---
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

# --- 2. API ĐĂNG NHẬP (Giữ nguyên) ---
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

# --- 3. API TẠO LỊCH TẬP (CẬP NHẬT LOGIC MỚI) ---
@app.route('/api/create-plan', methods=['POST'])
def create_plan():
    try:
        data = request.json
        username = data.get('username')
        
        # Log debug
        name = data.get('name')
        age = data.get('age', 'N/A')
        print(f"📩 Nhận yêu cầu tạo lịch mới: {name} | User: {username}")

        # [BƯỚC 1] Hủy kích hoạt (Archive) các lịch cũ của user này
        # Để đảm bảo tại 1 thời điểm chỉ có 1 lịch là "active"
        db = get_db()
        db["workouts"].update_many(
            {"username": username, "status": "active"},
            {"$set": {"status": "archived"}}
        )

        # [BƯỚC 2] Gọi AI tạo lịch mới
        plan = generate_workout_plan(data)
        
        if not plan:
            return jsonify({"status": "error", "message": "AI không phản hồi"}), 500

        # [BƯỚC 3] Lưu lịch mới với trạng thái Active
        record = {
            "username": username, 
            "user_info": data, 
            "plan": plan,
            "created_at": datetime.now(), # Lưu giờ server
            "status": "active",           # <--- Trạng thái đang tập
            "current_day": 1,             # <--- Bắt đầu từ ngày 1
            "progress_log": []            # <--- Mảng lưu lịch sử check-in
        }
        db["workouts"].insert_one(record)

        return jsonify({"status": "success", "data": plan})
    except Exception as e:
        print(f"❌ Lỗi Server: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 4. API LẤY DASHBOARD (MỚI TINH) ---
# Dùng để kiểm tra xem user có đang tập dở lịch nào không
@app.route('/api/get-dashboard', methods=['POST'])
def get_dashboard():
    try:
        data = request.json
        username = data.get('username')
        db = get_db()
        
        # Tìm lịch đang Active
        active_plan = db.workouts.find_one(
            {"username": username, "status": "active"},
            {"_id": 0} # Ẩn ID mongo đi cho đỡ lỗi JSON
        )

        if active_plan:
            # Xử lý ngày tháng để trả về JSON không bị lỗi
            if 'created_at' in active_plan:
                active_plan['created_at'] = str(active_plan['created_at'])
            if 'progress_log' in active_plan:
                active_plan['progress_log'] = [str(d) for d in active_plan['progress_log']]

            return jsonify({"status": "has_plan", "data": active_plan})
        else:
            return jsonify({"status": "no_plan"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 5. API HOÀN THÀNH NGÀY TẬP (MỚI TINH) ---
# Dùng khi user bấm "Hoàn thành buổi tập"
@app.route('/api/complete-day', methods=['POST'])
def complete_day():
    try:
        data = request.json
        username = data.get('username')
        
        db = get_db()
        
        # Tăng current_day lên 1 và ghi log thời gian
        db.workouts.update_one(
            {"username": username, "status": "active"},
            {
                "$inc": {"current_day": 1},         # Tăng ngày hiện tại lên 1
                "$push": {"progress_log": datetime.now()} # Lưu thời điểm hoàn thành
            }
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 6. API LẤY LỊCH SỬ (CẬP NHẬT XỬ LÝ NGÀY THÁNG) ---
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

        # Convert datetime sang string để không bị lỗi JSON
        for h in history:
            if 'created_at' in h: h['created_at'] = str(h['created_at'])
            if 'progress_log' in h: h['progress_log'] = [str(d) for d in h['progress_log']]

        return jsonify({"status": "success", "data": history})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("🚀 API Python đang chạy tại http://127.0.0.1:5000")
    app.run(port=5000, debug=True)