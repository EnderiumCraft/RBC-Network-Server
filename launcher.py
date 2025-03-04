import os
import sys
import json
import base64
import threading
import sqlite3
import bcrypt
import requests
import socket
import subprocess
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UpdateManager:
    def __init__(self, app):
        self.app = app
        self.REPO = "EnderiumCraft/RBC-Network-Server"
        self.LAUNCHER_EXE = "RBCLauncher.exe"
        self.MODPACK_DIR = "Minecraft/game"
        self.current_version = self.load_version()
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        self.update_base_url = f"https://api.github.com/repos/{self.REPO}"

    def load_version(self):
        try:
            with open("version.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"launcher": "1.0.0", "modpack": "1.0.0"}

    def save_version(self):
        with open("version.json", "w") as f:
            json.dump(self.current_version, f)

    def check_updates(self):
        try:
            response = requests.get(f"{self.update_base_url}/releases/latest", headers=self.headers)
            response.raise_for_status()
            latest_release = response.json()
            
            version_content = next(a for a in latest_release["assets"] if a["name"] == "version.json")
            version_response = requests.get(version_content["browser_download_url"])
            latest_version = version_response.json()
            
            updates = {
                "launcher": latest_version["launcher"] != self.current_version["launcher"],
                "modpack": latest_version["modpack"] != self.current_version["modpack"]
            }
            return updates, latest_release
        except Exception as e:
            print(f"Update check failed: {e}")
            return None, None

    def perform_update(self, updates, release):
        try:
            if updates["modpack"]:
                self.update_modpack(release)
                
            if updates["launcher"]:
                self.update_launcher(release)
                return True
                
            if updates["modpack"]:
                self.current_version["modpack"] = release["tag_name"]
                self.save_version()
                
            return False
        except Exception as e:
            messagebox.showerror("Update Error", f"Update failed: {str(e)}")
            return False

    def update_modpack(self, release):
        response = requests.get(f"{self.update_base_url}/contents/{self.MODPACK_DIR}",
                              headers=self.headers, params={"ref": release["tag_name"]})
        response.raise_for_status()
        
        for item in response.json():
            if item["type"] == "file":
                file_path = Path(item["path"])
                download_url = item["download_url"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_response = requests.get(download_url)
                with open(file_path, "wb") as f:
                    f.write(file_response.content)

    def update_launcher(self, release):
        launcher_asset = next(a for a in release["assets"] if a["name"] == self.LAUNCHER_EXE)
        temp_path = Path.home() / "AppData" / "Local" / "Temp" / self.LAUNCHER_EXE
        
        with requests.get(launcher_asset["browser_download_url"], stream=True) as r:
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        script = f"""@echo off
        timeout /t 2 /nobreak >nul
        del "{sys.executable}"
        move /Y "{temp_path}" "{sys.executable}"
        start "" "{sys.executable}"
        del %0
        """
        
        script_path = Path("update.bat")
        with open(script_path, "w") as f:
            f.write(script)
            
        subprocess.Popen(["start", "cmd", "/c", str(script_path)], shell=True)
        self.app.quit()

class MinecraftLauncher(ctk.CTk):
    APP_DATA_DIR = Path.home() / ".rbc_launcher"
    CONFIG_FILE = APP_DATA_DIR / "config.json"

    def __init__(self):
        super().__init__()
        self.allocated_ram = 2048
        self.logged_in_username = None
        self.config = {}
        self.update_manager = UpdateManager(self)
        
        self.setup_paths()
        self.load_config()
        self.db_setup()
        
        self.title("RBC Network Launcher")
        self.geometry("1100x600")
        self.minsize(900, 650)
        self.maxsize(1100, 650)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_login_ui()
        self.after(1000, self.check_updates)

    def setup_paths(self):
        self.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def db_setup(self):
        self.db_path = self.APP_DATA_DIR / "users.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def load_config(self):
        self.config = {"remember_username": False, "last_username": "", "ram_allocation": 2048}
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, "r") as f:
                    loaded_config = json.load(f)
                    if 1024 <= loaded_config.get("ram_allocation", 2048) <= 16384:
                        self.config.update(loaded_config)
                    self.allocated_ram = self.config["ram_allocation"]
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        self.config["ram_allocation"] = self.allocated_ram
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def check_updates(self, silent=False):
        updates, release = self.update_manager.check_updates()
        if updates and any(updates.values()):
            self.show_update_dialog(updates)
        elif not silent:
            messagebox.showinfo("No Updates", "You're already up to date!")

    def show_update_dialog(self, updates):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Updates Available")
        dialog.geometry("350x300")  # More compact size
        dialog.transient(self)
        dialog.grab_set()
        
        dialog.lift()
        dialog.focus_force()
        
        main_frame = ctk.CTkFrame(dialog, fg_color="#2B2B2B", corner_radius=15)
        main_frame.pack(padx=15, pady=15, fill="both", expand=True)

        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(pady=(10, 5), fill="x")
        
        # RBC Logo
        logo_img = ctk.CTkImage(light_image=Image.open("rbc_logo.png"),
                            dark_image=Image.open("rbc_logo.png"),
                            size=(40, 40))
        ctk.CTkLabel(header_frame, image=logo_img, text="").pack(side="left", padx=10)
        
        # Title
        title_label = ctk.CTkLabel(header_frame,
                                text="Updates Available",
                                font=ctk.CTkFont(size=18, weight="bold"),
                                text_color="#FF4B4B")
        title_label.pack(side="left", padx=10)

        # Update List
        update_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        update_frame.pack(pady=10, fill="both", expand=True)
        
        if updates["launcher"]:
            update_item = ctk.CTkFrame(update_frame, fg_color="transparent")
            update_item.pack(pady=3, fill="x")
            ctk.CTkLabel(update_item, 
                    text="• Launcher Update",
                    text_color="#FF4B4B",
                    font=ctk.CTkFont(weight="bold")).pack(side="left")
            
        if updates["modpack"]:
            update_item = ctk.CTkFrame(update_frame, fg_color="transparent")
            update_item.pack(pady=3, fill="x")
            ctk.CTkLabel(update_item,
                    text="• Modpack Update",
                    text_color="#FF4B4B",
                    font=ctk.CTkFont(weight="bold")).pack(side="left")

        # Warning Text
        ctk.CTkLabel(main_frame,
                text="Update required to play!",
                text_color="#E74C3C",
                font=ctk.CTkFont(size=12)).pack(pady=(5, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=20)
        
        update_btn = ctk.CTkButton(btn_frame,
                                text="Install Updates",
                                fg_color="#FF4B4B",
                                hover_color="#FF3030",
                                command=lambda: self.handle_update_choice(True, dialog),
                                width=120)
        update_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(btn_frame,
                                text="Cancel",
                                fg_color="#3A3A3A",
                                hover_color="#2B2B2B",
                                border_color="#FF4B4B",
                                border_width=2,
                                command=lambda: self.handle_update_choice(False, dialog),
                                width=120)
        cancel_btn.pack(side="right", padx=5)

        dialog.wait_window()

    def handle_update_choice(self, choice, dialog):
        self.update_choice = choice
        dialog.destroy()

    def start_update_process(self, parent):
        progress_dialog = ctk.CTkToplevel(parent)
        progress_dialog.title("Updating...")
        progress_dialog.geometry("300x150")
        
        progress_label = ctk.CTkLabel(progress_dialog, text="Downloading updates...")
        progress_label.pack(pady=20)
        
        progress_bar = ctk.CTkProgressBar(progress_dialog)
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        threading.Thread(target=self.run_background_update, args=(progress_dialog, progress_bar)).start()

    def run_background_update(self, dialog, progress_bar):
        updates, release = self.update_manager.check_updates()
        if updates and any(updates.values()):
            restart_needed = self.update_manager.perform_update(updates, release)
            self.after(0, lambda: [progress_bar.stop(), dialog.destroy(),
                                 self.show_update_complete(restart_needed)])

    def show_update_complete(self, restart_needed):
        if restart_needed:
            messagebox.showinfo("Update Complete", "Launcher will now restart!")
        else:
            messagebox.showinfo("Update Complete", "Updates installed successfully!")

    def check_server_status(self, port):
        """Check if server port is reachable"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except Exception as e:
            print(f"Status check error: {e}")
            return False

    def update_server_status(self):
        """Update server status indicators"""
        def update_status(port, label):
            is_online = self.check_server_status(port)
            status_text = "✓" if is_online else "✗"
            status_color = "#2ECC71" if is_online else "#E74C3C"
            self.after(0, lambda: label.configure(
                text=status_text, 
                text_color=status_color
            ))

        # Check statuses in separate threads
        threading.Thread(target=update_status, args=(25860, self.vanilla_status)).start()
        threading.Thread(target=update_status, args=(25566, self.modded_status)).start()


    def setup_login_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Background Image with overlay
        self.bg_image = ctk.CTkImage(Image.open("background.png"), size=(1100, 700))
        self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
        self.bg_label.place(relwidth=1, relheight=1)
        

        # Login Frame
        login_frame = ctk.CTkFrame(self, width=400, height=500)
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # RBC Logo
        logo_image = ctk.CTkImage(light_image=Image.open("rbc_logo.png"),
                                dark_image=Image.open("rbc_logo.png"),
                                size=(150, 150))
        logo_label = ctk.CTkLabel(login_frame, image=logo_image, text="")
        logo_label.pack(pady=(20, 10))

        # Welcome Text
        welcome_label = ctk.CTkLabel(login_frame, 
                                text="Welcome to RBC Network",
                                font=ctk.CTkFont(size=20, weight="bold"),
                                text_color="#ffffff")
        welcome_label.pack(pady=(0, 20))

        # Username Entry
        self.login_username = ctk.CTkEntry(login_frame, 
                                        placeholder_text="Username",
                                        width=300,
                                        height=45,
                                        corner_radius=10,
                                        fg_color="#3a3a3a",
                                        border_color="#FF4B4B",
                                        text_color="#e7e7e7")
        self.login_username.pack(pady=5, padx=20)

        # Password Entry
        self.login_password = ctk.CTkEntry(login_frame, 
                                        placeholder_text="Password",
                                        show="*",
                                        width=300,
                                        height=45,
                                        corner_radius=10,
                                        fg_color="#3a3a3a",
                                        border_color="#FF4B4B",
                                        text_color="#e7e7e7")
        self.login_password.pack(pady=5)

        # Remember Me Checkbox
        self.remember_me_var = ctk.BooleanVar(value=self.config["remember_username"])
        self.remember_check = ctk.CTkCheckBox(login_frame, 
                                            text="Remember Me",
                                            variable=self.remember_me_var,
                                            checkbox_width=20,
                                            checkbox_height=20,
                                            border_color="#FF4B4B",
                                            checkmark_color="#FFFFFF",
                                            fg_color="#FF4B4B",
                                            text_color="#ffffff")
        self.remember_check.pack(pady=10)

        # Login Button
        login_button = ctk.CTkButton(login_frame, 
                                text="Login",
                                command=self.handle_login,
                                width=300,
                                height=45,
                                corner_radius=10,
                                fg_color="#FF4B4B",
                                hover_color="#FF3030",
                                text_color="white",
                                font=ctk.CTkFont(weight="bold"))
        login_button.pack(pady=10)

        # Register Button
        register_button = ctk.CTkButton(login_frame, 
                                    text="Create Account",
                                    command=self.open_register,
                                    width=300,
                                    height=35,
                                    corner_radius=10,
                                    fg_color="transparent",
                                    hover_color="#f0f0f0",
                                    text_color="#FF4B4B",
                                    border_color="#FF4B4B",
                                    border_width=2)
        register_button.pack(pady=10)

        # Pre-fill username if remembered
        if self.config["remember_username"] and self.config["last_username"]:
            self.login_username.insert(0, self.config["last_username"])

    def setup_main_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Load Background Image
        self.bg_image = ctk.CTkImage(Image.open("background.png"), size=(1100, 700))
        self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")  
        self.bg_label.place(relwidth=1, relheight=1)

        
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        # Logo
        self.logo_image = ctk.CTkImage(light_image=Image.open("rbc_logo.png"),
                                      dark_image=Image.open("rbc_logo.png"),
                                      size=(200, 200))
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_image, text="")
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        # Welcome Message
        welcome_label = ctk.CTkLabel(self.sidebar_frame, 
                                   text=f"Welcome, {self.logged_in_username}!",
                                   font=ctk.CTkFont(size=14, weight="bold"))
        welcome_label.grid(row=1, column=0, padx=20, pady=10)

        # Minecraft Username Display
        username_frame = ctk.CTkFrame(self.sidebar_frame, corner_radius=10)
        username_frame.grid(row=2, column=0, padx=20, pady=10)
        
        ctk.CTkLabel(username_frame, text="Minecraft Nickname:").pack(padx=50, pady=5)
        self.username_display = ctk.CTkLabel(username_frame, 
                                           text=self.logged_in_username,
                                           font=ctk.CTkFont(weight="bold"))
        self.username_display.pack(pady=5)

        # Server Selection
        self.server_var = ctk.StringVar(value="Vanilla (25565)")
        self.server_dropdown = ctk.CTkComboBox(self.sidebar_frame,
                                            values=["Vanilla (25565)", "Modded (25566)"],
                                            variable=self.server_var,
                                            width=200,
                                            height=35,
                                            corner_radius=10,
                                            dropdown_fg_color="#2B2B2B",
                                            button_color="#FF4B4B",
                                            border_color="#FF4B4B")
        self.server_dropdown.grid(row=3, column=0, padx=20, pady=(10, 5))

        # Launch Button
        self.launch_button = ctk.CTkButton(self.sidebar_frame,
                                        text="Launch",
                                        command=self.run_minecraft,
                                        width=210,
                                        height=45,
                                        corner_radius=10,
                                        fg_color="#FF4B4B",
                                        hover_color="#FF3030")
        self.launch_button.grid(row=4, column=0, padx=20, pady=(5, 10))
    

        self.progress_bar = ctk.CTkProgressBar(self.sidebar_frame,
                                            mode='indeterminate',
                                            height=10,
                                            width=200,
                                            corner_radius=5)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_bar.grid_remove()  # Hide initially



        buttons_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        buttons_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        # Settings Button
        self.settings_button = ctk.CTkButton(buttons_frame,
                                        text="Settings",
                                        command=self.open_settings,
                                        height=45,
                                        corner_radius=10)
        self.settings_button.grid(row=0, column=0, padx=5, sticky="ew")

        # Open Folder Button
        self.open_folder_button = ctk.CTkButton(buttons_frame,
                                            text="📁",
                                            command=self.open_minecraft_folder,
                                            height=45,
                                            width=5,
                                            corner_radius=10)
        self.open_folder_button.grid(row=0, column=1, padx=5, sticky="ew")


        logout_button = ctk.CTkButton(self.sidebar_frame,
                                    text="Logout",
                                    command=self.handle_logout,
                                    fg_color="transparent",
                                    border_color="#FF4B4B",
                                    border_width=2,
                                    hover_color="#2B2B2B")
        logout_button.grid(row=7, column=0, padx=20, pady=20)

        # Create main content area
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # News Label
        self.news_label = ctk.CTkLabel(self.main_frame, 
                                      text="Latest News",
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.news_label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        # News Textbox
        self.news_text = ctk.CTkTextbox(self.main_frame,
                                       width=600,
                                       corner_radius=10,
                                       font=ctk.CTkFont(size=14))
        self.news_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        news_content = """⚠️ Experimental Launcher Notice ⚠️
        ───────────────────────────────────────
        This launcher is in an experimental stage 
        and intended for testing purposes only. 
        Features may be incomplete or unstable. 

        Use at your own discretion, and expect 
        frequent updates as development progresses. 

        🌟 Latest Updates 🌟
        ───────────────────────────────────────
        • Added real-time server status monitoring
        • New RAM allocation settings (1-16GB)
        • Improved login security system
        • Fixed memory leak

        🎮 Upcoming Features
        ───────────────────────────────────────
        ➤ Player skin customization 
        ➤ Server statistics dashboard
        ➤ Discord rich presence support

        📅 Planned Maintenance
        ───────────────────────────────────────
        - Vanilla server backend upgrades
        - Modded server modpack updates

        💡 Pro Tip:
        Use F2 to capture in-game screenshots!
        They'll be saved in .minecraft/screenshots

        🔧 Known Issues
        ───────────────────────────────────────
        - Occasional texture flickering in menus
        - RAM allocation reset on logout
        - Server status delay during high load

        Join our Discord for real-time updates! 🎉
        """
        
        self.news_text.insert("0.0", news_content)
        self.news_text.configure(state="disabled")


        self.news_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        
        # News Section
        self.news_label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        self.news_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Server Status Section
        status_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        status_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        
        self.main_frame.grid_columnconfigure(0, weight=2)  # News column
        self.main_frame.grid_columnconfigure(1, weight=1)   # Status column

        # Status Content
        ctk.CTkLabel(status_frame, 
                    text="Server Status",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Status List
        status_list = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_list.pack(pady=10, padx=10, fill="both", expand=True)

        # Vanilla Server Status
        vanilla_row = ctk.CTkFrame(status_list, fg_color="transparent")
        vanilla_row.pack(pady=5, fill="x")
        ctk.CTkLabel(vanilla_row, text="Vanilla Server:", width=100).pack(side="left")
        self.vanilla_status = ctk.CTkLabel(vanilla_row, text="Checking...")
        self.vanilla_status.pack(side="right")

        # Modded Server Status
        modded_row = ctk.CTkFrame(status_list, fg_color="transparent")
        modded_row.pack(pady=5, fill="x")
        ctk.CTkLabel(modded_row, text="Modded Server:", width=100).pack(side="left")
        self.modded_status = ctk.CTkLabel(modded_row, text="Checking...")
        self.modded_status.pack(side="right")

        # Refresh Button
        refresh_btn = ctk.CTkButton(status_frame, 
                                text="Refresh Status",
                                command=self.update_server_status,
                                width=120,
                                height=30,
                                fg_color="#4CAF50",
                                hover_color="#45a049")
        refresh_btn.pack(pady=10)

        # Initial status check
        self.update_server_status()


    def handle_login(self):
        username = self.login_username.get()
        password = self.login_password.get()

        # Update config
        self.config["remember_username"] = self.remember_me_var.get()
        self.config["last_username"] = username if self.remember_me_var.get() else ""
        self.save_config()

        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return

        self.cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        result = self.cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Invalid username or password")
            return

        if bcrypt.checkpw(password.encode('utf-8'), result[0]):
            self.logged_in_username = username  # Store the logged in username
            self.setup_main_ui()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def open_register(self):
        register_window = ctk.CTkToplevel(self)
        register_window.title("Register")
        register_window.geometry("400x300")

        # Username Entry
        self.register_username = ctk.CTkEntry(register_window, placeholder_text="Username", width=300, height=40)
        self.register_username.pack(pady=20)

        # Password Entry
        self.register_password = ctk.CTkEntry(register_window, placeholder_text="Password", show="*", width=300, height=40)
        self.register_password.pack(pady=20)

        # Register Button
        register_button = ctk.CTkButton(register_window, text="Register", 
                                      command=lambda: self.handle_register(register_window),
                                      width=300, height=40)
        register_button.pack(pady=20)

    def handle_register(self, window):
        username = self.register_username.get()
        password = self.register_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return

        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            return

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                              (username, password_hash))
            self.conn.commit()
            messagebox.showinfo("Success", "Registration successful")
            window.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")


    def check_updates(self, silent=False):
        """Returns tuple: (updates_dict, release_info)"""
        updates, release = self.update_manager.check_updates()
        if not silent and updates and any(updates.values()):
            self.show_update_dialog(updates)
        return updates, release  # Return the original updates dictionary



    def run_minecraft(self):
        if not self.logged_in_username:
            messagebox.showerror("Error", "Not logged in!")
            return

        updates, release = self.check_updates(silent=True)
        
        if updates and any(updates.values()):
            if not self.show_update_dialog(updates):
                messagebox.showwarning("Update Required", 
                    "You must update to play!")
                self.cleanup_after_launch()
                return
            else:
                restart_needed = self.update_manager.perform_update(updates, release)
                if restart_needed:
                    return

        # Configure UI for launch
        self.launch_button.configure(state="disabled")
        self.progress_bar.grid()
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        selected_server = self.server_var.get()
        server_ip = "localhost"
        server_port = "25565" if selected_server == "Vanilla" else "25566"



        java_path = os.path.join("Minecraft", "jre", "java-runtime-gamma", "windows-x64", "java-runtime-gamma", "bin", "javaw.exe")
        minecraft_dir = os.path.join("Minecraft", "game")
        natives_dir = os.path.join(minecraft_dir, "versions", "Fabric 1.20.4", "natives")
        libraries = [
            os.path.join(minecraft_dir, "libraries", "com", "github", "oshi", "oshi-core", "6.4.5", "oshi-core-6.4.5.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "google", "code", "gson", "gson", "2.10.1", "gson-2.10.1.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "google", "guava", "failureaccess", "1.0.1", "failureaccess-1.0.1.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "google", "guava", "guava", "32.1.2-jre", "guava-32.1.2-jre.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "ibm", "icu", "icu4j", "73.2", "icu4j-73.2.jar"),
            os.path.join(minecraft_dir, "libraries", "by", "ely", "authlib", "6.0.52-ely.4", "authlib-6.0.52-ely.4.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "mojang", "blocklist", "1.0.10", "blocklist-1.0.10.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "mojang", "brigadier", "1.2.9", "brigadier-1.2.9.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "mojang", "datafixerupper", "6.0.8", "datafixerupper-6.0.8.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "mojang", "logging", "1.1.1", "logging-1.1.1.jar"),
            os.path.join(minecraft_dir, "libraries", "ru", "tln4", "empty", "0.1", "empty-0.1.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "mojang", "text2speech", "1.17.9", "text2speech-1.17.9.jar"),
            os.path.join(minecraft_dir, "libraries", "commons-codec", "commons-codec", "1.16.0", "commons-codec-1.16.0.jar"),
            os.path.join(minecraft_dir, "libraries", "commons-io", "commons-io", "2.13.0", "commons-io-2.13.0.jar"),
            os.path.join(minecraft_dir, "libraries", "commons-logging", "commons-logging", "1.2", "commons-logging-1.2.jar"),
            os.path.join(minecraft_dir, "libraries", "io", "netty", "netty-buffer", "4.1.97.Final", "netty-buffer-4.1.97.Final.jar"),
            os.path.join(minecraft_dir, "libraries", "io", "netty", "netty-codec", "4.1.97.Final", "netty-codec-4.1.97.Final.jar"),
            os.path.join(minecraft_dir, "libraries", "io", "netty", "netty-common", "4.1.97.Final", "netty-common-4.1.97.Final.jar"),
            os.path.join(minecraft_dir, "libraries", "io", "netty", "netty-handler", "4.1.97.Final", "netty-handler-4.1.97.Final.jar"),
            os.path.join(minecraft_dir, "libraries", "io", "netty", "netty-resolver", "4.1.97.Final", "netty-resolver-4.1.97.Final.jar"),
            os.path.join(minecraft_dir, "libraries", "io", "netty", "netty-transport-classes-epoll", "4.1.97.Final", "netty-transport-classes-epoll-4.1.97.Final.jar"),
            os.path.join(minecraft_dir, "libraries", "io", "netty", "netty-transport-native-unix-common", "4.1.97.Final", "netty-transport-native-unix-common-4.1.97.Final.jar"),
            os.path.join(minecraft_dir, "libraries", "io", "netty", "netty-transport", "4.1.97.Final", "netty-transport-4.1.97.Final.jar"),
            os.path.join(minecraft_dir, "libraries", "it", "unimi", "dsi", "fastutil", "8.5.12", "fastutil-8.5.12.jar"),
            os.path.join(minecraft_dir, "libraries", "net", "java", "dev", "jna", "jna-platform", "5.13.0", "jna-platform-5.13.0.jar"),
            os.path.join(minecraft_dir, "libraries", "net", "java", "dev", "jna", "jna", "5.13.0", "jna-5.13.0.jar"),
            os.path.join(minecraft_dir, "libraries", "net", "sf", "jopt-simple", "jopt-simple", "5.0.4", "jopt-simple-5.0.4.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "apache", "commons", "commons-compress", "1.22", "commons-compress-1.22.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "apache", "commons", "commons-lang3", "3.13.0", "commons-lang3-3.13.0.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "apache", "httpcomponents", "httpclient", "4.5.13", "httpclient-4.5.13.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "apache", "httpcomponents", "httpcore", "4.4.16", "httpcore-4.4.16.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "apache", "logging", "log4j", "log4j-api", "2.19.0", "log4j-api-2.19.0.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "apache", "logging", "log4j", "log4j-core", "2.19.0", "log4j-core-2.19.0.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "apache", "logging", "log4j", "log4j-slf4j2-impl", "2.19.0", "log4j-slf4j2-impl-2.19.0.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "joml", "joml", "1.10.5", "joml-1.10.5.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-glfw", "3.3.2", "lwjgl-glfw-3.3.2.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-glfw", "3.3.2", "lwjgl-glfw-3.3.2-natives-windows.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-glfw", "3.3.2", "lwjgl-glfw-3.3.2-natives-windows-arm64.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-glfw", "3.3.2", "lwjgl-glfw-3.3.2-natives-windows-x86.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-jemalloc", "3.3.2", "lwjgl-jemalloc-3.3.2.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-jemalloc", "3.3.2", "lwjgl-jemalloc-3.3.2-natives-windows.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-jemalloc", "3.3.2", "lwjgl-jemalloc-3.3.2-natives-windows-arm64.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-jemalloc", "3.3.2", "lwjgl-jemalloc-3.3.2-natives-windows-x86.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-openal", "3.3.2", "lwjgl-openal-3.3.2.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-openal", "3.3.2", "lwjgl-openal-3.3.2-natives-windows.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-openal", "3.3.2", "lwjgl-openal-3.3.2-natives-windows-arm64.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-openal", "3.3.2", "lwjgl-openal-3.3.2-natives-windows-x86.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-opengl", "3.3.2", "lwjgl-opengl-3.3.2.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-opengl", "3.3.2", "lwjgl-opengl-3.3.2-natives-windows.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-opengl", "3.3.2", "lwjgl-opengl-3.3.2-natives-windows-arm64.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-opengl", "3.3.2", "lwjgl-opengl-3.3.2-natives-windows-x86.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-stb", "3.3.2", "lwjgl-stb-3.3.2.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-stb", "3.3.2", "lwjgl-stb-3.3.2-natives-windows.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-stb", "3.3.2", "lwjgl-stb-3.3.2-natives-windows-arm64.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-stb", "3.3.2", "lwjgl-stb-3.3.2-natives-windows-x86.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-tinyfd", "3.3.2", "lwjgl-tinyfd-3.3.2.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-tinyfd", "3.3.2", "lwjgl-tinyfd-3.3.2-natives-windows.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-tinyfd", "3.3.2", "lwjgl-tinyfd-3.3.2-natives-windows-arm64.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl-tinyfd", "3.3.2", "lwjgl-tinyfd-3.3.2-natives-windows-x86.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl", "3.3.2", "lwjgl-3.3.2.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl", "3.3.2", "lwjgl-3.3.2-natives-windows.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl", "3.3.2", "lwjgl-3.3.2-natives-windows-arm64.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "lwjgl", "lwjgl", "3.3.2", "lwjgl-3.3.2-natives-windows-x86.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "slf4j", "slf4j-api", "2.0.7", "slf4j-api-2.0.7.jar"),
            # ASM libraries
            os.path.join(minecraft_dir, "libraries", "org", "ow2", "asm", "asm", "9.7.1", "asm-9.7.1.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "ow2", "asm", "asm-analysis", "9.7.1", "asm-analysis-9.7.1.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "ow2", "asm", "asm-commons", "9.7.1", "asm-commons-9.7.1.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "ow2", "asm", "asm-tree", "9.7.1", "asm-tree-9.7.1.jar"),
            os.path.join(minecraft_dir, "libraries", "org", "ow2", "asm", "asm-util", "9.7.1", "asm-util-9.7.1.jar"),

            # Fabric libraries
            os.path.join(minecraft_dir, "libraries", "net", "fabricmc", "sponge-mixin", "0.15.4+mixin.0.8.7", "sponge-mixin-0.15.4+mixin.0.8.7.jar"),
            os.path.join(minecraft_dir, "libraries", "net", "fabricmc", "intermediary", "1.20.4", "intermediary-1.20.4.jar"),
            os.path.join(minecraft_dir, "libraries", "net", "fabricmc", "fabric-loader", "0.16.10", "fabric-loader-0.16.10.jar"),

            # Existing libraries (keep these)
            os.path.join(minecraft_dir, "libraries", "com", "github", "oshi", "oshi-core", "6.4.5", "oshi-core-6.4.5.jar"),
            os.path.join(minecraft_dir, "libraries", "com", "google", "code", "gson", "gson", "2.10.1", "gson-2.10.1.jar"),
            # ... keep all other existing library entries ...

            # Updated main JAR
            os.path.join(minecraft_dir, "versions", "Fabric 1.20.4", "Fabric 1.20.4.jar")
        ]

        # Java arguments
        java_args = [
            f"-Xms{self.allocated_ram}M",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+DisableExplicitGC",
            "-XX:MaxGCPauseMillis=200",
            "-XX:+AlwaysPreTouch",
            "-XX:+ParallelRefProcEnabled",
            "-XX:+UseG1GC",
            "-XX:G1NewSizePercent=40",
            "-XX:G1MaxNewSizePercent=50",
            "-XX:G1HeapRegionSize=16M",
            "-XX:G1ReservePercent=15",
            "-XX:InitiatingHeapOccupancyPercent=20",
            "-XX:G1HeapWastePercent=5",
            "-XX:G1MixedGCCountTarget=4",
            "-XX:G1MixedGCLiveThresholdPercent=90",
            "-XX:G1RSetUpdatingPauseTimePercent=5",
            "-XX:+UseStringDeduplication",
            "-Xmx16384M",
            "-Dfile.encoding=UTF-8",
            f"-Djava.library.path={natives_dir}",
            f"-Djna.tmpdir={natives_dir}",
            f"-Dorg.lwjgl.system.SharedLibraryExtractPath={natives_dir}",
            f"-Dio.netty.native.workdir={natives_dir}",
            "-Dminecraft.launcher.brand=java-minecraft-launcher",
            "-Dminecraft.launcher.version=1.6.84-j",
            "-cp", ";".join(libraries),
            "net.fabricmc.loader.impl.launch.knot.KnotClient",  # Changed main class
            "--username", self.logged_in_username,
            "--version", "Fabric 1.20.4",  # Updated version
            "--gameDir", minecraft_dir,
            "--assetsDir", os.path.join(minecraft_dir, "assets"),
            "--assetIndex", "12",
            "--uuid", "501e8da5b1cd3df89970618b2b706e97",
            "--accessToken", "[Minecraft is a lie]",
            "--userType", "legacy",
            "--versionType", "release",
            "--width", "925",
            "--height", "530",
            "--server", server_ip,
            "--port", server_port
        ]

    # Launch process
        try:
            self.process = subprocess.Popen(
                [java_path] + java_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Close launcher after short delay if process starts successfully
            self.after(5000, self.quit)  # Close after 3 seconds
            self.monitor_process()

        except Exception as e:
            self.cleanup_after_launch()
            messagebox.showerror("Launch Failed", f"Failed to start Minecraft:\n{str(e)}")

    def monitor_process(self):
        # Only check for immediate errors
        if self.process.poll() is not None and self.process.returncode != 0:
            error = self.process.stderr.read().decode()
            self.show_launch_error(error)
            self.cleanup_after_launch()

    def cleanup_after_launch(self):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.launch_button.configure(state="normal")

    def show_launch_error(self, error):
        self.cleanup_after_launch()
        messagebox.showerror("Launch Error", 
                        f"Minecraft failed to launch:\n\n{error}")


    def open_settings(self):
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x465")
        settings_window.transient(self)
        
        main_container = ctk.CTkFrame(settings_window)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Skin Customization Section
        skin_frame = ctk.CTkFrame(main_container, corner_radius=10)
        skin_frame.pack(pady=10, padx=5, fill="x")

        ctk.CTkLabel(skin_frame, 
                    text="Skin Customization",
                    font=ctk.CTkFont(weight="bold")).pack(pady=10)

        # Skin Preview
        skin_preview = ctk.CTkFrame(skin_frame, width=150, height=200)
        skin_preview.pack(pady=10)
        ctk.CTkLabel(skin_preview, 
                    text="Skin Preview",
                    text_color="#808080").pack(expand=True)

        # Upload Button
        upload_btn = ctk.CTkButton(skin_frame,
                                text="Upload New Skin",
                                command=lambda: messagebox.showinfo("Info", "Skin upload feature coming soon!"),
                                fg_color="#4CAF50",
                                hover_color="#45a049")
        upload_btn.pack(pady=5)

        # Skin Options
        skin_options = ctk.CTkFrame(skin_frame, fg_color="transparent")
        skin_options.pack(pady=10, fill="x")

        ctk.CTkLabel(skin_options, text="Skin Type:").pack(side="left", padx=30)
        self.skin_type = ctk.CTkComboBox(skin_options,
                                    values=["Classic", "Slim"],
                                    state="readonly")
        self.skin_type.pack(side="right", padx=30)
        self.skin_type.set("Classic")

        # Existing RAM Allocation Section
        ram_frame = ctk.CTkFrame(main_container, corner_radius=10)
        ram_frame.pack(pady=10, padx=5, fill="x")
        
        ctk.CTkLabel(ram_frame, text="RAM Allocation (MB):").pack(pady=10)

        # Input frame for manual entry
        input_frame = ctk.CTkFrame(ram_frame, fg_color="transparent")
        input_frame.pack(pady=5, fill="x")

        # Manual input field
        self.ram_entry = ctk.CTkEntry(input_frame,
                                    width=100,
                                    validate="key",
                                    validatecommand=(self.register(self.validate_ram_input), "%P"))
        self.ram_entry.pack(padx=5)
        self.ram_entry.insert(0, str(self.allocated_ram))
        

        # Slider
        self.ram_slider = ctk.CTkSlider(ram_frame,
                                    from_=1024,
                                    to=16384,
                                    command=self.update_ram_values)
        self.ram_slider.set(self.allocated_ram)
        self.ram_slider.pack(pady=5, padx=10, fill="x")

        # Current value display
        self.ram_label = ctk.CTkLabel(ram_frame, text=f"Current: {self.allocated_ram} MB")
        self.ram_label.pack(pady=5)

        # Link entry changes to slider
        self.ram_entry.bind("<KeyRelease>", self.update_slider_from_entry)

        # Save Button
        save_button = ctk.CTkButton(main_container,
                                text="Save Settings",
                                command=lambda: self.save_settings(settings_window),
                                corner_radius=10)
        save_button.pack(pady=20)

    def validate_ram_input(self, value):
        """Validate RAM entry input"""
        if value == "":
            return True
        try:
            return 1024 <= int(value) <= 16384
        except ValueError:
            return False

    def update_ram_values(self, value):
        """Update both slider and entry when slider moves"""
        ram_value = int(float(value))
        self.ram_label.configure(text=f"Current: {ram_value} MB")
        if self.ram_entry.get() != str(ram_value):
            self.ram_entry.delete(0, "end")
            self.ram_entry.insert(0, str(ram_value))

    def update_slider_from_entry(self, event):
        """Update slider position when entry changes"""
        if self.ram_entry.get():
            try:
                value = int(self.ram_entry.get())
                if 1024 <= value <= 16384:
                    self.ram_slider.set(value)
                    self.ram_label.configure(text=f"Current: {value} MB")
            except ValueError:
                pass

    def open_minecraft_folder(self):
        minecraft_dir = os.path.abspath(os.path.join("Minecraft", "game"))
        if os.path.exists(minecraft_dir):
            os.startfile(minecraft_dir)
        else:
            messagebox.showerror("Error", 
                f"Minecraft directory not found at:\n{minecraft_dir}")

    def save_settings(self, window):
        """Handle saving of settings"""
        try:
            ram_value = int(self.ram_entry.get())
            if 1024 <= ram_value <= 16384:
                self.allocated_ram = ram_value
                self.config["ram_allocation"] = ram_value
                self.save_config()
                messagebox.showinfo("Settings Saved", f"RAM allocation set to {ram_value} MB")
                window.destroy()
            else:
                messagebox.showerror("Error", "RAM must be between 1024 and 16384 MB")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")


    def handle_logout(self):
        self.logged_in_username = None
        self.config["last_username"] = ""
        self.config["remember_username"] = False
        self.save_config()
        self.setup_login_ui()


    def on_close(self):
        self.save_config()
        self.conn.close()
        self.destroy()



if __name__ == "__main__":
    app = MinecraftLauncher()
    app.after(1000, lambda: app.check_updates(silent=True))
    app.mainloop()