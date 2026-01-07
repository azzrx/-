from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    @task(3)
    def get_students(self):
        self.client.get('/api/students?page=1&limit=10')

    @task(1)
    def login(self):
        self.client.post('/api/login', json={
            'username': 'load_test_user',
            'password': '123456'
        })
