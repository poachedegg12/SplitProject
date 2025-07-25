# ───────────────────────────────────────────
# Standard Library Imports
# ───────────────────────────────────────────
import configparser
import os
import platform
import random
import shutil
import ssl
import subprocess
import tempfile
import threading
# ───────────────────────────────────────────
# Tkinter GUI Toolkit Imports
# ───────────────────────────────────────────
import tkinter as tk
from functools import partial
from tkinter import (
    ttk, filedialog, messagebox, Scrollbar, Text, simpledialog
)

# ───────────────────────────────────────────
# Third-Party Library Imports
# ───────────────────────────────────────────
import certifi
import cv2
import pyxdelta
import requests
import simpleaudio as sa
from PIL import Image, ImageTk, ImageSequence
from bs4 import BeautifulSoup
# ───────────────────────────────────────────
# GameBanana API Import
# ───────────────────────────────────────────
from pybanana.api import PyBanana
from requests.adapters import HTTPAdapter
# ───────────────────────────────────────────
# Web Automation (Selenium) Imports
# ───────────────────────────────────────────
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ───────────────────────────────────────────
# Setup
# ───────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
context = ssl.create_default_context(cafile=certifi.where())
api = PyBanana()

# ────────────────
# Utility Functions
# ────────────────
TIMEOUT_DELAY = 3


class LoadingScreen(tk.Toplevel):
    def __init__(self, master, total_steps):
        super().__init__(master)
        self.title("Loading Split Modding Program...")
        self.geometry("500x250")
        self.resizable(False, False)

        self.progress = ttk.Progressbar(self, mode='determinate', maximum=total_steps)
        self.progress.pack(fill='x', padx=20, pady=(20, 10))

        self.log_text = tk.Text(self, height=8, state='disabled', bg='black', fg='lime', font=("Courier", 10))
        self.log_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.update_idletasks()

    def log(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.configure(state='disabled')
        self.log_text.yview_moveto(1.0)
        self.update()

    def update_progress(self, step):
        self.progress['value'] = step
        self.update_idletasks()


def process_mod(ini_id, mod_dir, splash: LoadingScreen):
    try:
        splash.log("Creating GameBanana API interface...")
        api = PyBanana()
        splash.update_progress(1)

        splash.log(f"Fetching mod profile for ID {ini_id}...")
        mod = api.get_mod_profile(int(ini_id))
        splash.update_progress(2)

        name = mod.name or ""
        author = mod.submitter.name if mod.submitter else ""
        description = BeautifulSoup(mod.text or "", "html.parser").get_text().strip()
        video_link = ""
        date_made = ""
        if mod.base and mod.base.date_added:
            try:
                date_made = mod.base.date_added.strftime("%Y-%m-%d")
            except Exception:
                date_made = ""
        like_count = str(mod.like_count or 0)
        download_count = str(mod.download_count or 0)
        link = f"https://gamebanana.com/mods/{ini_id}"

        splash.log("Writing mod.ini file...")
        with open(os.path.join(mod_dir, "mod.ini"), "w", encoding="utf-8") as f:
            f.write("[Mod]\n")
            f.write(f"name = {name}\n")
            f.write(f"description = {description}\n")
            f.write(f"video_link = {video_link}\n")
            f.write(f"author = {author}\n")
            f.write(f"date_made = {date_made}\n")
            f.write(f"like_count = {like_count}\n")
            f.write(f"download_count = {download_count}\n")
            f.write(f"link = {link}\n")
        splash.update_progress(3)

        splash.log("Starting browser to fetch thumbnail...")
        driver = create_driver()
        splash.update_progress(4)

        splash.log("Fetching first thumbnail URL (this may take a while)...")
        thumb_url = get_first_thumbnail(driver, ini_id)
        driver.quit()
        splash.update_progress(5)

        if thumb_url:
            splash.log(f"Downloading thumbnail from: {thumb_url}")
            download_thumbnail(thumb_url, os.path.join(mod_dir, "thumbnail.jpg"))
        else:
            splash.log("No thumbnail found.")

        splash.update_progress(6)
        splash.log("Process complete!")

    except Exception as e:
        splash.log(f"Error: {e}")
        messagebox.showerror("Error", f"Failed to handle mod ID: {e}")


def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    return webdriver.Chrome(options=options)


def get_first_thumbnail(driver, mod_id):
    try:
        url = f"https://gamebanana.com/mods/{mod_id}"
        driver.get(url)
        WebDriverWait(driver, TIMEOUT_DELAY).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#ScreenshotsModule a img"))
        )
        img_element = driver.find_element(By.CSS_SELECTOR, "#ScreenshotsModule a img")
        return img_element.get_attribute('src')
    except Exception as e:
        print(f"Thumbnail error: {e}")
        return None


