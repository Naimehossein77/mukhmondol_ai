import firebase_admin
from firebase_admin import credentials, storage

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
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
