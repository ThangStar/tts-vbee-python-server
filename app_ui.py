import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
from process_tts import ProcessTTS


class ChromeProfileManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrome Profile Manager - Selenium")
        self.root.geometry("600x500")
        self.driver = None
        # Đường dẫn thư mục chứa profiles
        self.chrome_data_path = "chrome_data"

        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(self.chrome_data_path):
            os.makedirs(self.chrome_data_path)

        # File lưu cấu hình
        self.config_file = "profile_config.json"

        # Load cấu hình
        self.config = self.load_config()

        # Tạo giao diện
        self.setup_ui()

        # Load danh sách profile
        self.load_profiles()

    def setup_ui(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Cấu hình grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Label tiêu đề
        title_label = ttk.Label(main_frame, text="Chrome Profile Manager - Selenium",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=10)

        # Frame chứa button refresh
        refresh_frame = ttk.Frame(main_frame)
        refresh_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # Button refresh
        refresh_btn = ttk.Button(
            refresh_frame, text="🔄 Refresh Profiles", command=self.load_profiles)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Button chạy automation
        self.run_automation_btn = ttk.Button(refresh_frame, text="🚀 Chạy Automation",
                                             command=self.run_automation, state='disabled')
        self.run_automation_btn.pack(side=tk.LEFT)

        # Frame danh sách profile
        profile_list_frame = ttk.LabelFrame(
            main_frame, text="Danh sách Profile", padding="10")
        profile_list_frame.grid(row=2, column=0, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=10)
        profile_list_frame.columnconfigure(0, weight=1)
        profile_list_frame.rowconfigure(0, weight=1)

        # Tạo Treeview để hiển thị danh sách profile
        columns = ('Profile', 'Status', 'Action')
        self.profile_tree = ttk.Treeview(
            profile_list_frame, columns=columns, show='headings', height=15)

        # Định nghĩa các cột
        self.profile_tree.heading('Profile', text='Tên Profile')
        self.profile_tree.heading('Status', text='Trạng thái')
        self.profile_tree.heading('Action', text='Hành động')

        # Đặt độ rộng cột
        self.profile_tree.column('Profile', width=200, minwidth=150)
        self.profile_tree.column('Status', width=100, minwidth=80)
        self.profile_tree.column('Action', width=150, minwidth=120)

        # Scrollbar cho Treeview
        scrollbar = ttk.Scrollbar(
            profile_list_frame, orient=tk.VERTICAL, command=self.profile_tree.yview)
        self.profile_tree.configure(yscrollcommand=scrollbar.set)

        # Grid Treeview và scrollbar
        self.profile_tree.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Bind double-click event
        self.profile_tree.bind('<Double-1>', self.on_profile_double_click)

        # Bind selection change event để enable/disable button automation
        self.profile_tree.bind('<<TreeviewSelect>>',
                               self.on_profile_selection_change)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng - Sử dụng Selenium để mở Chrome")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)

    def load_profiles(self):
        """Load danh sách folder trong chrome_data/"""
        try:
            # Xóa tất cả items cũ
            for item in self.profile_tree.get_children():
                self.profile_tree.delete(item)

            profiles = [d for d in os.listdir(self.chrome_data_path)
                        if os.path.isdir(os.path.join(self.chrome_data_path, d))]

            if profiles:
                for profile in sorted(profiles):
                    # Kiểm tra trạng thái profile
                    status = "Sẵn sàng"
                    if profile in self.config:
                        status = "Đã cấu hình"

                    # Thêm vào Treeview
                    self.profile_tree.insert('', 'end', values=(
                        profile, status, "Double-click để mở"))

                self.status_var.set(f"Đã tải {len(profiles)} profile(s)")
            else:
                self.status_var.set("Không tìm thấy profile nào")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể load profiles: {str(e)}")
            self.status_var.set("Lỗi khi load profiles")

    def on_profile_double_click(self, event):
        """Khi double-click vào profile"""
        selection = self.profile_tree.selection()
        if selection:
            item = self.profile_tree.item(selection[0])
            profile_name = item['values'][0]
            self.open_profile_with_selenium(profile_name)

    def open_profile_with_selenium(self, profile_name):
        """Mở Chrome profile bằng Selenium"""
        try:
            self.status_var.set(
                f"Đang mở profile {profile_name} với Selenium...")

            # Chạy trong thread riêng để không block UI
            thread = threading.Thread(
                target=self._open_selenium_thread, args=(profile_name,))
            thread.daemon = True
            thread.start()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở profile: {str(e)}")
            self.status_var.set("Lỗi khi mở profile")

    def _open_selenium_thread(self, profile_name):
        """Thread để mở Chrome với Selenium"""
        try:
            # Đường dẫn profile
            profile_path = os.path.abspath(
                os.path.join(self.chrome_data_path, profile_name))

            # Cấu hình Chrome options
            chrome_options = Options()
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument(
                "--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                'useAutomationExtension', False)

            # Bật performance logging
            chrome_options.set_capability(
                'goog:loggingPrefs', {'performance': 'ALL'})

            # Khởi tạo WebDriver
            driver = webdriver.Chrome(options=chrome_options)

            # Ẩn thông báo automation
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Mở trang mặc định
            driver.get("https://www.google.com")

            self.status_var.set(f"Đã mở profile {profile_name} thành công")

        except Exception as e:
            error_msg = f"Lỗi khi mở profile {profile_name}: {str(e)}"
            messagebox.showerror("Lỗi", error_msg)
            self.status_var.set(f"Lỗi: {str(e)}")

    def load_config(self):
        """Load cấu hình từ file JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            # Không hiển thị lỗi nếu file config chưa tồn tại
            pass
        return {}

    def on_profile_selection_change(self, event):
        """Khi thay đổi selection của profile, enable/disable button automation"""
        selection = self.profile_tree.selection()
        if selection:
            self.run_automation_btn.config(state='normal')
        else:
            self.run_automation_btn.config(state='disabled')

    def run_automation(self):
        """Chạy automation cho profile đang được chọn"""
        selection = self.profile_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Cảnh báo", "Vui lòng chọn một profile để chạy automation")
            return

        item = self.profile_tree.item(selection[0])
        profile_name = item['values'][0]

        try:
            self.status_var.set(
                f"Đang chạy automation cho profile {profile_name}...")
            self.run_automation_btn.config(state='disabled')

            # Chạy automation trong thread riêng
            thread = threading.Thread(
                target=self._run_automation_thread, args=(profile_name,))
            thread.daemon = True
            thread.start()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể chạy automation: {str(e)}")
            self.status_var.set("Lỗi khi chạy automation")
            self.run_automation_btn.config(state='normal')

    def _run_automation_thread(self, profile_name):
        """Thread để chạy automation"""
        try:
            # Đường dẫn profile
            profile_path = os.path.abspath(
                os.path.join(self.chrome_data_path, profile_name))

            # Cấu hình Chrome options
            chrome_options = Options()
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument(
                "--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                'useAutomationExtension', False)

            # Bật performance logging
            chrome_options.set_capability(
                'goog:loggingPrefs', {'performance': 'ALL'})

            # Khởi tạo WebDriver
            self.driver = webdriver.Chrome(options=chrome_options)

            # Ẩn thông báo automation
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Mở trang mặc định
            self.driver.get("https://studio.vbee.vn/studio/text-to-speech")
            time.sleep(10)

            process_tts = ProcessTTS()
            process_tts.start_tts(callback_tts=self.cb_start)
        except Exception as e:
            print("CONFIG ERROR", e)

    def cb_start(self, content):
        try:
            editable_div = self.driver.find_element(
                By.XPATH,
                "//div[@contenteditable='true']"
            )

            # Click vào để focus
            editable_div.click()
            time.sleep(2)
            
            pyperclip.copy(content)
            # Select all text trước, sau đó dán
            editable_div.send_keys(Keys.CONTROL + 'a')
            editable_div.send_keys(Keys.CONTROL + 'v')

            # Bật Performance Logging để bắt network requests
            self.driver.execute_cdp_cmd('Performance.enable', {})

            # Bật Network Logging
            self.driver.execute_cdp_cmd('Network.enable', {})

            # Lưu trữ requests để phân tích
            requests_data = []

            # Click button TTS
            button_tts = self.driver.find_element(
                By.XPATH, "//button[@id='convert-tts']")
            button_tts.click()

            # Chờ và thu thập requests
            time.sleep(5)
            auth_value = None
            # Lấy performance logs
            try:
                logs = self.driver.get_log('performance')
                for entry in logs:
                    try:
                        message = json.loads(entry['message'])
                        if 'message' in message and message['message']['method'] == 'Network.requestWillBeSent':
                            request = message['message']['params']['request']
                            if '/api/v1/synthesis' in request['url']:
                                request_info = {
                                    'url': request['url'],
                                    'method': request['method'],
                                    'headers': request['headers'],
                                    'postData': request.get('postData', '')
                                }
                                requests_data.append(request_info)
                                print(f"🔍 Bắt được API /api/v1/synthesis:")
                                if 'Authorization' in request_info['headers']:
                                    auth_value = request_info['headers']['Authorization']
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"Lỗi khi lấy performance logs: {e}")
                # Tắt logging
            self.driver.execute_cdp_cmd('Performance.disable', {})
            self.driver.execute_cdp_cmd('Network.disable', {})

            print("TOKEN", auth_value[:20])
            request_id = None
            retry_count = 0
            max_retries = 15
            
            while retry_count < max_retries:
                try:
                    print(f"ĐANG CHỜ TTS.. (lần thử {retry_count + 1}/{max_retries})")
                    time.sleep(5)

                    # Tìm element dựa trên text content và class cha, sau đó select vào span có data-id
                    element = self.driver.find_element(
                        By.XPATH,
                        f"//tr[contains(@class, 'MuiTableRow-root')]//p[contains(text(), '{content.strip()[:20]}')]/ancestor::tr//span[@data-id='play-req-audio']"
                    )

                    request_id = element.get_attribute("data-request-id")
                    print(f"✅ Tìm thấy element, request_id: {request_id}")
                    break
                except Exception as e:
                    retry_count += 1
                    print(f"❌ Lần thử {retry_count}/{max_retries} thất bại: {e}")
                    
                    if retry_count >= max_retries:
                        print("⚠️ Đã thử quá 15 lần, bỏ qua và tiếp tục...")
                        break
                    
                    time.sleep(5)
            # Gửi nội dung
            print("data-request-id:", request_id)

            # check success
            print("🔍 Đang kiểm tra trạng thái TTS...")
            audio_url = None
            while True:
                try:
                    res = requests.get(f"https://vbee.vn/api/v1/requests/{request_id}/audio", headers={
                        "authorization": auth_value
                    })

                    # Kiểm tra response
                    if res.status_code == 200:
                        try:
                            response_data = res.json()

                            # Kiểm tra nếu có audio URL
                            if (response_data.get('status') == 1 and
                                'result' in response_data and
                                    'audio' in response_data['result']):

                                audio_url = response_data['result']['audio']
                                print(f"🎵 TTS HOÀN THÀNH!")
                                print(f"   Audio URL: {audio_url}")
                                break
                            else:
                                print("⏳ TTS đang xử lý... status:",
                                        response_data.get('status'))

                        except json.JSONDecodeError:
                            print("⚠️ Response không phải JSON hợp lệ")

                    # Chờ 5 giây trước khi kiểm tra lại
                    time.sleep(5)

                except Exception as e:
                    print("❌ Lỗi khi kiểm tra TTS:", e)
                    time.sleep(5)

            # trả audio về cho user
            print("audio_url", audio_url)
            return audio_url
            # self.status_var.set(
            #     f"Đã chạy automation cho profile {profile_name} thành công")

        except Exception as e:
            self.status_var.set(f"Lỗi: {str(e)}")

        finally:
            # Re-enable button automation
            self.run_automation_btn.config(state='normal')


if __name__ == "__main__":
    root = tk.Tk()
    app = ChromeProfileManager(root)
    root.mainloop()
