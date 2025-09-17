import urllib.parse
import json
import requests
import re
class VbeeAuth:
    def __init__(self):
        self.session = None
    def get_refresh_token(self, random_line, log_callback=print):
        url = "https://accounts.vbee.vn/api/v1/login"
        # random_line dạng usr:psw
        payload = {
            "username": random_line.split(":")[0].replace("\n", ""),
            "password": random_line.split(":")[1].replace("\n", ""),
            "session": self.session
        }
        response = requests.post(url, json=payload)
        try:
            data = response.json()
            refresh_token = data.get("result", {}).get("refresh_token")
            if refresh_token:
                return refresh_token
            else:
                print("Không tìm thấy refresh_token trong response.")
        except Exception as e:
            print("Lỗi khi parse response:", e)
            print("Response:", response.text)

    def get_session(self, log_callback=print):
        URL = "https://auth.vbee.vn/authorize?clientId=aivoice-web-application&codeChallenge=7BxjAcxK7dKxKqLDGkQwl9IZCUVFf9-0AOLn6Fao5tM&codeChallengeMethod=S256&redirectUri=https%3A%2F%2Fstudio.vbee.vn%2Fstudio%2Ftext-to-speech%3F&responseType=code&action=login"
        try:
            res = requests.get(URL, timeout=30)
        except Exception as e:
            print(f"Proxy failed for session: {e}")
            print("Falling back to direct connection...")
            res = requests.get(URL, timeout=30)
            print("Session retrieval successful with direct connection")
        
        html_content = res.text
        next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content, re.DOTALL)
        if next_data_match:
            try:
                json_data = json.loads(next_data_match.group(1))
                session_data = json_data.get('props', {}).get('pageProps', {}).get('sessionData', {})
                session_id = session_data.get('session')
                print(f"Session ID: {session_id}")
                self.session = session_id
                return session_id
            except json.JSONDecodeError:
                print("Failed to parse JSON data")
        else:
            print("Could not find __NEXT_DATA__ script tag")
