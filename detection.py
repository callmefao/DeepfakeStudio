import mediapipe as mp
import torch
import cv2
from models.model import ResNet
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

# Initialize MediaPipe face detection
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.9)

# model
model = ResNet()
state_dict = torch.load('models/deepfake_classifier_resnet.pth', map_location=device)
model.load_state_dict(state_dict)
model = model.to(device)
model.eval()

min_confidence = None
max_confidence = None
# EfficientNet80
def predict(input_tensor):
    global min_confidence, max_confidence
    with torch.no_grad():
        # Pass the input through the model
        outputs = model(input_tensor.to(device))
        if min_confidence is None or max_confidence is None:
            min_confidence = outputs.item()
            max_confidence = outputs.item()
        print("outputs: ", outputs)
        if outputs.item() < min_confidence:
            min_confidence = outputs.item()
        if outputs.item() > max_confidence:
            max_confidence = outputs.item()
        confidence_score = -(outputs.item() + 1.5)
        predicted_class = "Fake" if confidence_score < 0 else "Real"
        print("min_confidence: ", min_confidence)
        print("max_confidence: ", max_confidence)
    return predicted_class, confidence_score


prev_frame_time = 0
curr_frame_time = 0


def process_frame(frame):
    global prev_frame_time, curr_frame_time

    if frame is None:
        return None

    # Calculate FPS
    curr_frame_time = time.time()
    fps = 1 / (curr_frame_time - prev_frame_time) if prev_frame_time > 0 else 0
    prev_frame_time = curr_frame_time

    # Convert the frame to RGB (MediaPipe works with RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detection.process(frame_rgb)

    # If faces are detected
    if results.detections:
        for detection in results.detections:
            bboxC = detection.location_data.relative_bounding_box
            h, w, _ = frame.shape

            # Calculate original bounding box coordinates
            x1, y1 = int(bboxC.xmin * w), int(bboxC.ymin * h)
            x2, y2 = int((bboxC.xmin + bboxC.width) * w), int((bboxC.ymin + bboxC.height) * h)

            # Calculate center of the face
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2

            # Calculate new width and height (1.25 times larger)
            new_width = int((x2 - x1) * 1.25)
            new_height = int((y2 - y1) * 1.25)

            # Calculate new coordinates based on center
            new_x1 = center_x - new_width // 2
            new_y1 = center_y - new_height // 2
            new_x2 = center_x + new_width // 2
            new_y2 = center_y + new_height // 2

            # Ensure coordinates are within frame boundaries
            new_x1 = max(0, new_x1)
            new_y1 = max(0, new_y1)
            new_x2 = min(w, new_x2)
            new_y2 = min(h, new_y2)

            # Crop the face from the frame with the enlarged ROI
            face_crop = frame[new_y1:new_y2, new_x1:new_x2]

            if face_crop.size == 0:  # Skip if face crop is empty
                continue

            # Resize the cropped face to match the model input size
            face_resized = cv2.resize(face_crop, (224, 224))

            # Convert the image to a tensor and normalize
            face_tensor = torch.tensor(face_resized).permute(2, 0, 1).unsqueeze(0) / 255.0

            # Predict whether the face is real or fake
            predicted_class, confidence_score = predict(face_tensor)
            # Set rectangle color based on prediction
            color = (0, 255, 0) if predicted_class == "Real" else (0, 0, 255)  # Green for real, Red for fake

            # Draw bounding box around the enlarged face area
            cv2.rectangle(frame, (new_x1, new_y1), (new_x2, new_y2), color, 2)

            # Display confidence score as a label
            label = f"{predicted_class}: {confidence_score:.2f}"
            cv2.putText(frame, label, (new_x1, new_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Display FPS in the top-right corner
    fps_text = f"FPS: {fps:.1f}"
    cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 255), 2)

    return frame