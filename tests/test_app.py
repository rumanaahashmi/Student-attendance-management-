import unittest
from app import app
from firebase_config import db


class AppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        self.test_doc_id = "test-student-100"
        self.test_doc_ref = db.collection("students").document(self.test_doc_id)
        self.test_doc_ref.set({
            "roll": self.test_doc_id,
            "name": "Test Student",
            "course": "Computer Science"
        })

    def tearDown(self):
        self.test_doc_ref.delete()
        # Clean up test attendance
        att_ref = db.collection("attendance").document(f"2026-07-31_{self.test_doc_id}")
        att_ref.delete()

    def login_demo_user(self):
        return self.client.post(
            "/login",
            data={"email": "admin@school.com", "password": "admin123"},
            follow_redirects=True
        )

    def test_home_page_is_available(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)

    def test_login_and_logout(self):
        response = self.login_demo_user()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back", response.data)

        logout_resp = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(logout_resp.status_code, 200)
        self.assertIn(b"logged out", logout_resp.data)

    def test_view_students_shows_course_data(self):
        response = self.client.get("/view_students")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Computer Science", response.data)
        self.assertIn(b"Edit", response.data)
        self.assertIn(b"Delete", response.data)

    def test_add_student_route(self):
        self.login_demo_user()
        response = self.client.post(
            "/add_student",
            data={"roll": "999", "name": "New Student", "course": "Data Science"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"New Student", response.data)

        # Cleanup
        db.collection("students").document("999").delete()

    def test_edit_student_updates_data(self):
        self.login_demo_user()
        response = self.client.post(
            f"/edit_student/{self.test_doc_id}",
            data={"roll": self.test_doc_id, "name": "Updated Student Name", "course": "AI & ML"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        updated = self.test_doc_ref.get()
        self.assertTrue(updated.exists)
        self.assertEqual(updated.to_dict()["name"], "Updated Student Name")
        self.assertEqual(updated.to_dict()["course"], "AI & ML")

    def test_delete_student_removes_data(self):
        self.login_demo_user()
        response = self.client.get(f"/delete_student/{self.test_doc_id}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.test_doc_ref.get().exists)

    def test_attendance_marking_and_history(self):
        self.login_demo_user()
        # Mark attendance
        post_resp = self.client.post(
            "/attendance",
            data={
                "date": "2026-07-31",
                "course": "Computer Science",
                f"status_{self.test_doc_id}": "Present"
            },
            follow_redirects=True
        )
        self.assertEqual(post_resp.status_code, 200)

        # Check history report
        hist_resp = self.client.get("/attendance_history")
        self.assertEqual(hist_resp.status_code, 200)
        self.assertIn(b"Present", hist_resp.data)


if __name__ == "__main__":
    unittest.main()
