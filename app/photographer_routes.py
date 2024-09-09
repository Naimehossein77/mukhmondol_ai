from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from app.db import get_db_connection
from app.firebase import upload_image_to_firebase
from app.face_recognition_utils import process_image
import face_recognition
import numpy as np
from typing import List

from app.unknown_user import save_unknown_embedding

router = APIRouter()

def get_photographer_id_by_email(email):
    """Retrieve the photographer's ID using their email."""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "SELECT id FROM photographers WHERE email = %s"
    cursor.execute(sql, (email,))
    result = cursor.fetchone()
    cursor.close()
    db_conn.close()
    return result[0] if result else None

def save_image_info(user_id, photographer_id, image_url):
    """Save image information to the database."""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "INSERT INTO images (user_id, photographer_id, image_url) VALUES (%s, %s, %s)"
    cursor.execute(sql, (user_id, photographer_id, image_url))
    db_conn.commit()
    cursor.close()
    db_conn.close()

def find_matching_users(face_encoding):
    """Find users with matching face encodings."""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "SELECT id, embedding FROM users"
    cursor.execute(sql)
    users = cursor.fetchall()
    cursor.close()
    db_conn.close()

    matched_users = []
    for user in users:
        user_id, embedding_blob = user
        saved_embedding = np.frombuffer(embedding_blob, dtype=np.float64)
        if face_recognition.compare_faces([saved_embedding], face_encoding,tolerance= 0.4)[0]:
            matched_users.append(user_id)
    
    return matched_users

def get_images_by_photographer(photographer_id: int) -> List[dict]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT image_url FROM images
        WHERE photographer_id = %s
    """, (photographer_id,))
    images = cursor.fetchall()
    cursor.close()
    conn.close()
    return images



@router.post("/upload_photographer")
async def upload_photographer_image(
    file: UploadFile = File(...),
    photographer_email: str = Form(...)
):
    photographer_id = get_photographer_id_by_email(photographer_email)
    if not photographer_id:
        return {"message": "Photographer not found"}

    # Save uploaded image locally
    image_path = f"temp_{file.filename}"
    with open(image_path, "wb") as f:
        f.write(await file.read())

    # Load and process the image
    _, face_encodings = process_image(image_path)

    for face_encoding in face_encodings:
        matched_users = find_matching_users(face_encoding)
        if matched_users:
            for user_id in matched_users:
                image_url = upload_image_to_firebase(image_path, f"photographer_{photographer_id}_user_{user_id}_{file.filename}")
                save_image_info(user_id, photographer_id, image_url)
                # send_image_to_user(user_id, image_url)
        else:
           image_url = upload_image_to_firebase(image_path, f"photographer_{photographer_id}_user_unknown_{file.filename}")
           save_unknown_embedding(face_encoding,image_url,photographer_id)
            # save_face_encoding_for_future(face_encoding)

    return {"message": "Processing completed"}



@router.post("/register_photographer")
async def register_photographer(name: str = Form(...), email: str = Form(...)):
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "INSERT INTO photographers (name, email) VALUES (%s, %s)"
    cursor.execute(sql, (name, email))
    db_conn.commit()
    photographer_id = cursor.lastrowid
    cursor.close()
    return {"photographer_id": photographer_id, "message": "Photographer registered successfully"}



@router.get("/images/{photographer_id}")
async def get_photographer_images(photographer_id: int):
    images = get_images_by_photographer(photographer_id)
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this photographer")
    return {"images": images}