from ultralytics import YOLO
import os

model = YOLO(r"C:\\Ml projects\\Pothole\\Pothole-Detection\\best.pt")  

results = model([
    r"C:\\Ml projects\\Pothole\\Pothole-Detection\\image1.jpeg",
    r"C:\\Ml projects\\Pothole\\Pothole-Detection\\image2.jpeg",
    r"C:\\Ml projects\\Pothole\\Pothole-Detection\\images3.jpeg"
    ]) 


for id,result in enumerate(results):
    boxes = result.boxes  
    masks = result.masks  
    keypoints = result.keypoints  
    probs = result.probs  
    obb = result.obb  
    # result.show()  
    output = os.path.join("C:\Ml projects\Pothole\Pothole-Detection\output",f"result{id+1}.jpg")  
    result.save(output)