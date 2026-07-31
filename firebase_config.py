import os
import json
import tempfile
import uuid
import firebase_admin
from firebase_admin import credentials, firestore

# Use /tmp for serverless environments like Vercel
if os.environ.get("VERCEL") or not os.access(os.path.dirname(__file__), os.W_OK):
    LOCAL_DB_FILE = os.path.join(tempfile.gettempdir(), ".local_db.json")
else:
    LOCAL_DB_FILE = os.path.join(os.path.dirname(__file__), ".local_db.json")


class LocalDocumentSnapshot:
    def __init__(self, doc_id, data):
        self.id = str(doc_id)
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data is not None else None


class LocalDocumentRef:
    def __init__(self, collection_ref, doc_id):
        self.collection_ref = collection_ref
        self.id = str(doc_id)

    def set(self, data, merge=False):
        self.collection_ref._set_doc(self.id, data, merge=merge)

    def get(self):
        data = self.collection_ref._get_doc(self.id)
        return LocalDocumentSnapshot(self.id, data)

    def delete(self):
        self.collection_ref._delete_doc(self.id)


class LocalCollectionRef:
    def __init__(self, db_instance, collection_name):
        self.db = db_instance
        self.name = collection_name

    def document(self, doc_id=None):
        if not doc_id:
            doc_id = str(uuid.uuid4())
        return LocalDocumentRef(self, str(doc_id))

    def _get_all(self):
        return self.db._store.get(self.name, {})

    def _get_doc(self, doc_id):
        return self.db._store.get(self.name, {}).get(str(doc_id))

    def _set_doc(self, doc_id, data, merge=False):
        if self.name not in self.db._store:
            self.db._store[self.name] = {}
        if merge and str(doc_id) in self.db._store[self.name]:
            self.db._store[self.name][str(doc_id)].update(data)
        else:
            self.db._store[self.name][str(doc_id)] = dict(data)
        self.db._save()

    def _delete_doc(self, doc_id):
        if self.name in self.db._store and str(doc_id) in self.db._store[self.name]:
            del self.db._store[self.name][str(doc_id)]
            self.db._save()

    def stream(self):
        docs = self._get_all()
        return [LocalDocumentSnapshot(k, v) for k, v in list(docs.items())]

    def where(self, field, op, value):
        docs = self._get_all()
        results = []
        for k, v in docs.items():
            if op == "==" and v.get(field) == value:
                results.append(LocalDocumentSnapshot(k, v))
            elif op == "in" and isinstance(value, (list, tuple, set)) and v.get(field) in value:
                results.append(LocalDocumentSnapshot(k, v))
        return results


class LocalFirestore:
    def __init__(self, db_path=LOCAL_DB_FILE):
        self.db_path = db_path
        self._store = {}
        self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self._store = json.load(f)
            except Exception:
                self._store = {}

        if "students" not in self._store or not self._store["students"]:
            self._store["students"] = {
                "101": {"roll": "101", "name": "Ali Khan", "course": "Computer Science"},
                "102": {"roll": "102", "name": "Sara Ahmed", "course": "Computer Science"},
                "103": {"roll": "103", "name": "Zaid Shaikh", "course": "Data Science"},
            }
            self._save()

    def _save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            print(f"Failed to save local DB: {e}")

    def collection(self, name):
        return LocalCollectionRef(self, name)


db = None
firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
cert_path = "serviceAccountKey.json"

if firebase_key or os.path.exists(cert_path):
    try:
        if not firebase_admin._apps:
            if firebase_key:
                service_account = json.loads(firebase_key)
                cred = credentials.Certificate(service_account)
            else:
                cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as err:
        print(f"[WARNING] Firebase initialization failed: {err}. Using local fallback.")
        db = LocalFirestore()
else:
    print("[INFO] Firebase credentials not found. Using local JSON Firestore fallback.")
    db = LocalFirestore()