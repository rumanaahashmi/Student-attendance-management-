import os
import firebase_admin
from firebase_admin import credentials, firestore

# Get the folder where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Full path to the service account key
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

# Initialize Firebase
cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)

# Firestore database
db = firestore.client()