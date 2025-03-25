import insightface
import numpy as np
import threading

FACE_ANALYSER = None
THREAD_LOCK = threading.Lock()

def get_face_analyser():
    global FACE_ANALYSER
    with THREAD_LOCK:
        if FACE_ANALYSER is None:
            FACE_ANALYSER = insightface.app.FaceAnalysis(name='buffalo_l', providers=["DmlExecutionProvider"],
                                                         provider_options=[{}])
            FACE_ANALYSER.prepare(ctx_id=-1)  # -1 để tránh dùng CUDA
    return FACE_ANALYSER

def get_one_face(frame, position=0):
    faces = get_many_faces(frame)
    return faces[position] if faces else None

def get_many_faces(frame):
    try:
        return get_face_analyser().get(frame)
    except ValueError:
        return None

def find_similar_face(frame, reference_face):
    faces = get_many_faces(frame)
    if faces:
        for face in faces:
            if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
                distance = np.sum(np.square(face.normed_embedding - reference_face.normed_embedding))
                if distance < 1.2:
                    return face
    return None
