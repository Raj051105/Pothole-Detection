from ultralytics import YOLO
import os

model = YOLO("best.pt")  

results = model([
    "image1.jpeg",
    "image2.jpeg",
    "images3.jpeg"
    ]) 


for id,result in enumerate(results):
    boxes = result.boxes  
    masks = result.masks  
    keypoints = result.keypoints  
    probs = result.probs  
    obb = result.obb  
    # result.show()  
    output = os.path.join("output",f"result{id+1}.jpg")  
    result.save(output)