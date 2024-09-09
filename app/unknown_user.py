from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from app.db import get_db_connection
from app.firebase import upload_image_to_firebase
from app.face_recognition_utils import process_image
import numpy as np
from typing import List
import face_recognition


def save_unknown_embedding(embedding, image_url, photographer_id):
    """Save unknown face embedding to the 'unknowns' table."""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    embedding_blob = embedding.tobytes()
    sql = "INSERT INTO unknowns (embedding, image_url, photographer_id) VALUES (%s, %s, %s)"
    cursor.execute(sql, (embedding_blob, image_url, photographer_id))
    db_conn.commit()
    cursor.close()
    db_conn.close()



def find_matching_unknown_users(embedding):
    """Find all matching unknown face embeddings from 'unknowns'."""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "SELECT id, embedding, photographer_id, image_url FROM unknowns"
    cursor.execute(sql)
    unknown_faces = cursor.fetchall()

    matching_unknowns = []
    for unknown_face in unknown_faces:
        unknown_embedding = np.frombuffer(unknown_face[1], dtype=np.float64)
        distance = np.linalg.norm(unknown_embedding - embedding)
        if distance < 0.4:  # Adjust threshold as needed
            matching_unknowns.append({
                'id': unknown_face[0],
                'photographer_id': unknown_face[2],
                'image_url': unknown_face[3]
            })

    cursor.close()
    db_conn.close()
    return matching_unknowns




def transfer_image_to_user(user_id,photographer_id, image_url):
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "INSERT INTO images (user_id,photographer_id, image_url) VALUES (%s, %s, %s)"
    cursor.execute(sql, (user_id, photographer_id, image_url))
    db_conn.commit()
    cursor.close()
    db_conn.close()

def delete_unknown_face(unknown_id):
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    sql = "DELETE FROM unknowns WHERE id = %s"
    cursor.execute(sql, (unknown_id,))
    db_conn.commit()
    cursor.close()
    db_conn.close()
