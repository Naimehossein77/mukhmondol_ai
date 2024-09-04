import firebase_admin
from firebase_admin import credentials, storage
import cv2
import dlib
import numpy as np
from fastapi import FastAPI, File, UploadFile
from uvicorn import run
import mysql.connector
# Initialize Firebase Admin SDK
cred = credentials.Certificate('path/to/your-firebase-adminsdk.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'your-bucket-name.appspot.com'
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

# Initialize face detector and recognizer
detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
face_rec_model = dlib.face_recognition_model_v1('dlib_face_recognition_resnet_model_v1.dat')

# MySQL Database connection
db_conn = mysql.connector.connect(
    host='your_host',
    user='your_username',
    password='your_password',
    database='your_database'
)

def save_embedding_to_db(name, email, embedding):
    """Save face embedding to MySQL database."""
    cursor = db_conn.cursor()
    embedding_blob = embedding.tobytes()
    sql = "INSERT INTO users (name, email, embedding) VALUES (%s, %s, %s)"
    cursor.execute(sql, (name, email, embedding_blob))
    db_conn.commit()
    cursor.close()

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...), name: str = None, email: str = None):
    # Save uploaded image locally
    image_path = f"temp_{file.filename}"
    with open(image_path, "wb") as f:
        f.write(await file.read())

    # Load and process the image
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector(gray_image)

    embeddings = []
    for face in faces:
        shape = shape_predictor(gray_image, face)
        embedding = np.array(face_rec_model.compute_face_descriptor(image, shape))
        embeddings.append(embedding)

        # Save the first detected face embedding to the database
        if name and email:
            save_embedding_to_db(name, email, embedding)

    # Upload the image to Firebase
    image_url = upload_image_to_firebase(image_path, file.filename)

    # Return response
    return {"image_url": image_url, "embeddings": len(embeddings)}

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)
