# import firebase_admin
# from firebase_admin import credentials, storage
# import cv2
# import dlib
# import numpy as np
# from fastapi import FastAPI, File, UploadFile
# from uvicorn import run
# import mysql.connector
# # Initialize Firebase Admin SDK
# cred = credentials.Certificate('naim-bcec9-firebase-adminsdk-p2vqv-16833a0772.json')
# firebase_admin.initialize_app(cred, {
#     'storageBucket': 'gs://naim-bcec9.appspot.com'
# })

# def upload_image_to_firebase(image_path, image_name):
#     """Upload image to Firebase Storage and return the download URL."""
#     bucket = storage.bucket()
#     blob = bucket.blob(image_name)
#     blob.upload_from_filename(image_path)
#     blob.make_public()  # Make the file public
#     return blob.public_url





# # Initialize FastAPI
# app = FastAPI()

# # Initialize face detector and recognizer
# detector = dlib.get_frontal_face_detector()
# shape_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
# face_rec_model = dlib.face_recognition_model_v1('dlib_face_recognition_resnet_model_v1.dat')

# # MySQL Database connection
# db_conn = mysql.connector.connect(
#     host='localhost',
#     user='pinpoint',
#     password='pinpoint',
#     database='your_database'
# )

# def save_embedding_to_db(name, email, embedding):
#     """Save face embedding to MySQL database."""
#     cursor = db_conn.cursor()
#     embedding_blob = embedding.tobytes()
#     sql = "INSERT INTO users (name, email, embedding) VALUES (%s, %s, %s)"
#     cursor.execute(sql, (name, email, embedding_blob))
#     db_conn.commit()
#     cursor.close()

# @app.post("/upload/")
# async def upload_image(file: UploadFile = File(...), name: str = None, email: str = None):
#     # Save uploaded image locally
#     image_path = f"temp_{file.filename}"
#     with open(image_path, "wb") as f:
#         f.write(await file.read())

#     # Load and process the image
#     image = cv2.imread(image_path)
#     gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     faces = detector(gray_image)

#     embeddings = []
#     for face in faces:
#         shape = shape_predictor(gray_image, face)
#         embedding = np.array(face_rec_model.compute_face_descriptor(image, shape))
#         embeddings.append(embedding)

#         # Save the first detected face embedding to the database
#         if name and email:
#             save_embedding_to_db(name, email, embedding)

#     # Upload the image to Firebase
#     image_url = upload_image_to_firebase(image_path, file.filename)

#     # Return response
#     return {"image_url": image_url, "embeddings": len(embeddings)}

# if __name__ == "__main__":
#     run(app, host="0.0.0.0", port=8000)






import firebase_admin
from firebase_admin import credentials, storage
import cv2
import face_recognition
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form
from uvicorn import run
import mysql.connector

# Initialize Firebase Admin SDK
cred = credentials.Certificate('naim-bcec9-firebase-adminsdk-p2vqv-16833a0772.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'naim-bcec9.appspot.com'
})

def upload_image_to_firebase(image_path, image_name):
    """Upload image to Firebase Storage and return the download URL."""
    bucket = storage.bucket()
    blob = bucket.blob(image_name)
    blob.upload_from_filename(image_path)
    blob.make_public()  # Make the file public
    return blob.public_url

# Initialize FastAPI
app = FastAPI()

# MySQL Database connection
db_conn = mysql.connector.connect(
    host='localhost',
    user='pinpoint',
    password='pinpoint',
    database='mukhmondol'
)

def save_embedding_to_db(name, email, embedding):
    """Save face embedding to MySQL database."""
    print("Saving data to mysql")
    cursor = db_conn.cursor()
    embedding_blob = embedding.tobytes()
    sql = "INSERT INTO users (name, email, embedding) VALUES (%s, %s, %s)"
    cursor.execute(sql, (name, email, embedding_blob))
    db_conn.commit()
    cursor.close()

@app.post("/upload_user")
async def upload_image(file: UploadFile = File(...), name: str = Form(...), email: str = Form(...)):
    # Save uploaded image locally
    image_path = f"temp_{file.filename}"
    with open(image_path, "wb") as f:
        f.write(await file.read())

    # Load and process the image using face_recognition
    image = face_recognition.load_image_file(image_path)
    
    # Detect faces and compute face encodings
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    embeddings = []
    for face_encoding in face_encodings:
        embeddings.append(face_encoding)
        print(name)
        print(email)
        # Save the first detected face embedding to the database
        if name and email:
            print(name)
            save_embedding_to_db(name, email, face_encoding)

    # Upload the image to Firebase
    image_url = upload_image_to_firebase(image_path, file.filename)

    # Return response
    print(face_encodings)
    return {"image_url": image_url, "embeddings": len(face_encodings)}



@app.post("/upload_photographer")
async def upload_photographer_image(file: UploadFile = File(...)):
    # Save uploaded image locally
    image_path = f"temp_{file.filename}"
    with open(image_path, "wb") as f:
        f.write(await file.read())

    # Load and process the image
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    # Check for matches
    for face_encoding in face_encodings:
        matched_users = find_matching_users(face_encoding)
        if matched_users:
            # Send image to matched users
            for user in matched_users:
                send_image_to_user(user, image_path)
        else:
            # Save face encoding for future use
            save_face_encoding_for_future(face_encoding)

    return {"message": "Processing completed"}


def find_matching_users(face_encoding):
    """Find users with matching face encodings."""
    cursor = db_conn.cursor()
    sql = "SELECT name, email, embedding FROM users"
    cursor.execute(sql)
    users = cursor.fetchall()
    cursor.close()

    matched_users = []
    for user in users:
        name, email, embedding_blob = user
        saved_embedding = np.frombuffer(embedding_blob, dtype=np.float64)
        if face_recognition.compare_faces([saved_embedding], face_encoding)[0]:
            matched_users.append(email)
    
    return matched_users

def send_image_to_user(email, image_path):
    """Send image to the user."""
    print(email)
    # Implement the logic to send image (e.g., via email or messaging service)
    pass

def save_face_encoding_for_future(face_encoding):
    """Save new face encoding for future use."""
    print("save it for later")
    # Implement logic to save the new face encoding
    pass


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)
