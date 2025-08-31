import socket
import time
from typing import Optional


import requests
import json

class ProcessTTS:
    def __init__(self) -> None:
        print("ĐÃ KHỞI TẠO SELENIUM")

    def init_driver(self):
        pass

    def task_need_process(self):
        response = requests.get('http://localhost:5000/api/get_new_tts')
        if response.status_code == 200:
            return response.json()
        return None

    def start_tts(self, callback_tts):
        print("Observing TTS..")
        while True:
            item = self.task_need_process()
            print(item)
            if not item:
                print("Đang chờ TTS..")
                time.sleep(10)
                continue
            print("START TTS..")
            # selenium_start
            
            print("Xử lý TTS..", item['key'], "\nID:", item['id'])
            
            # Simulate processing work here
            print("item['content']", item['content'])
            url = callback_tts(item['content'])

            self.update_status(item, 'done', url)
            print(f"TTS {item.get('id')} processed with URL: {url}")

    def selenium_start(self):
        pass
    def update_status(self, item, status: str, url: str = None):
        try:
            # Use HTTP POST to trigger socket emission and database update
            payload = {
                'socket_id': item['connection_id'],
                'event_name': 'enqueue_tts_result',
                'event_data': { 
                    'id': item.get('id'),  # Include TTS ID for database update
                    'item': item, 
                    'url': url, 
                    'status': status 
                }
            }
            
            response = requests.post('http://127.0.0.1:5000/api/emit_socket', 
                                  json=payload, 
                                  headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                result = response.json()
                print(f"Successfully emitted status update for item {item.get('id', 'unknown')}: {status}")
                print(f"Response: {result}")
            else:
                print(f"Failed to emit status update. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Error emitting status update: {e}")

def fake_callback(content):
    time.sleep(10)
    return "URLLLLLLL..."
# process_tts = ProcessTTS()
# process_tts.start_tts(callback_tts=fake_callback)