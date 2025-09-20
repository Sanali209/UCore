"""
Performance test for UCore API endpoints using Locust.

To run this test:
1. Start the UCore application.
2. Run: locust -f tests/performance/locustfile.py
3. Open http://localhost:8089 in your browser and start the test.
"""

from locust import HttpUser, task, between

class WebAppUser(HttpUser):
    host = "http://127.0.0.1:8888"
    wait_time = between(1, 3)

    @task(3)
    def get_file_list(self):
        self.client.get("/api/files")

    @task(1)
    def upload_file(self):
        with open("tests/assets/sample.jpg", "rb") as f:
            files = {"file": ("sample.jpg", f, "image/jpeg")}
            self.client.post("/api/files", files=files)
