import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# Directory to store uploads
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure folder exists
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file found"}), 400

    file = request.files["video"]
    
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Create a date-based folder
        today = datetime.today().strftime("%Y-%m-%d")
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], today)
        os.makedirs(save_path, exist_ok=True)  # Ensure subfolder exists

        file_path = os.path.join(save_path, filename)
        file.save(file_path)

        return jsonify({"message": "Upload successful", "file_path": file_path}), 200

    return jsonify({"error": "Invalid file type"}), 400

if __name__ == "__main__":
    app.run(debug=True)
