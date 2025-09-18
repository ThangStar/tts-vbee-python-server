import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import threading
from process_tts import ProcessTTS
from module.vbee_auth import VbeeAuth
from module.vbee_auto import VbeeAuto

class MinimalTTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VBee TTS Client")
        self.root.geometry("520x360")

        # File lưu cấu hình
        self.config_file = "profile_config.json"

        # Trạng thái thread xử lý
        self.processing_thread = None
        self.is_processing = False

        # Load cấu hình
        self.config = self.load_config()

        # Tạo giao diện
        self.setup_ui()

        # Tự động bắt đầu quan sát TTS queue
        self.start_processing()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        title_label = ttk.Label(main_frame, text="VBee TTS Client", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky=tk.W)

        ttk.Label(main_frame, text="Username").grid(row=1, column=0, sticky=tk.W, padx=(0, 8))
        self.username_var = tk.StringVar(value=self.config.get("username", ""))
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var)
        self.username_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E))

        ttk.Label(main_frame, text="Password").grid(row=2, column=0, sticky=tk.W, padx=(0, 8))
        self.password_var = tk.StringVar(value=self.config.get("password", ""))
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))

        self.save_btn = ttk.Button(main_frame, text="Lưu", command=self.save_credentials)
        self.save_btn.grid(row=2, column=2, padx=(8, 0), sticky=tk.E)

        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="6")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=12, wrap="word", state="disabled")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

    def log(self, *args):
        msg = " ".join(str(a) for a in args)
        def _append():
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
        self.root.after(0, _append)

    def save_credentials(self):
        self.config["username"] = self.username_var.get().strip()
        self.config["password"] = self.password_var.get().strip()
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Thành công", "Đã lưu thông tin đăng nhập")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")

    def start_processing(self):
        if self.is_processing:
            return
        self.is_processing = True
        self.log("Observing TTS queue...")
        def _run():
            try:
                process_tts = ProcessTTS()
                process_tts.start_tts(callback_tts=self.cb_start)
            except Exception as e:
                self.log("PROCESS ERROR:", e)
            finally:
                self.is_processing = False
        self.processing_thread = threading.Thread(target=_run, daemon=True)
        self.processing_thread.start()

    def cb_start(self, content, voice, speech, punctuation):
        try:
            url = None
            attempt = 0
            max_retries = 3

            while attempt < max_retries:
                username = self.username_var.get().strip()
                password = self.password_var.get().strip()
                if not username or not password:
                    self.log("Thiếu username/password. Vui lòng lưu thông tin trước.")
                    return None

                creds = f"{username}:{password}"
                self.log("Lấy session...")
                vbee_auth = VbeeAuth()
                session = vbee_auth.get_session()
                self.log("Session:", session)

                self.log("Lấy refresh_token...")
                print(creds)
                refresh_token = vbee_auth.get_refresh_token(creds)
                if not refresh_token:
                    self.log("Không lấy được refresh_token")
                    return None
                self.log("Refresh token OK")

                self.log("Lấy access_token...")
                vbee_auto = VbeeAuto()
                access_token = vbee_auto.get_access_token(f"aivoice_refresh_token={refresh_token}")
                if not access_token:
                    self.log("Không lấy được access_token")
                    return None
                self.log("Access token OK")

                self.log("Gọi TTS...")
                url = vbee_auto.tts(access_token, content, voice, speech, punctuation)
                if url:
                    self.log("TTS URL:", url)
                    break
                attempt += 1
                if attempt < max_retries:
                    self.log(f"URL None, thử lại ({attempt}/{max_retries})...")
                else:
                    self.log("URL None sau khi thử tối đa, dừng lại.")
                    break
                self.log("TTS URL:", url)
            return url
        except Exception as e:
            self.log("CONFIG ERROR", e)
            return None

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

if __name__ == "__main__":
    root = tk.Tk()
    app = MinimalTTSApp(root)
    root.mainloop()
