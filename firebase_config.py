import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

    if firebase_key:
        try:
            service_account = json.loads(firebase_key)
            cred = credentials.Certificate(service_account)
        except Exception:
            cred = credentials.Certificate("serviceAccountKey.json")
    else:
        cred = credentials.Certificate("serviceAccountKey.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()