def download_thumbnail(url, output_path):
    try:
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded thumbnail to: {output_path}")
    except Exception as e:
        print(f"Download failed: {e}")


def make_compatible():
    result = messagebox.askokcancel(message="Please select the folder for this mod.")
    if not result:
        return

    mod_dir = filedialog.askdirectory(initialdir=os.getcwd())

    result = messagebox.askokcancel(message="Please select the data.win patch.")
    if result:
        try:
            win_xdelta = filedialog.askopenfilename(initialdir=mod_dir, filetypes=[("xdelta files", "*.xdelta")])
            if win_xdelta:
                os.rename(win_xdelta, os.path.join(mod_dir, "data.win.xdelta"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename file: {e}")

    result = messagebox.askokcancel(message="Is there an exe patch? If so, please select it.")
    if result:
        try:
            exe_xdelta = filedialog.askopenfilename(initialdir=mod_dir, filetypes=[("xdelta files", "*.xdelta")])
            if exe_xdelta:
                os.rename(exe_xdelta, os.path.join(mod_dir, "exe.xdelta"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename exe patch: {e}")

    ini_id = simpledialog.askstring(title="Mod Conversion Tool", prompt="What is the mod ID for this mod?")
    if not ini_id:
        return

    # Create and show splash on main thread
    splash = LoadingScreen(tk._default_root, total_steps=6)
    splash.grab_set()
    splash.update()  # Force immediate render

    # Define the background thread function
    def threaded_task():
        process_mod(ini_id, mod_dir, splash)
        splash.destroy()
        messagebox.showinfo("Finished", "Mod conversion complete!")

    # Start the background thread
    threading.Thread(target=threaded_task, daemon=True).start()


def is_patch_valid(source_path, patch_path):
    """
    Tests if a patch can be successfully applied to a source file.
    Returns True if valid, False if decoding fails.
    """
    fd, temp_output_path = tempfile.mkstemp()
    os.close(fd)

    try:
        pyxdelta.decode(source_path, patch_path, temp_output_path)
        return True
    except Exception:
        return False
    finally:
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)


def default_mod_values():
    """
    Returns default placeholder values for a mod metadata dictionary.
    """
    return {
        "name": "name",
        "description": "description",
        "video_link": "video_link",
        "author": "author",
        "date_made": "date_made",
        "version": "version",
        "like_count": "like_count",
        "game_version": "game_version",
        "download_count": "download_count",
        "link": "link"
    }


def mod_thumbnail(mod_id):
    """
    Fetches the GameBanana thumbnail URL for a given mod ID using the og:image meta tag.
    """

    class SSLAdapter(HTTPAdapter):
        def __init__(self, ssl_context=None, **kwargs):
            self.ssl_context = ssl_context
            super().__init__(**kwargs)

        def init_poolmanager(self, *args, **kwargs):
            kwargs["ssl_context"] = self.ssl_context
            return super().init_poolmanager(*args, **kwargs)

    context = ssl.create_default_context(cafile=certifi.where())
    session = requests.Session()
    session.mount("https://", SSLAdapter(ssl_context=context))

    url = f"https://gamebanana.com/mods/{mod_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = session.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        thumbnail_tag = soup.find("meta", property="og:image")

        if thumbnail_tag and thumbnail_tag.get("content"):
            print("Thumbnail URL:", thumbnail_tag["content"])
        else:
            print("Thumbnail not found.")
    except Exception as e:
        print(f"Failed to fetch thumbnail: {e}")


def create_faded_image(path, fade_factor=0.3, size=(700, 250)):
    """
    Loads an image, resizes it, and applies a transparency fade.
    Returns a PhotoImage ready for Tkinter use.
    """
    try:
        image = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
        alpha = image.split()[3]
        alpha = alpha.point(lambda p: int(p * fade_factor))
        image.putalpha(alpha)
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Image loading failed: {e}")
        return None


def add_scrolling_background(parent_frame, image_path, canvas_size=(1280, 720), scroll_speed=1):
    """
    Adds a horizontally scrolling background to a given frame.
    Returns the canvas and PhotoImage to retain a reference.
    """
    try:
        # Ensure the image is wide enough to scroll
        image = Image.open(image_path).resize((canvas_size[0] * 2, canvas_size[1]), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        canvas = tk.Canvas(parent_frame, width=canvas_size[0], height=canvas_size[1], highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)

        image_item = canvas.create_image(0, 0, image=photo, anchor="nw")

        def scroll():
            canvas.move(image_item, -scroll_speed, 0)
            x, _ = canvas.coords(image_item)

            if x <= -canvas_size[0]:
                canvas.coords(image_item, 0, 0)

            parent_frame.after(20, scroll)

        scroll()  # Start scrolling animation
        return canvas, photo
    except Exception as e:
        print(f"Failed to load background: {e}")
        return None, None


# ─────────────
# Main UI Classes
# ─────────────

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="grey")
        self.controller = controller

        # ────────────────────────────
        # Title Label
        # ────────────────────────────
        title_label = tk.Label(
            self,
            text="Split Modding Program",
            font=("Arial", 35, "bold"),
            anchor="nw",
            fg="black",
            bg="grey",
            padx=15,
            pady=15
        )
        title_label.place(x=0, y=0)

        # ────────────────────────────
        # Load Banner Images
        # ────────────────────────────
        self.loader_img = create_faded_image(os.path.join(current_dir, "assets", "examplebanner.jpg"))
        self.browser_img = create_faded_image(os.path.join(current_dir, "assets", "banner_dummy.png"))
        self.settings_img = create_faded_image(
            os.path.join(current_dir, "assets", "examplebanner.jpg"),
            size=(300, 400)
        )

        # ────────────────────────────
        # Button Style Defaults
        # ────────────────────────────
        button_font = ("Arial", 20, "bold")
        button_opts = {
            "font": button_font,
            "compound": "center",
            "borderwidth": 0,
            "highlightthickness": 0
        }

        # ────────────────────────────
        # Mod Loader Button
        # ────────────────────────────
        button_loader = tk.Button(
            self,
            image=self.loader_img,
            text="Mod Loader",
            command=lambda: controller.show_frame("ModLoader"),
            **button_opts
        )
        button_loader.place(x=20, y=100)

        # ────────────────────────────
        # Mod Browser Button
        # ────────────────────────────
        button_browser = tk.Button(
            self,
            image=self.browser_img,
            text="Mod Browser",
            # command=lambda: controller.show_frame("ModBrowser")
            command=lambda: messagebox.showinfo(message="This feature has not yet been implemented."),
            **button_opts
        )
        button_browser.place(x=20, y=400)

        # ────────────────────────────
        # Settings Button
        # ────────────────────────────
        button_settings = tk.Button(
            self,
            image=self.settings_img,
            text="Settings",
            command=lambda: controller.show_frame("Settings"),
            **button_opts
        )
        button_settings.place(x=900, y=100)

        # ────────────────────────────
        # Sound Buttons with Custom Handlers
        # ────────────────────────────
        def play_sound_and_switch(frame_name, sound_file):
            """Helper to switch frame and play associated sound."""
            controller.show_frame(frame_name)
            wave_path = os.path.join(current_dir, f"Assets/{sound_file}")
            try:
                wave_obj = sa.WaveObject.from_wave_file(wave_path)
                wave_obj.play()
            except Exception as e:
                print(f"Failed to play sound: {e}")

        # Groovy Button
        button_groovy = tk.Button(
            self,
            text="Groovy",
            command=lambda: play_sound_and_switch("Groovy", "tvtime.wav"),
            **button_opts
        )
        button_groovy.place(x=900, y=500)

        # Glooby Button
        button_glooby = tk.Button(
            self,
            text="Glooby",
            command=lambda: play_sound_and_switch("Glooby", "didntpush.wav"),
            **button_opts
        )
        button_glooby.place(x=1100, y=500)


class ModLoader(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # ────────────────
        # Background Setup
        # ────────────────
        self.bg_canvas = tk.Canvas(self, width=1280, height=720, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        bg_path = os.path.join(current_dir, "assets", "background.jpg")
        self.bg_canvas, self.bg_photo = add_scrolling_background(self, bg_path)

        # ────────────────
        # Config
        # ────────────────
        self.current_page = 0
        self.mods_per_page = 6
        self.thumbnail_size = (400, 250)
        self.mods_path = os.path.join(current_dir, "mods")
        self.mod_data = self.load_mods()

        # ────────────────
        # Title
        # ────────────────
        title_label = tk.Label(
            self,
            text="Mod Loader Page",
            font=("Arial", 35, "bold"),
            fg="black",
            bg="white",
            anchor="nw",
            padx=15,
            pady=15
        )
        title_label.place(x=0, y=0)

        # ────────────────
        # Back Button
        # ────────────────
        back_btn = tk.Button(
            self,
            text="Back",
            font=("Arial", 20),
            command=lambda: controller.show_frame("MainPage")
        )
        back_btn.place(x=1100, y=28)

        # ────────────────
        # Mod Button Grid Container
        # ────────────────
        self.button_frame = tk.Frame(self, bg="white")
        self.button_frame.place(relx=0.5, rely=0.5, anchor="center")

        # ────────────────
        # Navigation Arrows
        # ────────────────
        self.prev_btn = tk.Button(
            self,
            text="←",
            font=("Arial", 20),
            command=self.prev_page
        )
        self.prev_btn.place(x=50, rely=0.95, anchor="sw")

        self.next_btn = tk.Button(
            self,
            text="→",
            font=("Arial", 20),
            command=self.next_page
        )
        self.next_btn.place(x=1230, rely=0.95, anchor="se")

        # ────────────────
        # Load First Page
        # ────────────────
        self.display_mods()

    def load_mods(self):
        """
        Loads mod metadata and thumbnails from the mods folder.
        Looks for a 'mod.ini' file and 'thumbnail.jpg' in each mod subdirectory.
        """
        mods = []

        if not os.path.exists(self.mods_path):
            return mods

        for mod_dir in os.listdir(self.mods_path):
            mod_path = os.path.join(self.mods_path, mod_dir)
            if not os.path.isdir(mod_path):
                continue

            # Find mod.ini recursively
            ini_path = None
            for root, dirs, files in os.walk(mod_path):
                for file in files:
                    if file.lower() == "mod.ini":
                        ini_path = os.path.join(root, file)
                        break
                if ini_path:
                    break

            image_path = os.path.join(mod_path, "thumbnail.jpg")

            # Default mod metadata
            mod_info = {
                "name": "Unknown Mod",
                "description": "",
                "video_link": "",
                "author": "",
                "date_made": "",
                "version": "",
                "like_count": 0,
                "game_version": "",
                "download_count": 0,
                "link": "",
                "image": None
            }

            # Load INI metadata if available
            if ini_path and os.path.exists(ini_path):
                config = configparser.ConfigParser()
                config.optionxform = str  # Preserve case sensitivity
                config.read(ini_path)

                if config.has_section("Mod"):
                    get = lambda key, fallback="": config.get("Mod", key, fallback=fallback)
                    getint = lambda key, fallback=0: int(config.get("Mod", key, fallback=str(fallback)) or fallback)

                    mod_info.update({
                        "name": get("name", "Unknown Mod"),
                        "description": get("description"),
                        "video_link": get("video_link"),
                        "author": get("author"),
                        "date_made": get("date_made"),
                        "version": get("version"),
                        "like_count": getint("like_count"),
                        "game_version": get("game_version"),
                        "download_count": getint("download_count"),
                        "link": get("link"),
                        "mod_path": mod_path
                    })

            # Load thumbnail image
            if os.path.exists(image_path):
                try:
                    img = Image.open(image_path).resize(self.thumbnail_size, Image.LANCZOS)
                    mod_info["image"] = ImageTk.PhotoImage(img)
                except Exception:
                    pass  # Silently skip bad images

            mods.append(mod_info)

        return mods

    def display_mods(self):
        """
        Clears the current mod grid and displays mods for the current page.
        """
        # Clear old buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        self.button_frame.config(width=800, height=500)
        self.button_frame.pack_propagate(False)

        # Get mods for current page
        start = self.current_page * self.mods_per_page
        end = start + self.mods_per_page
        current_mods = self.mod_data[start:end]

        for idx, mod in enumerate(current_mods):
            row = idx // 3
            col = idx % 3

            wrapper = tk.Frame(
                self.button_frame,
                width=490,
                height=480,
                bg=self["bg"],
                highlightthickness=0,
                bd=0
            )
            wrapper.grid(row=row, column=col, padx=20, pady=20)
            wrapper.grid_propagate(False)

            def button_command(selected_mod):
                self.controller.selected_mod = selected_mod
                self.controller.show_frame("ModPage")

            btn = tk.Button(
                wrapper,
                text=mod["name"],
                font=("Arial", 24, "bold"),
                image=mod["image"],
                compound="top",
                wraplength=480,
                relief="raised",
                bd=0,
                bg=wrapper["bg"],
                activebackground=wrapper["bg"],
                command=partial(button_command, mod)
            )
            btn.pack(fill="both", expand=True)

        # Update nav arrows
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")

        total_pages = len(self.mod_data) // self.mods_per_page
        if len(self.mod_data) % self.mods_per_page != 0:
            total_pages += 1

        self.next_btn.config(state="normal" if self.current_page < total_pages - 1 else "disabled")

    def next_page(self):
        """Switch to the next page of mods."""
        self.current_page += 1
        self.display_mods()

    def prev_page(self):
        """Switch to the previous page of mods."""
        self.current_page -= 1
        self.display_mods()


class ModPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # ────────────────
        # Title Label
        # ────────────────
        self.title_label = tk.Label(
            self,
            font=("Arial", 35, "bold"),
            fg="black",
            bg="white",
            anchor="nw",
            padx=15,
            pady=15
        )
        self.title_label.place(x=0, y=0)

        # ────────────────
        # Description Text + Scrollbar
        # ────────────────
        self.scrollbar = Scrollbar(self)
        self.scrollbar.place(x=650, y=255, height=440)

        self.desc = Text(
            self,
            font=("Arial", 15),
            fg="black",
            bg="white",
            padx=15,
            pady=15,
            wrap="word",
            yscrollcommand=self.scrollbar.set
        )
        self.desc.place(x=20, y=250, width=650, height=450)
        self.scrollbar.config(command=self.desc.yview)

        # ────────────────
        # Patch Button
        # ────────────────
        self.patch_btn = tk.Button(
            self,
            text="Patch mod!",
            font=("Arial", 35, "bold"),
            command=self.patch_mod
        )
        self.patch_btn.place(x=1000, y=600)

        # ────────────────
        # Navigation Buttons
        # ────────────────
        self.back_btn = tk.Button(
            self,
            text="Back",
            font=("Arial", 20),
            command=lambda: controller.show_frame("ModLoader")
        )
        self.back_btn.place(x=1150, y=20)

        self.browser_btn = tk.Button(
            self,
            text="Browse files",
            font=("Arial", 20),
            command=self.open_mod_folder
        )
        self.browser_btn.place(x=1150, y=520)

    def open_mod_folder(self):
        """Opens the selected mod folder in the system's file explorer."""
        mod = self.controller.selected_mod
        mod_path = mod.get("mod_path")

        if not mod_path or not os.path.isdir(mod_path):
            print("Invalid mod path.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(mod_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", mod_path])
            else:
                subprocess.Popen(["xdg-open", mod_path])
            print(f"Opened folder: {mod_path}")
        except Exception as e:
            print(f"Failed to open folder: {e}")

    def update_content(self):
        """Updates the text and title label with selected mod info."""
        mod = self.controller.selected_mod
        self.title_label.config(text=mod["name"])
        self.desc.delete("1.0", tk.END)
        self.desc.insert("1.0", mod["description"])

    def patch_mod(self):
        """Applies xdelta patches and assets from the selected mod."""
        mod = self.controller.selected_mod
        mod_path = mod.get("mod_path")

        if not mod_path or not os.path.isdir(mod_path):
            print("Invalid mod path.")
            return

        # ────────────────
        # Load game_dir from split.ini
        # ────────────────
        script_dir = os.path.dirname(os.path.abspath(__file__))
        split_ini_path = os.path.join(script_dir, "split.ini")

        game_dir = None
        if os.path.exists(split_ini_path):
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(split_ini_path)
            if config.has_section("Paths") and config.has_option("Paths", "game_dir"):
                game_dir = config.get("Paths", "game_dir")
                print(f"Loaded game_dir from split.ini: {game_dir}")

        if not game_dir or not os.path.isdir(game_dir):
            print("Invalid or missing game_dir. Cannot patch.")
            return

        # ────────────────
        # Find patch files and targets
        # ────────────────
        xdelta_files = [f for f in os.listdir(mod_path) if f.endswith(".xdelta")]
        input_candidates = [
            f for f in os.listdir(game_dir)
            if f.lower().endswith((".exe", ".win")) and os.path.isfile(os.path.join(game_dir, f))
        ]

        if not xdelta_files or not input_candidates:
            print("No patches or no valid input files found.")
            return

        # ────────────────
        # Determine main EXE file
        # ────────────────
        exe_candidates = [
            f for f in os.listdir(game_dir)
            if f.lower().endswith(".exe") and "unins" not in f.lower() and "setup" not in f.lower()
        ]

        main_exe = None
        for f in exe_candidates:
            if any(f.lower() in x.lower() for x in xdelta_files):
                main_exe = os.path.join(game_dir, f)
                break
        if not main_exe and exe_candidates:
            main_exe = os.path.join(game_dir, exe_candidates[0])

        if not main_exe:
            messagebox.showwarning("Game Not Launched", "No .exe file found in game directory.")
            return

        # ────────────────
        # Backup critical files
        # ────────────────
        backup_files = []
        for file_name in [os.path.basename(main_exe), "data.win"]:
            original_path = os.path.join(game_dir, file_name)
            if os.path.exists(original_path):
                backup_path = original_path + ".bak"
                try:
                    shutil.copy2(original_path, backup_path)
                    backup_files.append((original_path, backup_path))
                    print(f"Backed up {file_name} to {backup_path}")
                except Exception as e:
                    print(f"Failed to back up {file_name}: {e}")
                    messagebox.showerror("Backup Failed", f"Could not back up {file_name}:\n\n{e}")

        # ────────────────
        # Apply patches
        # ────────────────
        patched_any = False
        for xdelta_file in xdelta_files:
            patch_path = os.path.join(mod_path, xdelta_file)

            matched_input = next((f for f in input_candidates if f.lower() in xdelta_file.lower()), None)
            if not matched_input:
                print(f"No matching input for patch: {xdelta_file}")
                continue

            input_path = os.path.join(game_dir, matched_input)

            if not is_patch_valid(input_path, patch_path):
                print(f"Patch invalid: {xdelta_file} for {matched_input}")
                continue

            try:
                fd, temp_output_path = tempfile.mkstemp()
                os.close(fd)
                try:
                    pyxdelta.decode(input_path, patch_path, temp_output_path)
                    shutil.move(temp_output_path, input_path)
                    print(f"Patched {matched_input} with {xdelta_file}")
                    patched_any = True
                except Exception as e:
                    print(f"Failed patch: {e}")
                    if os.path.exists(temp_output_path):
                        os.remove(temp_output_path)
            except Exception as e:
                print(f"Patch error: {e}")

        if not patched_any:
            print("No patches applied.")
        else:
            print("Patching complete.")

        # ────────────────
        # Copy folders like lang/ and sound/
        # ────────────────
        for folder_name in ["lang", "sound"]:
            source_folder = os.path.join(mod_path, folder_name)
            target_folder = os.path.join(game_dir, folder_name)

            if os.path.exists(source_folder):
                try:
                    if os.path.exists(target_folder):
                        shutil.rmtree(target_folder)
                    shutil.copytree(source_folder, target_folder)
                    print(f"Copied {folder_name}/ to game directory.")
                except Exception as e:
                    print(f"Copy failed ({folder_name}): {e}")
                    messagebox.showerror("Copy Failed", f"Could not copy {folder_name}/:\n\n{e}")
            else:
                print(f"No {folder_name}/ folder in mod.")

        # ────────────────
        # Copy presence DLLs if found
        # ────────────────
        for dll_name in ["NekoPresence.dll", "NekoPresence_x64.dll"]:
            src = os.path.join(mod_path, dll_name)
            dst = os.path.join(game_dir, dll_name)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, dst)
                    print(f"Copied {dll_name} to game directory.")
                except Exception as e:
                    print(f"Failed to copy {dll_name}: {e}")
                    messagebox.showerror("Copy Failed", f"Could not copy {dll_name}:\n\n{e}")

        # ────────────────
        # Delete leftover .po translation files
        # ────────────────
        deleted_po_count = 0
        for root, _, files in os.walk(game_dir):
            for file in files:
                if file.endswith(".po"):
                    try:
                        os.remove(os.path.join(root, file))
                        deleted_po_count += 1
                    except Exception as e:
                        print(f"Failed to delete {file}: {e}")
        print(f"Deleted {deleted_po_count} .po file(s).")

        # ────────────────
        # Launch Game
        # ────────────────
        try:
            print(f"Launching: {main_exe}")
            proc = subprocess.Popen([main_exe], cwd=game_dir)
            proc.wait()
            print("Game closed.")
        except Exception as e:
            print(f"Launch failed: {e}")
            messagebox.showerror("Launch Failed", f"Could not launch the game:\n\n{main_exe}\n\nError: {e}")
            return

        # ────────────────
        # Restore backups
        # ────────────────
        for original, backup in backup_files:
            try:
                shutil.move(backup, original)
                print(f"Restored {backup} → {original}")
            except Exception as e:
                print(f"Failed to restore {backup}: {e}")
                messagebox.showerror("Restore Failed", f"Could not restore file:\n\n{backup}\n\nError: {e}")


# class ModBrowser(tk.Frame):
#     def __init__(self, parent, controller):
#         super().__init__(parent, bg="white")
#         self.controller = controller
#         self.api = PyBanana()  # GameBanana API client
#         self.current_page = 0
#         self.mods_per_page = 6
#         self.thumbnail_size = (400, 250)
#         self.mod_images = []  # prevent garbage collection of thumbnails
#
#         # Scrolling background (shared with ModLoader)
#         bg_path = os.path.join(current_dir, "assets", "background.jpg")
#         self.bg_canvas, self.bg_photo = add_scrolling_background(self, bg_path)
#
#         # Title + Back button
#         tk.Label(self,
#                  text="Mod Browser Page",
#                  font=("Arial", 35, "bold"),
#                  fg="black", bg="white",
#                  anchor="nw",
#                  padx=15, pady=15).place(x=0, y=0)
#
#         tk.Button(self,
#                   text="Back",
#                   font=("Arial", 20),
#                   command=lambda: controller.show_frame("MainPage")) \
#             .place(x=1100, y=28)
#
#         # Container for mod cards
#         self.button_frame = tk.Frame(self, bg="white")
#         self.button_frame.place(relx=0.5, rely=0.5, anchor="center")
#
#         # Navigation buttons
#         self.prev_btn = tk.Button(self, text="←", font=("Arial", 20),
#                                   command=self.prev_page)
#         self.prev_btn.place(x=50, rely=0.95, anchor="sw")
#
#         self.next_btn = tk.Button(self, text="→", font=("Arial", 20),
#                                   command=self.next_page)
#         self.next_btn.place(x=1230, rely=0.95, anchor="se")
#
#         # Load mods
#         self.fetch_mods()
#
#     def fetch_mods(self):
#         """Fetch mod data from GameBanana API and store it."""
#         try:
#             results = self.api.search(
#                 query="pizza tower",
#                 model=ModelType.MOD,
#                 order=OrderResult.RELEVANCE,
#                 page=1,
#                 per_page=100
#             )
#
#             self.all_mods = []
#             for mod in results.records:
#                 mod_info = {
#                     "name": mod.name,
#                     "url": mod.url,
#                     "profile_url": getattr(mod, "profile_url", None),
#                     "creator": getattr(mod, "owner_name", "Unknown"),
#                     "posted": str(mod.date),
#                     "description": (mod.description or "")[:100]
#                 }
#
#                 # Try loading a thumbnail if available
#                 try:
#                     if mod_info["profile_url"]:
#                         image_data = requests.get(mod_info["profile_url"], timeout=5).content
#                         img = Image.open(io.BytesIO(image_data)).resize(self.thumbnail_size, Image.LANCZOS)
#                         photo = ImageTk.PhotoImage(img)
#                         mod_info["image"] = photo
#                         self.mod_images.append(photo)  # Store reference
#                     else:
#                         mod_info["image"] = None
#                 except Exception as e:
#                     print(f"Failed to load image: {e}")
#                     mod_info["image"] = None
#
#                 self.all_mods.append(mod_info)
#
#             self.display_mods()
#
#         except Exception as e:
#             print(f"Error fetching mods: {e}")
#             self.all_mods = []
#
#     def display_mods(self):
#         """Displays the current page of mods in a button grid."""
#         for widget in self.button_frame.winfo_children():
#             widget.destroy()
#
#         self.button_frame.config(width=800, height=500)
#         self.button_frame.pack_propagate(False)
#
#         start = self.current_page * self.mods_per_page
#         end = start + self.mods_per_page
#         current_mods = self.all_mods[start:end]
#
#         for idx, mod in enumerate(current_mods):
#             row = idx // 3
#             col = idx % 3
#
#             wrapper = tk.Frame(self.button_frame,
#                                width=490,
#                                height=480,
#                                bg=self["bg"],
#                                highlightthickness=0,
#                                bd=0)
#             wrapper.grid(row=row, column=col, padx=20, pady=20)
#             wrapper.grid_propagate(False)
#
#             btn = tk.Button(wrapper,
#                             text=mod["name"],
#                             font=("Arial", 24, "bold"),
#                             image=mod.get("image"),
#                             compound="top",
#                             wraplength=480,
#                             relief="raised",
#                             bd=0,
#                             bg=wrapper["bg"],
#                             activebackground=wrapper["bg"],
#                             command=lambda name=mod["name"]: print(f"{name} clicked"))
#             btn.pack(fill="both", expand=True)
#
#         total_pages = len(self.all_mods) // self.mods_per_page
#         if len(self.all_mods) % self.mods_per_page:
#             total_pages += 1
#
#         self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
#         self.next_btn.config(state="normal" if self.current_page < total_pages - 1 else "disabled")
#
#     def next_page(self):
#         """Switch to the next page."""
#         self.current_page += 1
#         self.display_mods()
#
#     def prev_page(self):
#         """Switch to the previous page."""
#         self.current_page -= 1
#         self.display_mods()


class Settings(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # Page title
        title_label = tk.Label(self,
                               text="Settings",
                               font=("Arial", 35, "bold"),
                               anchor="nw",
                               fg="black",
                               bg="white",
                               padx=15,
                               pady=15)
        title_label.place(x=0, y=0)

        def find_game_dir():
            """Opens a dialog to select game directory and saves it to split.ini."""
            game_dir = filedialog.askdirectory()
            if not game_dir:
                return

            config = configparser.ConfigParser()
            config.optionxform = str
            config.read("split.ini")

            if not config.has_section("Paths"):
                config.add_section("Paths")

            config.set("Paths", "game_dir", str(game_dir))

            with open("split.ini", "w") as configfile:
                config.write(configfile)

        tk.Button(self,
                  text="Select directory",
                  font=("Arial", 20, "bold"),
                  command=find_game_dir).place(x=300, y=200)

        # NOTE: make_compatible must exist somewhere above this class
        tk.Button(self,
                  text="Convert",
                  font=("Arial", 20, "bold"),
                  command=make_compatible).place(x=800, y=200)

        tk.Button(self,
                  text="Back",
                  font=("Arial", 20),
                  command=lambda: controller.show_frame("MainPage")).place(x=1100, y=28)


class Groovy(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        self.animations = []

        # Load all gifs and create labels, but defer placement to move()
        for num in range(1, 4):
            gif_path = os.path.join(current_dir, f"Assets/tenna{num}.gif")
            gif = Image.open(gif_path)
            frames = [ImageTk.PhotoImage(f.copy().convert("RGBA")) for f in ImageSequence.Iterator(gif)]

            label = tk.Label(self, bg="white", borderwidth=0)
            # Do NOT place here, will place later in move()

            self.animations.append({
                "frames": frames,
                "frame_index": 0,
                "label": label
            })

        # Start animation and movement for each GIF
        for i in range(len(self.animations)):
            self.animate(i)
            self.move(i)  # Call move with proper idx immediately

    def animate(self, idx):
        anim = self.animations[idx]
        frame = anim["frames"][anim["frame_index"]]
        anim["label"].config(image=frame)
        anim["frame_index"] = (anim["frame_index"] + 1) % len(anim["frames"])
        self.after(100, lambda: self.animate(idx))

    def move(self, idx):
        anim = self.animations[idx]
        label = anim["label"]

        width = self.winfo_width()
        height = self.winfo_height()

        # If widget size not ready, try again shortly
        if width <= 100 or height <= 100:
            self.after(100, lambda: self.move(idx))
            return

        max_x = width - 100
        max_y = height - 100

        x = random.randint(0, max_x)
        y = random.randint(0, max_y)

        label.place(x=x, y=y)
        self.after(500, lambda: self.move(idx))


class Glooby(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")
        self.controller = controller

        video_path = os.path.join(current_dir, "Assets", "didntpush.mp4")
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print("Failed to load video.")

        self.label = tk.Label(self, bg="black")
        self.label.pack(expand=True, fill="both")
        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            label_width, label_height = self.label.winfo_width(), self.label.winfo_height()
            img = Image.fromarray(frame).resize((label_width, label_height), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label.imgtk = imgtk
            self.label.config(image=imgtk)
            self.after(33, self.update_frame)
        else:
            self.cap.release()


LOADING_STEPS = [
    "Setting default mod values...",
    "Initializing MainPage...",
    "Initializing ModLoader...",
    "Initializing ModBrowser...",
    "Initializing ModPage...",
    "Initializing Settings...",
    "Initializing Groovy...",
    "Initializing Glooby...",
    "Finalizing setup..."
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.frames = None
        self.withdraw()
        self.title("Split Modding Program")
        self.geometry("1280x720")
        self.resizable(False, False)
        self.selected_mod = None

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

    def initialize_frames(self, splash):
        splash.log("Setting default mod values...")
        default_mod_values()
        splash.update_progress(1)

        self.frames = {}
        for i, F in enumerate((MainPage, ModLoader, ModPage, Settings, Groovy, Glooby), start=2):
            page_name = F.__name__
            splash.log(f"Initializing {page_name}...")
            frame = F(self.container, self)
            self.frames[page_name] = frame
            frame.place(relwidth=1, relheight=1)
            splash.update_progress(i)

        splash.log("Finalizing setup...")
        splash.update_progress(len(LOADING_STEPS))
        self.show_frame("MainPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        if hasattr(frame, 'update_content'):
            frame.update_content()
        frame.tkraise()


if __name__ == "__main__":
    app = App()
    splash = LoadingScreen(app, total_steps=len(LOADING_STEPS))
    app.after(100, lambda: (
        app.initialize_frames(splash),
        splash.destroy(),
        app.deiconify()
    ))
    app.mainloop()
