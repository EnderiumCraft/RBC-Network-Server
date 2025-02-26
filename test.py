import os
import subprocess
import tkinter as tk
import sqlite3
import bcrypt
import threading
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from pathlib import Path
import json

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MinecraftLauncher(ctk.CTk):
    APP_DATA_DIR = Path.home() / ".rbc_launcher"
    CONFIG_FILE = APP_DATA_DIR / "config.json"

    def __init__(self):
        super().__init__()
        self.allocated_ram = 2048
        self.logged_in_username = None
        self.config = {}
        
        # Initialize directories and config
        self.setup_paths()
        self.load_config()

        # Database setup
        self.db_path = self.APP_DATA_DIR / "users.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

        # Window setup
        self.title("RBC NETWORK")
        self.geometry("1000x600")
        self.minsize(900, 600)
        self.maxsize(1000, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_login_ui()


    def setup_paths(self):

        self.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def create_tables(self):
        """Create database tables"""
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
        """Load configuration from file"""
        self.config = {
            "remember_username": False,
            "last_username": "",
            "ram_allocation": 2048
        }
        
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, "r") as f:
                    self.config.update(json.load(f))
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")



    def setup_login_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Background Image with overlay
        self.bg_image = ctk.CTkImage(Image.open("background.png"), size=(1000, 600))
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
        self.bg_image = ctk.CTkImage(Image.open("background.png"), size=(1000, 600))
        self.bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")  
        self.bg_label.place(relwidth=1, relheight=1)

        # Create sidebar frame with widgets
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
        self.server_var = ctk.StringVar(value="Vanilla")
        self.server_dropdown = ctk.CTkComboBox(self.sidebar_frame,
                                             values=["Vanilla", "Modded"],
                                             variable=self.server_var,
                                             width=200,
                                             height=35,
                                             corner_radius=10)
        self.server_dropdown.grid(row=3, column=0, padx=20, pady=10)

        # Launch Button
        self.launch_button = ctk.CTkButton(self.sidebar_frame,
                                          text="Launch",
                                          command=self.run_minecraft,
                                          width=200,
                                          height=45,
                                          corner_radius=10,
                                          fg_color="#FF4B4B",
                                          hover_color="#FF3030")
        self.launch_button.grid(row=3, column=0, padx=20, pady=10)

        # Settings Button
        self.settings_button = ctk.CTkButton(self.sidebar_frame,
                                            text="Settings",
                                            command=self.open_settings,
                                            width=200,
                                            height=35,
                                            corner_radius=10)
        self.settings_button.grid(row=4, column=0, padx=20, pady=20)


        logout_button = ctk.CTkButton(self.sidebar_frame,
                                    text="Logout",
                                    command=self.handle_logout,
                                    fg_color="transparent",
                                    border_color="#FF4B4B",
                                    border_width=2,
                                    hover_color="#2B2B2B")
        logout_button.grid(row=5, column=0, padx=20, pady=20)

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
        
        news_content = "Experimental Launcher Notice This launcher is in an experimental stage and is intended for testing purposes only. Features may be incomplete or unstable. Use at your own discretion, and expect updates or changes as development progresses. 🚀"
        
        self.news_text.insert("0.0", news_content)
        self.news_text.configure(state="disabled")

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

    def run_minecraft(self):
        if not self.logged_in_username:
            messagebox.showerror("Error", "Not logged in!")
            return

        selected_server = self.server_var.get()
        server_ip = "localhost"
        server_port = "25565" if selected_server == "Vanilla" else "25566"



        java_path = os.path.join("Minecraft", "jre", "java-runtime-gamma", "windows-x64", "java-runtime-gamma", "bin", "javaw.exe")
        minecraft_dir = os.path.join("Minecraft", "game")
        natives_dir = os.path.join(minecraft_dir, "versions", "1.20.4", "natives")
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
            os.path.join(minecraft_dir, "versions", "1.20.4", "1.20.4.jar")
        ]


        # Java arguments
        java_args = [
            f"-Xms{self.allocated_ram}M",  # Set the initial heap size (min RAM)
            f"-Xmx{self.allocated_ram}M",
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
            "net.minecraft.client.main.Main",
            "--username", self.logged_in_username,
            "--version", "1.20.4",
            "--gameDir", minecraft_dir,
            "--assetsDir", os.path.join(minecraft_dir, "assets"),
            "--assetIndex", "12",
            "--uuid", "501e8da5b1cd3df89970618b2b706e97",
            "--accessToken", "[Minecraft is a lie]",
            "--userType", "legacy",
            "--versionType", "release",
            "--width", "925",
            "--height", "530"
            "--server", server_ip,
            "--port", server_port
            
        ]

        print("Executing command:", [java_path] + java_args)

        try:
            # Start Minecraft in a separate thread
            def launch_minecraft():
                subprocess.run([java_path] + java_args, check=True)

            # Start the Minecraft launch in the background
            threading.Thread(target=launch_minecraft, daemon=True).start()

            # Quit the launcher after 5 seconds
            self.after(5000, self.quit)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Launch failed (code {e.returncode}): {e.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")


    def open_settings(self):
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self)

        # RAM Allocation
        ram_frame = ctk.CTkFrame(settings_window, corner_radius=10)
        ram_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(ram_frame, text="RAM Allocation (MB):").pack(pady=10)
        
        self.ram_slider = ctk.CTkSlider(ram_frame,
                                      from_=1024,
                                      to=16384,
                                      number_of_steps=12,
                                      command=self.update_ram_label)
        self.ram_slider.set(self.allocated_ram)
        self.ram_slider.pack(pady=5, padx=20, fill="x")
        
        self.ram_label = ctk.CTkLabel(ram_frame, text=f"{self.allocated_ram} MB")
        self.ram_label.pack(pady=5)

        # Save Button
        save_button = ctk.CTkButton(settings_window,
                                  text="Save Settings",
                                  command=lambda: self.save_settings(settings_window),
                                  corner_radius=10)
        save_button.pack(pady=10)

    def update_ram_label(self, value):
        self.ram_label.configure(text=f"{int(value)} MB")

    def save_settings(self, window):
        self.allocated_ram = int(self.ram_slider.get())
        messagebox.showinfo("Settings Saved", f"RAM allocation set to {self.allocated_ram} MB")
        window.destroy()


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
    app.mainloop()