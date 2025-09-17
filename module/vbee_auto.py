import sys
import requests
import json
import time
import uuid
import xml.etree.ElementTree as ElementTree

class VbeeAuto:
    def __init__(self):

        # Xóa tất cả cookies
        # self.driver.delete_all_cookies()

        # # Xóa Local Storage và Session Storage
        # self.driver.execute_script("window.localStorage.clear();")
        # self.driver.execute_script("window.sessionStorage.clear();")
        self.driver = None

    def send_keys_js(self, selector, text, js=False):
        if js:
            script = """
                var element = document.querySelector(arguments[0]);
                element.value = arguments[1];
                var event = new Event('input', { bubbles: true });
                element.dispatchEvent(event);
                event = new Event('change', { bubbles: true });
            element.dispatchEvent(event);
            """
            self.driver.execute_script(script, selector, text)
        else:
            self.driver.type(selector, text)

    def test_handle_popup(self, log_callback=print):
        if self.driver.is_element_visible("div.brz-popup2__close"):
            log_callback("Popup hiển thị, đang đóng...")
            self.driver.click("div.brz-popup2__close")
            log_callback("Đã đóng popup")
        else:
            log_callback("Không có popup hiển thị")
    def get_access_token(self, cookie_string, log_callback=print):
        try:
            url = "https://accounts.vbee.vn/api/v1/auth/refresh-token"

            # Header chứa Cookie
            headers = {
                "Content-Type": "application/json",
                "Cookie": cookie_string,
            }

            # Body (JSON raw)
            data = {"clientId": "aivoice-web-application"}
            response = requests.post(url, json=data, headers=headers)
            access_token = json.loads(response.text)["result"]["access_token"]
            return access_token
        except Exception as e:
            print(f"error get_access_token: {e}")
            log_callback(e)
            return None

    def tts(self, asset_token, text, SPEECH_VOICE, log_callback=print):
        try:
            url = "https://vbee.vn/api/v1/synthesis"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {asset_token}",
            }
            data = {
                "audioType": "mp3",
                "bitrate": 128,
                "backgroundMusic": {"volume": 80},
                "text": text,
                "voiceCode": "hn_female_ngochuyen_full_48k-fhg",
                "speed": SPEECH_VOICE,
                "datasenses": {
                    "referrer": "studio.vbee.vn",
                    "platform": "web",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
                    "sdk_version": "1.1.9",
                    "unix_timestamp": "1746536466890",
                    "client_id": "5ee0af9a-5dc3-4182-ba04-ffe3dca3e332",
                },
            }
            response = requests.post(url, json=data, headers=headers)
            log_callback(response.text)
            if (
                "error_message" in json.loads(response.text)
                and json.loads(response.text)["error_message"] == "Text too long"
            ):
                log_callback("[ERROR]: Đã vượt quá giới hạn sử dụng!")
                return None
            request_id = json.loads(response.text)["result"]["request_id"]
            # get url audio
            url_audio = f"https://vbee.vn/api/v1/requests/{request_id}/audio"
            time.sleep(3)
            while True:
                url_progress = f"https://vbee.vn/api/v1/requests/{request_id}/progress"
                response = requests.get(url_progress, headers=headers)
                if json.loads(response.text)["result"]["status"] == "SUCCESS":
                    log_callback("Đã tạo audio thành công")
                    break
                time.sleep(1)
            response = requests.get(url_audio, headers=headers)
            return json.loads(response.text)["result"]["audio"]
        except Exception as e:
            print(f"error tts: {e}")
            # nếu lỗi có chứa Invalid URL 'None': No scheme supplied.
            log_callback(e)
            return None


    def check_bonus_characters(self, access_token, log_callback=print):
        active_url = "https://vbee.vn/api/v1/user-tts"
        url = "https://vbee.vn/api/v1/me"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        response = requests.get(active_url, headers=headers)
        time.sleep(1)
        response = requests.get(url, headers=headers)
        bonus_characters = json.loads(response.text)["result"]["bonus_characters"]
        return bonus_characters
    def tts_from_text(self, access_token, content, voice="hn_female_ngochuyen_full_48k-fhg", speed=1.0, save_path="", account_id=0):
        print("PARAMS", voice, save_path)
        synthesis_url = 'https://vbee.vn/api/v1/synthesis'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        payload = {
            "audioType": "mp3",
            "bitrate": 128,
            "backgroundMusic": {"volume": 80},
            "text": content,
            "voiceCode": voice,
            "speed": speed,
            "datasenses": {
                "referrer": "studio.vbee.vn",
                "platform": "web",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
                "sdk_version": "1.1.9",
                "unix_timestamp": "1751786914311",
                "client_id": "4886a962-24b4-461d-93aa-7a1833ff925"
            }
        }
        
        max_retries = 1
        retry_count = 0
        response_data = None
        
        while retry_count < max_retries:
            res = requests.post(url=synthesis_url, headers=headers, json=payload)
            print(f"res: {res.text}")
            
            # Kiểm tra nếu response chứa thông báo bị chặn
            if "Text-to-speech feature has been blocked due to unusual activity" in res.text:
                print("Tài khoản này đã bị khoá!")
                break
            response_data = json.loads(res.text)
            if response_data.get('status') == 0:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"retry..")
                    continue
                else:
                    print(f"retry false")
                    break
            else:
                break
                
        if not response_data or 'result' not in response_data:
            print(f"Lỗi response: {response_data}")
            return None
            
        request_id = response_data.get("result")['request_id']

        # Retry logic để lấy audio
        max_audio_retries = 50  # Tối đa 30 lần thử
        audio_retry_count = 0
        audio_response = None
        
        while audio_retry_count < max_audio_retries:
            audio_response = requests.get(url=f'https://vbee.vn/api/v1/requests/{request_id}/audio', headers=headers)
            print(f"audio_response lần {audio_retry_count + 1}: {audio_response.status_code}")
            
            if audio_response.status_code == 200:
                try:
                    response_json = json.loads(audio_response.text)
                    if response_json.get("status") == 1 and "result" in response_json and "audio" in response_json["result"]:
                        audio_url = response_json["result"]["audio"]
                        print(f"Tìm thấy audio URL: {audio_url}")
                        
                        # Tải audio từ URL
                        audio_file_response = requests.get(audio_url)
                        if audio_file_response.status_code == 200:
                            print("Tải audio file thành công!")
                            
                            # Lưu file âm thanh nếu có save_path
                            if save_path:
                                with open(save_path, "wb") as f:
                                    f.write(audio_file_response.content)
                                print(f"Đã lưu file âm thanh thành công tại: {save_path}")
                                return save_path
                            else:
                                return audio_file_response.content
                        else:
                            print(f"Lỗi khi tải audio file: {audio_file_response.status_code}")
                    else:
                        print("Response không chứa audio URL, thử lại...")
                except json.JSONDecodeError:
                    print("Lỗi parse JSON response")
                except Exception as e:
                    print(f"Lỗi xử lý response: {e}")
            
            audio_retry_count += 1
            if audio_retry_count < max_audio_retries:
                print(f"Lần {audio_retry_count}: Audio chưa sẵn sàng, thử lại sau 3 giây...")
                time.sleep(3)  # Đợi 3 giây trước khi thử lại
            else:
                print(f"Đã thử {max_audio_retries} lần nhưng không lấy được audio")
                break
        
        # Nếu đã thử hết số lần mà không thành công
        print("Không thể lấy audio sau tất cả các lần thử")
        return None