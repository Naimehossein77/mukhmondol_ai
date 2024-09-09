from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from app.db import get_db_connection
from app.firebase import upload_image_to_firebase
from app.face_recognition_utils import process_image
import numpy as np
from typing import List

from app.unknown_user import *

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

def get_user_id_by_email(email):
    """Retrieve the user's ID using their email."""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "SELECT id FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    result = cursor.fetchone()
    cursor.close()
    db_conn.close()
    return result[0] if result else None

def check_existing_user(email):
    """Check if there is any existing user with email"""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    result = cursor.fetchone()
    cursor.close()
    db_conn.close()
    return result[0] if result else None



@router.post("/register")
async def register_user(file: UploadFile = File(...), name: str = Form(...), email: str = Form(...)):
    # Save uploaded image locally
    
    existing_user = check_existing_user(email)
    if existing_user:
        return {"message": "user already exist with email: {email}".format(email=email)}
    image_path = f"temp_{file.filename}"


    with open(image_path, "wb") as f:
        f.write(await file.read())

    # Load and process the image
    _, face_encodings = process_image(image_path)

    if face_encodings:
        # Save the first face encoding to the database
        face_encoding = face_encodings[0]
        save_embedding_to_db(name, email, face_encoding)
        user_id = get_user_id_by_email(email)
        unknown_photo_list = find_matching_unknown_users(face_encoding)
        print(unknown_photo_list)
        if unknown_photo_list:
            for unknown in unknown_photo_list:
        # Link the image with the new user and delete from 'unknown_faces'
                transfer_image_to_user(user_id, unknown['photographer_id'], unknown['image_url'])
                delete_unknown_face(unknown['id'])
                return {"message": "User registered successfully, previous images linked"}
        else:
            return {"message": "User registered successfully, no previous images found"}
    else:
        return {"message": "No face detected in the image"}



@router.get("/images/{user_id}")
async def get_user_images(user_id: int):
    images = get_images_by_user(user_id)
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this user")
    return {"images": images}

