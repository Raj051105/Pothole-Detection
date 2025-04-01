import os
from ultralytics import YOLO
import torch

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load YOLOv8 model (pretrained on COCO)
    model = YOLO('yolov8n.pt').to(device)  # 'n' (nano) is lightweight; use 's', 'm', 'l', or 'x' for larger versions

    # Function to find the next available model filename
    def get_next_model_filename(base_name="model"):
        existing_models = [f for f in os.listdir() if f.startswith(base_name) and f.endswith(".pt")]
        model_numbers = [int(f[len(base_name):-3]) for f in existing_models if f[len(base_name):-3].isdigit()]
        
        next_number = max(model_numbers) + 1 if model_numbers else 1
        return f"{base_name}{next_number}.pt"

    # Train the model
    results = model.train(data=r"pothole-dataset\data.yaml", epochs=50, imgsz=640, device=0)

    # Save the trained model with an incrementing name
    model_filename = get_next_model_filename()
    model.export(format='pt')  # Save in PyTorch format
    os.rename("runs/detect/train/weights/best.pt", model_filename)  # Rename the best model

    print(f"Model saved as: {model_filename}")
    