from locust import HttpUser, task, between

class TicketValidationUser(HttpUser):
    # Wait time between requests (simulates realistic user behavior)
    wait_time = between(1, 3)  

    @task(3)
    def validate_ticket(self):
        """
        Simulate calling the ticket validation endpoint.
        Replace the URL and payload with your actual API details.
        """
        payload = {
            "ticket_id": "123456",
            "user_id": "user_789"
        }
        with self.client.post("/api/tickets/validate", json=payload, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed with status {response.status_code} | {response.text}")

    @task(1)
    def health_check(self):
        """Hit a health endpoint to ensure service availability."""
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Health check failed")
