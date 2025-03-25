FACE_REFERENCE = None

def get_face_reference():
    return FACE_REFERENCE

def set_face_reference(face):
    global FACE_REFERENCE
    FACE_REFERENCE = face

def clear_face_reference():
    global FACE_REFERENCE
    FACE_REFERENCE = None
