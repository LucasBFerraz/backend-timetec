import requests

class WhatsAppAPI:
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def send_custom_payload(self, payload: dict):
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {
                "error": "request_exception",
                "message": str(e)
            }

    def _handle_response(self, response):
        try:
            data = response.json()
        except ValueError:
            return {
                "error": "invalid_json",
                "status_code": response.status_code,
                "message": response.text
            }

        # Catch explicit errors in successful (200) responses
        if "error" in data:
            return {
                "error": "api_error",
                "status_code": response.status_code,
                "message": data["error"].get("message", "Unknown error"),
                "details": data["error"]
            }

        # If no errors and expected message ID is missing
        if "messages" not in data:
            return {
                "error": "no_messages",
                "status_code": response.status_code,
                "message": "Response returned 200 but no message was sent.",
                "details": data
            }

        # Success
        return data
