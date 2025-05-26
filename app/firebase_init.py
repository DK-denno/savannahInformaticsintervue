import firebase_admin
from firebase_admin import credentials
import os

def initialize_firebase():
    print("initialize_firebase -> ()")
    if not firebase_admin._apps:
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        if not cred_path:
            raise ValueError("FIREBASE_CREDENTIALS_PATH not set in environment variables")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)