import unittest

from app import app
from firebase_config import db


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.test_doc_id = "test-student"
        self.test_doc_ref = db.collection("students").document(self.test_doc_id)
        self.test_doc_ref.set({"roll": self.test_doc_id, "name": "Test Student", "course": "CS"})

    def tearDown(self):
        self.test_doc_ref.delete()

    def test_home_page_is_available(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_view_students_shows_course_data(self):
        response = self.client.get("/view_students")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"DS", response.data)
        self.assertIn(b"Edit", response.data)
        self.assertIn(b"Delete", response.data)

    def test_edit_student_updates_data(self):
        response = self.client.post(
            f"/edit_student/{self.test_doc_id}",
            data={"roll": self.test_doc_id, "name": "Updated Student", "course": "AI"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        updated = self.test_doc_ref.get()
        self.assertEqual(updated.to_dict()["name"], "Updated Student")
        self.assertEqual(updated.to_dict()["course"], "AI")

    def test_delete_student_removes_data(self):
        response = self.client.get(f"/delete_student/{self.test_doc_id}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.test_doc_ref.get().exists)


if __name__ == "__main__":
    unittest.main()
