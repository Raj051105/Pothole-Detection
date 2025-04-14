import os
import json
import subprocess
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
import imghdr

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)
VIDEOS_FILE = os.path.join(DATA_FOLDER, "videos.json")
PHOTOS_FILE = os.path.join(DATA_FOLDER, "photos.json")
DETECTIONS_FILE = os.path.join(DATA_FOLDER, "detections.json")

for file in [VIDEOS_FILE, PHOTOS_FILE, DETECTIONS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([], f)

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "heic", "webp"}

def allowed_video(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def get_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return []

def save_json(data, file):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/<path:filename>')
def serve_video(filename):
    filename = filename.replace("\\", "/")  # Replace backslashes with forward slashes
    uploads_folder = os.path.join(os.getcwd(), 'uploads')  # Define your uploads folder path
    return send_from_directory(uploads_folder, filename)

@app.route("/")
def index():
    # Load the data from JSON files
    videos = get_json(VIDEOS_FILE) or []
    photos = get_json(PHOTOS_FILE) or []
    detections = get_json(DETECTIONS_FILE) or []
    
    # Pass the data to the template
    return render_template("index.html", videos=videos, photos=photos, detections=detections)

@app.route("/videos")
def videos_page():
    return render_template("videos.html")

@app.route("/photos")
def photos_page():
    return render_template("photos.html", photos=get_json(PHOTOS_FILE))

@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file found"}), 400

    file = request.files["video"]
    title = request.form.get("title", "Untitled Video")
    location = request.form.get("location", "Unknown Location")

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_video(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"

        today = datetime.today().strftime("%Y-%m-%d")
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], today)
        os.makedirs(save_path, exist_ok=True)

        file_path = os.path.join(save_path, unique_filename)
        relative_path = os.path.join(today, unique_filename)
        file.save(file_path)

        videos = get_json(VIDEOS_FILE)
        new_video = {
            "id": len(videos) + 1,
            "title": title,
            "location": location,
            "path": relative_path,
            "uploaded": datetime.now().strftime("%B %d, %Y"),
            "status": "Processing",
            "potholes": 0,
            "coordinates": []
        }
        videos.append(new_video)
        save_json(videos, VIDEOS_FILE)

        subprocess.Popen(["python", "video_processor.py", file_path])

        return jsonify({"message": "Upload successful", "file_path": file_path}), 200

    return jsonify({"error": "Invalid file type"}), 400

@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    if "photo" not in request.files:
        return jsonify({"error": "No photo file found"}), 400

    file = request.files["photo"]
    title = request.form.get("title", "Untitled Photo")
    description = request.form.get("description", "")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_image(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"

        today = datetime.today().strftime("%Y-%m-%d")
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], today)
        os.makedirs(save_path, exist_ok=True)

        file_path = os.path.join(save_path, unique_filename)
        relative_path = os.path.join(today, unique_filename)
        file.save(file_path)

        photos = get_json(PHOTOS_FILE)
        new_photo = {
            "id": len(photos) + 1,
            "title": title,
            "description": description,
            "path": relative_path,
            "url": url_for('serve_file', filename=relative_path),
            "thumbnail_url": url_for('serve_file', filename=relative_path),
            "upload_date": datetime.now().isoformat(),
            "latitude": float(latitude) if latitude else None,
            "longitude": float(longitude) if longitude else None
        }
        photos.append(new_photo)
        save_json(photos, PHOTOS_FILE)

        return jsonify({"message": "Upload successful", "photo_id": new_photo["id"]}), 200

    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/videos", methods=["GET"])
def get_all_videos():
    return jsonify(get_json(VIDEOS_FILE))

@app.route("/api/videos/<int:video_id>", methods=["GET"])
def get_video(video_id):
    videos = get_json(VIDEOS_FILE)
    for video in videos:
        if video["id"] == video_id:
            return jsonify(video)
    return jsonify({"error": "Video not found"}), 404

@app.route("/api/photos", methods=["GET"])
def get_all_photos():
    return jsonify(get_json(PHOTOS_FILE))

@app.route("/api/photos/<int:photo_id>", methods=["GET"])
def get_photo(photo_id):
    photos = get_json(PHOTOS_FILE)
    for photo in photos:
        if photo["id"] == photo_id:
            return jsonify(photo)
    return jsonify({"error": "Photo not found"}), 404

@app.route("/api/photos/<int:photo_id>", methods=["DELETE"])
def delete_photo(photo_id):
    photos = get_json(PHOTOS_FILE)
    for i, photo in enumerate(photos):
        if photo["id"] == photo_id:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], photo["path"])
            if os.path.exists(file_path):
                os.remove(file_path)
            deleted = photos.pop(i)
            save_json(photos, PHOTOS_FILE)
            return jsonify({"message": "Photo deleted", "photo": deleted})
    return jsonify({"error": "Photo not found"}), 404

@app.route("/api/potholes", methods=["GET"])
def get_all_potholes():
    try:
        with open(DETECTIONS_FILE, "r") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
