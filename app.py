from flask import Flask, render_template, jsonify, request
import os
import pandas as pd

app = Flask(__name__)

IMAGE_FOLDER = "static/images"
RESULTS_FOLDER = "results"  # 存放所有 results_<UserID>.xlsx 文件

# 確保存放結果的目錄存在
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

# 確保圖片目錄存在
folders = ["static/images/ref", "static/images/p0", "static/images/p1"]
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/images")
def get_images():
    """獲取圖片列表"""
    ref_dir = os.path.join(IMAGE_FOLDER, "ref")

    if not os.path.exists(ref_dir):
        return jsonify({"images": []})

    image_names = [f for f in os.listdir(ref_dir) if f.endswith((".jpg", ".png"))]

    images = [
        {
            "ref": f"/static/images/ref/{img}",
            "p0": f"/static/images/p0/{img}",
            "p1": f"/static/images/p1/{img}",
        }
        for img in image_names
    ]
    return jsonify({"images": images})


@app.route("/api/load_user", methods=["POST"])
def load_user():
    """根據用戶 ID 加載已保存的選擇數據"""
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "請提供用戶 ID！"}), 400

    user_file = os.path.join(RESULTS_FOLDER, f"results_{user_id}.xlsx")

    if os.path.exists(user_file):
        df = pd.read_excel(user_file, engine="openpyxl")
        saved_choices = {row["圖片名稱"]: "p0" if row["選擇結果"] == 0 else "p1" for _, row in df.iterrows()}
        return jsonify({"status": "success", "message": "已加載用戶數據！", "saved_choices": saved_choices})

    return jsonify({"status": "success", "message": "新用戶，開始新的問卷！", "saved_choices": {}})


@app.route("/api/submit", methods=["POST"])
def submit():
    """接收使用者的選擇並存入對應的 Excel 文件"""
    data = request.json
    user_id = data.get("user_id")  # 從請求數據中獲取用戶 ID

    if not user_id:
        return jsonify({"status": "error", "message": "請提供用戶 ID！"})

    user_file = os.path.join(RESULTS_FOLDER, f"results_{user_id}.xlsx")

    # 轉換 p0 為 0，p1 為 1
    records = [
        {
            "用戶 ID": user_id,
            "圖片名稱": os.path.basename(img),
            "選擇結果": 0 if choice == "p0" else 1,  # p0 -> 0, p1 -> 1
            "提交時間": pd.Timestamp.now()
        }
        for img, choice in data["selections"].items()
    ]
    df = pd.DataFrame(records)

    try:
        # 嘗試讀取現有 Excel，然後合併數據，避免重複記錄
        if os.path.exists(user_file):
            existing_df = pd.read_excel(user_file, engine="openpyxl")
            df = pd.concat([existing_df, df]).drop_duplicates(subset=["圖片名稱"], keep="last")
    except Exception as e:
        print(f"讀取 Excel 發生錯誤: {e}")

    # 儲存到 Excel
    df.to_excel(user_file, index=False, engine="openpyxl")

    return jsonify(
        {"status": "success", "message": f"問卷提交成功，數據已存入 results_{user_id}.xlsx！", "user_id": user_id})


if __name__ == "__main__":
    app.run(debug=True, port=5000)