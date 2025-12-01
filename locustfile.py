from locust import HttpUser, task, between

class StreamlitUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def home_page(self):
        self.client.get("/")
