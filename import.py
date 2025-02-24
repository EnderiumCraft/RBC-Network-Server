import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

class MinecraftLauncher(tk.Tk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("RBC NETWORK")
        self.geometry("1000x550")
        self.configure(bg="#1e1e1e")

        # Add background image
        self.bg_image = tk.PhotoImage(file="background.png")
        self.bg_label = tk.Label(self, image=self.bg_image)
        self.bg_label.place(relwidth=1, relheight=1)


        self.left_frame = tk.Frame(self, bg="#1e1e1e")
        self.left_frame.pack(side="left", padx=20, pady=20)

       
        self.right_frame = tk.Frame(self, bg="#1e1e1e")
        self.right_frame.pack(side="right", padx=20, pady=20)

        # Load the RBC logo
        self.logo = tk.PhotoImage(file="rbc_logo.png")
        self.logo = self.logo.subsample(4, 4)
        
        self.logo_label = tk.Label(self.left_frame, image=self.logo, bg="#1e1e1e")
        self.logo_label.pack(pady=20)

        # Username entry section
        self.username_label = tk.Label(self.left_frame, text="Username:", font=("Segoe UI", 12), fg="white", bg="#1e1e1e")
        self.username_label.pack(pady=(5, 0))

        self.username_entry = tk.Entry(self.left_frame, font=("Segoe UI", 12), fg="black", relief="flat", width=25)
        self.username_entry.pack(pady=(0, 10))

        # Server selection dropdown
        self.server_label = tk.Label(self.left_frame, text="Select Server:", font=("Segoe UI", 12), fg="white", bg="#1e1e1e")
        self.server_label.pack(pady=(5, 0))

        self.server_var = tk.StringVar()
        self.server_var.set("Vanilla")  # Default server
        self.server_dropdown = ttk.Combobox(self.left_frame, textvariable=self.server_var, font=("Segoe UI", 12), values=["Vanilla", "Modded"], width=23)
        self.server_dropdown.pack(pady=(0, 20))

        # Launch Button
        self.launch_button = tk.Button(self.left_frame, text="Launch", font=("Segoe UI", 14), bg="#ff0000", fg="white", relief="flat", command=self.run_minecraft, bd=0, width=15, height=2)
        self.launch_button.pack(pady=(0, 10))
        self.create_rounded_button(self.launch_button)

        # Settings Button
        self.settings_button = tk.Button(self.left_frame, text="Settings", font=("Segoe UI", 12), bg="#2e2e2e", fg="white", relief="flat", command=self.open_settings, bd=0, width=15, height=2)
        self.settings_button.pack()
        self.create_rounded_button(self.settings_button)

        # News section
        self.news_label = tk.Label(self.right_frame, text="Latest News", font=("Segoe UI", 14, "bold"), fg="white", bg="#1e1e1e")
        self.news_label.pack(pady=(10, 5))

        # Frame to hold text widget and scrollbar
        self.news_frame = tk.Frame(self.right_frame, bg="#1e1e1e")
        self.news_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollable Text Widget for News
        self.news_text = tk.Text(self.news_frame, font=("Segoe UI", 12), fg="white", width=40, height=15, bd=0, bg="#1e1e1e", wrap="word", padx=10, pady=5, state="disabled")
        self.news_text.pack(side="left", fill="both", expand=True)

        # Scrollbar
        self.news_scrollbar = tk.Scrollbar(self.news_frame, command=self.news_text.yview, bg="#1e1e1e")
        self.news_scrollbar.pack(side="right", fill="y")

        # Link scrollbar to text widget
        self.news_text.config(yscrollcommand=self.news_scrollbar.set)

        # Example news items
        news_items = [
            "📢 Server update: New features coming soon!\n\n",
            "🔧 Maintenance scheduled for tomorrow at 3 PM UTC.\n\n",
            "🌍 New modded server launched! Explore new worlds and mechanics.\n\n",
            "🎉 Join us for the next community event this Saturday!\n\n",
            "TESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTESTTESTEST\n\n"
        ]

        # Function to update news
        def update_news():
            self.news_text.config(state="normal") 
            self.news_text.delete("1.0", tk.END)  
            for item in news_items:
                self.news_text.insert(tk.END, item)
            self.news_text.config(state="disabled")  

        update_news()  # Load initial news


    def run_minecraft(self):
        username = self.username_entry.get()
        if not username:
            messagebox.showwarning("Input Error", "Please enter a username.")
            return

        selected_server = self.server_var.get()
        server_ip = "localhost"
        server_port = "25565" if selected_server == "Vanilla" else "25566"



        java_path = r"/Minecraft/jre/java-runtime-gamma/windows-x64/java-runtime-gamma/bin/javaw.exe"
        minecraft_dir = r"/Minecraft/game"
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
            "-Xms8017M",
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
            "--username", username,
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
            result = subprocess.run([java_path] + java_args, check=True, capture_output=True, text=True)
            print("Output:", result.stdout)
            print("Error:", result.stderr)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Launch failed (code {e.returncode}): {e.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("250x200")
        settings_window.configure(bg="#1e1e1e")

        save_button = tk.Button(settings_window, text="Save", font=("Segoe UI", 12), bg="#ff0000", fg="white", relief="flat", bd=0, command=settings_window.destroy, width=15, height=2)
        save_button.pack(pady=20)
        self.create_rounded_button(save_button)

    def create_rounded_button(self, button):
        # Bind hover events
        button.bind("<Enter>", lambda e: self.on_hover_enter(button))
        button.bind("<Leave>", lambda e: self.on_hover_leave(button))

    def on_hover_enter(self, button):
        if button == self.launch_button:
            button.config(bg="#e60000")
        elif button == self.settings_button:
            button.config(bg="#3c3c3c")

    def on_hover_leave(self, button):
        if button == self.launch_button:
            button.config(bg="#ff0000")
        elif button == self.settings_button:
            button.config(bg="#2e2e2e")

# Run the launcher
if __name__ == "__main__":
    app = MinecraftLauncher()
    app.mainloop()