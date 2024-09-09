import face_recognition

def process_image(image_path):
    """Load image and return face locations and encodings."""
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)
    return face_locations, face_encodings
