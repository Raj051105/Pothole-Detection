import cv2
import json
import random
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO

# === CONFIGURATION ===
UPLOADS_DIR = Path("uploads")
OUTPUT_DIR = Path("detected_frames")
N = 5  # Process every nth frame
CONF_THRESHOLD = 0.5
MOCK_LOCATION_RANGE = {
    "lat": (45.48, 57.52),
    "lng": (-10.11, 15.07)
}

# === Load YOLO Model ===
model = YOLO("best.pt")  # Replace with your trained model path

# === Helper to Generate Mock GPS ===
def generate_mock_coordinates():
    return {
        "lat": round(random.uniform(*MOCK_LOCATION_RANGE["lat"]), 12),
        "lng": round(random.uniform(*MOCK_LOCATION_RANGE["lng"]), 12)
    }

# === Process Videos ===
def process_video(video_file, video_id):
    cap = cv2.VideoCapture(str(video_file))
    upload_date = datetime.now()  # For now, we use the current date as upload date
    pothole_coords = []
    saved_frame_count = 0
    output_subdir = OUTPUT_DIR / video_file.stem
    output_subdir.mkdir(parents=True, exist_ok=True)

    frame_index = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % N == 0:
            result = model(frame)[0]
            boxes = result.boxes
            frame_has_pothole = False

            for box in boxes:
                if box.conf.item() >= CONF_THRESHOLD:
                    frame_has_pothole = True
                    xyxy = box.xyxy[0].tolist()
                    label = model.names[int(box.cls)]
                    # Draw bounding box
                    cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)
                    cv2.putText(frame, label, (int(xyxy[0]), int(xyxy[1]) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if frame_has_pothole:
                pothole_coords.append(generate_mock_coordinates())
                frame_path = output_subdir / f"frame_{frame_index}.jpg"
                cv2.imwrite(str(frame_path), frame)
                saved_frame_count += 1

        frame_index += 1

    cap.release()

    # Save results summary
    result_summary = {
        "id": video_id,
        "title": f"Video {video_id}",
        "location": "Mock Street",  # You can adjust this to pull from metadata if needed
        "path": str(video_file).replace("\\", "/"),
        "uploaded": upload_date.strftime("%B %d, %Y"),
        "status": "Complete",
        "potholes": saved_frame_count,
        "coordinates": pothole_coords
    }

    return result_summary

# === Main Function to Process Videos in the Uploads Directory ===
def process_videos():
    results_summary = []
    video_id = 1

    for date_folder in UPLOADS_DIR.iterdir():
        video_dir = date_folder
        if not video_dir.exists():
            continue

        for video_file in video_dir.glob("*.mp4"):
            result = process_video(video_file, video_id)
            results_summary.append(result)
            video_id += 1

    # Save to detections.json
    with open("data/detections.json", "w") as f:
        json.dump(results_summary, f, indent=4)

    print("Done! JSON saved to detections.json and frames saved in 'detected_frames'")

# Call the main processing function
if __name__ == "__main__":
    process_videos()
