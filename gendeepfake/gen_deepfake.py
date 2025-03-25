import cv2
import insightface
import threading
import os
from .face_analyser import get_one_face, get_many_faces, find_similar_face
from .face_reference import get_face_reference, set_face_reference, clear_face_reference

FACE_SWAPPER = None
THREAD_LOCK = threading.Lock()


def get_face_swapper():
    global FACE_SWAPPER
    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            # Lấy đường dẫn tuyệt đối đến thư mục chứa gen_deepfake.py
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Tạo đường dẫn tuyệt đối đến file model
            model_path = os.path.join(current_dir, 'models', 'inswapper_128.onnx')

            # Kiểm tra xem file model có tồn tại không
            if not os.path.exists(model_path):
                # Thử tìm ở thư mục .models
                alt_model_path = os.path.join(current_dir, '.models', 'inswapper_128.onnx')
                if os.path.exists(alt_model_path):
                    model_path = alt_model_path
                else:
                    raise FileNotFoundError(f"Model file not found at {model_path} or {alt_model_path}")

            print(f"Loading model from: {model_path}")
            FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=["DmlExecutionProvider"],
                                                           provider_options=[{}])
            print(FACE_SWAPPER.session.get_providers())
    return FACE_SWAPPER


# Phần còn lại của file giữ nguyên
def swap_face(source_face, target_face, frame):
    return get_face_swapper().get(frame, target_face, source_face, paste_back=True)


def process_frame(source_face, reference_face, frame):
    faces = get_many_faces(frame)
    if faces:
        for target_face in faces:
            frame = swap_face(source_face, target_face, frame)
    return frame


def process_video(source_path, target_path, output_path):
    source_face = get_one_face(cv2.imread(source_path))
    video = cv2.VideoCapture(target_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break
        reference_face = get_face_reference() or get_one_face(frame)
        set_face_reference(reference_face)
        result_frame = process_frame(source_face, reference_face, frame)
        out.write(result_frame)

    video.release()
    out.release()
    clear_face_reference()


if __name__ == "__main__":
    source_path = "input.png"
    target_path = "target_1.mp4"
    output_path = "output_1.mp4"

    process_video(source_path, target_path, output_path)
    print("Hoán đổi khuôn mặt hoàn tất!")