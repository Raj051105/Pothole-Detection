import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
import imghdr  # For image validation

app = Flask(__name__)

# Directory to store uploads
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure folder exists
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# File to store metadata
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)
VIDEOS_FILE = os.path.join(DATA_FOLDER, "videos.json")
PHOTOS_FILE = os.path.join(DATA_FOLDER, "photos.json")

# Initialize videos.json if it doesn't exist
if not os.path.exists(VIDEOS_FILE):
    with open(VIDEOS_FILE, 'w') as f:
        json.dump([], f)

# Initialize photos.json if it doesn't exist
if not os.path.exists(PHOTOS_FILE):
    with open(PHOTOS_FILE, 'w') as f:
        json.dump([], f)

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "heic", "webp"}

def allowed_video(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def get_videos():
    try:
        with open(VIDEOS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_videos(videos):
    with open(VIDEOS_FILE, 'w') as f:
        json.dump(videos, f, indent=4)

def get_photos():
    try:
        with open(PHOTOS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_photos(photos):
    with open(PHOTOS_FILE, 'w') as f:
        json.dump(photos, f, indent=4)

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/videos")
def videos_page():
    videos = get_videos()
    return render_template("videos.html", videos=videos)

@app.route("/photos")
def photos_page():
    photos = get_photos()
    return render_template("photos.html", photos=photos)

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
        # Create a unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        # Create a date-based folder
        today = datetime.today().strftime("%Y-%m-%d")
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], today)
        os.makedirs(save_path, exist_ok=True)
        
        file_path = os.path.join(save_path, unique_filename)
        relative_path = os.path.join(today, unique_filename)
        file.save(file_path)
        
        # Store video metadata
        videos = get_videos()
        new_video = {
            "id": len(videos) + 1,
            "title": title,
            "location": location,
            "path": relative_path,
            "uploaded": datetime.now().strftime("%B %d, %Y"),
            "status": "Processing",  # Initial status
            "potholes": 0,  # Will be updated after processing
            "coordinates": []  # Will store pothole coordinates
        }
        videos.append(new_video)
        save_videos(videos)
        
        # Here you would normally call your pothole detection model
        # For demo purposes, let's simulate processing completion after upload
        simulate_processing(new_video["id"])
        
        return jsonify({"message": "Upload successful", "file_path": file_path}), 200

    return jsonify({"error": "Invalid file type"}), 400

@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    if "photo" not in request.files:
        return jsonify({"error": "No photo file found"}), 400

    file = request.files["photo"]
    title = request.form.get("title", "Untitled Photo")
    description = request.form.get("description", "")
    
    # Get coordinates if available
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_image(file.filename):
        # Create a unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        # Create a date-based folder
        today = datetime.today().strftime("%Y-%m-%d")
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], today)
        os.makedirs(save_path, exist_ok=True)
        
        file_path = os.path.join(save_path, unique_filename)
        relative_path = os.path.join(today, unique_filename)
        file.save(file_path)
        
        # Store photo metadata
        photos = get_photos()
        new_photo = {
            "id": len(photos) + 1,
            "title": title,
            "description": description,
            "path": relative_path,
            "url": url_for('serve_file', filename=relative_path),
            "thumbnail_url": url_for('serve_file', filename=relative_path),  # Same as url for now
            "upload_date": datetime.now().isoformat(),
            "latitude": float(latitude) if latitude else None,
            "longitude": float(longitude) if longitude else None
        }
        photos.append(new_photo)
        save_photos(photos)
        
        return jsonify({"message": "Upload successful", "photo_id": new_photo["id"]}), 200

    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/videos", methods=["GET"])
def get_all_videos():
    return jsonify(get_videos())

@app.route("/api/videos/<int:video_id>", methods=["GET"])
def get_video(video_id):
    videos = get_videos()
    for video in videos:
        if video["id"] == video_id:
            return jsonify(video)
    return jsonify({"error": "Video not found"}), 404

@app.route("/api/photos", methods=["GET"])
def get_all_photos():
    return jsonify(get_photos())

@app.route("/api/photos/<int:photo_id>", methods=["GET"])
def get_photo(photo_id):
    photos = get_photos()
    for photo in photos:
        if photo["id"] == photo_id:
            return jsonify(photo)
    return jsonify({"error": "Photo not found"}), 404

@app.route("/api/photos/<int:photo_id>", methods=["DELETE"])
def delete_photo(photo_id):
    photos = get_photos()
    for i, photo in enumerate(photos):
        if photo["id"] == photo_id:
            # Delete the file if it exists
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], photo["path"])
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove from list
            deleted = photos.pop(i)
            save_photos(photos)
            return jsonify({"message": "Photo deleted", "photo": deleted})
    
    return jsonify({"error": "Photo not found"}), 404

@app.route("/api/potholes", methods=["GET"])
def get_all_potholes():
    videos = get_videos()
    all_potholes = []
    
    for video in videos:
        if video["status"] == "Complete" and video["coordinates"]:
            for coord in video["coordinates"]:
                all_potholes.append({
                    "lat": coord["lat"],
                    "lng": coord["lng"],
                    "video_id": video["id"],
                    "title": video["title"],
                    "location": video["location"]
                })
    
    # Also include pothole markers from photos with GPS data
    photos = get_photos()
    for photo in photos:
        if photo["latitude"] and photo["longitude"]:
            all_potholes.append({
                "lat": photo["latitude"],
                "lng": photo["longitude"],
                "photo_id": photo["id"],
                "title": photo["title"],
                "location": photo.get("description", "Photo location")
            })
    
    return jsonify(all_potholes)

# Function to simulate processing a video and finding potholes
def simulate_processing(video_id):
    videos = get_videos()
    
    for i, video in enumerate(videos):
        if video["id"] == video_id:
            # Simulate finding some potholes with random coordinates
            import random
            num_potholes = random.randint(3, 15)
            
            # Generate some sample coordinates around a central point
            # In a real app, these would come from your ML model
            center_lat = 51.505
            center_lng = -0.09
            
            coordinates = []
            for _ in range(num_potholes):
                lat_offset = random.uniform(-0.02, 0.02)
                lng_offset = random.uniform(-0.02, 0.02)
                coordinates.append({
                    "lat": center_lat + lat_offset,
                    "lng": center_lng + lng_offset
                })
            
            # Update the video details
            videos[i]["status"] = "Complete"
            videos[i]["potholes"] = num_potholes
            videos[i]["coordinates"] = coordinates
            
            save_videos(videos)
            break

if __name__ == "__main__":
    app.run(debug=True)