from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from app.db import get_db_connection
from app.firebase import upload_image_to_firebase
from app.face_recognition_utils import process_image
import numpy as np
from typing import List

router = APIRouter()

def save_embedding_to_db(name, email, embedding):
    """Save face embedding to MySQL database."""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    embedding_blob = embedding.tobytes()
    sql = "INSERT INTO users (name, email, embedding) VALUES (%s, %s, %s)"
    cursor.execute(sql, (name, email, embedding_blob))
    db_conn.commit()
    cursor.close()
    db_conn.close()

def get_images_by_user(user_id: int) -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT image_url FROM images
        WHERE user_id = %s
    """, (user_id,))
    images = cursor.fetchall()
    cursor.close()
    conn.close()
    return images



@router.post("/register")
async def register_user(file: UploadFile = File(...), name: str = Form(...), email: str = Form(...)):
    # Save uploaded image locally
    image_path = f"temp_{file.filename}"
    with open(image_path, "wb") as f:
        f.write(await file.read())

    # Load and process the image
    _, face_encodings = process_image(image_path)

    if face_encodings:
        # Save the first face encoding to the database
        face_encoding = face_encodings[0]
        save_embedding_to_db(name, email, face_encoding)
        return {"message": "User registered successfully"}
    else:
        return {"message": "No face detected in the image"}



@router.get("/images/{user_id}")
async def get_user_images(user_id: int):
    images = get_images_by_user(user_id)
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this user")
    return {"images": images}