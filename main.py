# ───────────────────────────────────────────
# Standard Library Imports
# ───────────────────────────────────────────
import configparser  # For reading/writing configuration files (INI format)
import os            # For file path and directory handling
import platform      # To detect OS/platform details (currently unused)
import random        # For generating random values (currently unused)
import shutil        # For file/folder operations like copy, move, delete (currently unused)
import ssl           # For managing secure connections (SSL/TLS)
import subprocess    # To run external commands (currently unused)
import tempfile      # To create and manage temporary files (currently unused)
import threading     # For multi-threaded execution (currently unused)
import sys           # For interacting with the Python runtime and environment
import io            # For stream handling (currently unused)
import atexit        # For registering cleanup functions (currently unused)

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
import certifi       # Provides Mozilla’s CA Bundle for SSL verification
# import cv2           # OpenCV library for image and video processing (currently unused here)
import pyxdelta      # For binary diff/patch operations (currently unused here)
import requests      # HTTP requests handling
# import simpleaudio as sa  # For playing audio files (currently unused here)
from PIL import Image, ImageTk, ImageSequence  # Pillow library for image manipulation
from bs4 import BeautifulSoup  # HTML/XML parser for web scraping (currently unused here)

# ───────────────────────────────────────────
# GameBanana API Import
# ───────────────────────────────────────────
from pybanana.api import PyBanana  # Wrapper for interacting with GameBanana API
from requests.adapters import HTTPAdapter  # Allows configuring HTTP request behavior

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

# Create SSL context with Certifi CA bundle — ensures HTTPS requests are trusted.
context = ssl.create_default_context(cafile=certifi.where())

# api = PyBanana() # Initialises PyBanana (currently commented out — likely not needed yet)

# Get the directory where the executable (PyInstaller bundle) or script is located.
current_dir = getattr(sys, '_MEIPASS', os.path.abspath("."))

# Delay constant for timeouts (in seconds)
TIMEOUT_DELAY = 3

# List for tracking temporary files (currently unused but initialized for later use)
_temp_files = []


def get_exe_dir():
    """
    Return the directory where the executable or script is located.

    - If running as a frozen PyInstaller executable, returns the directory of the .exe.
    - If running as a normal Python script, returns the directory of the .py file.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# Get the executable/script directory path
exe_dir = get_exe_dir()

# Path to the configuration file (split.ini)
ini_path = os.path.join(exe_dir, "split.ini")

# ───────────────────────────────────────────
# Create default config file if it doesn't exist
# ───────────────────────────────────────────
if not os.path.exists(ini_path):
    config = configparser.ConfigParser()
    config["Paths"] = {"game_dir": ""}  # Game installation directory
    config["Toggles"] = {"bg_enabled": "True"}  # Background feature toggle
    with open(ini_path, "w") as configfile:
        config.write(configfile)
    print(f"Created default config at {ini_path}")

# ───────────────────────────────────────────
# Load configuration
# ───────────────────────────────────────────
config = configparser.ConfigParser()
config.read(ini_path)


# ───────────────────────────────────────────
# Debug output of loaded configuration
# ───────────────────────────────────────────
print(f"Config loaded from: {ini_path}")
print(f"Sections found: {config.sections()}")
for section in config.sections():
    print(f"[{section}]")
    for key, value in config.items(section):
        print(f"{key} = {value}")

# Store background toggle setting from config
bg_enabled = config.get("Toggles", "bg_enabled")

# ────────────────
# Utility Functions
# ────────────────

def resource_path(relative_path):
    """
    Get absolute path to a resource, compatible with both development and PyInstaller environments.

    When running as a PyInstaller executable, resources are unpacked to a temporary folder
    referenced by `sys._MEIPASS`. In normal Python execution, uses the current working directory.

    Args:
        relative_path (str): Path to the resource relative to the base path.

    Returns:
        str: Absolute path to the resource.
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller temporary extraction path
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_image_safely(path, size=None, convert_mode="RGBA"):
    """
    Load an image from disk or PyInstaller bundle safely.

    Args:
        path (str): Absolute path to the image file.
        size (tuple[int, int], optional): (width, height) to resize the image to. Defaults to None.
        convert_mode (str, optional): Mode to convert image with Pillow (e.g., "RGBA", "RGB"). Defaults to "RGBA".

    Returns:
        PIL.Image.Image | None: Loaded image object if successful, otherwise None.
    """
    try:
        # Read image data manually to avoid path access issues inside PyInstaller bundles
        with open(path, "rb") as f:
            image_data = f.read()

        image = Image.open(io.BytesIO(image_data))

        # Convert to the requested mode
        if convert_mode:
            image = image.convert(convert_mode)

        # Resize if requested
        if size:
            image = image.resize(size, Image.LANCZOS)

        return image
    except Exception as e:
        print(f"Image loading failed ({path}): {e}")
        return None


@atexit.register
def cleanup_temp_images():
    """
    Delete any temporary images created during runtime.

    This function is automatically registered to run at program exit
    via the `atexit` decorator.
    """
    for f in _temp_files:
        try:
            os.remove(f)
        except:
            # Ignore errors (e.g., file already removed or locked)
            pass


def get_base_path():
    """
    Get the base path of the executable or script.

    Returns:
        str: Path of the directory containing the executable (if PyInstaller)
             or the Python script (if running normally).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)  # Path of compiled .exe
    return os.path.dirname(os.path.abspath(__file__))  # Path of .py script


def get_asset_path(filename):
    """
    Get the absolute path to an asset inside the 'assets' folder.

    Works in both PyInstaller and normal execution environments.

    Args:
        filename (str): Name of the asset file.

    Returns:
        str: Absolute path to the asset.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, 'assets', filename)


# Path to the background image asset
bg_path = get_asset_path('main_class_background.png')


def make_mod_folder():
    """
    Ensure that a 'mods' folder exists in the base directory.

    Creates it if it does not exist.
    """
    base_path = get_base_path()
    mods_path = os.path.join(base_path, "mods")
    os.makedirs(mods_path, exist_ok=True)  # Safe to call multiple times

# Create mods folder at startup
make_mod_folder()


def create_driver():
    """
    Create a headless Selenium Chrome WebDriver instance.

    Returns:
        webdriver.Chrome: Configured Chrome driver.
    """
    options = Options()
    options.add_argument('--headless')     # Run without GUI
    options.add_argument('--disable-gpu')  # Disable GPU acceleration
    return webdriver.Chrome(options=options)


def get_first_thumbnail(driver, mod_id):
    """
    Retrieve the first thumbnail image URL from a GameBanana mod page.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        mod_id (int | str): ID of the mod on GameBanana.

    Returns:
        str | None: URL of the thumbnail image if found, otherwise None.
    """
    try:
        url = f"https://gamebanana.com/mods/{mod_id}"
        driver.get(url)

        # Wait until the screenshot module loads
        WebDriverWait(driver, TIMEOUT_DELAY).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#ScreenshotsModule a img"))
        )

        img_element = driver.find_element(By.CSS_SELECTOR, "#ScreenshotsModule a img")
        return img_element.get_attribute('src')
    except Exception as e:
        print(f"Thumbnail error: {e}")
        return None


def download_thumbnail(url, output_path):
    """
    Download an image from a URL and save it locally.

    Args:
        url (str): Direct link to the image file.
        output_path (str): File path to save the image to.
    """
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
    """
    Interactively guide the user through preparing a mod folder for compatibility.

    This function uses Tkinter dialogs to:
      1. Prompt the user to select a mod folder.
      2. Prompt the user to select and rename a 'data.win' patch file.
      3. Prompt the user to select and rename an executable patch file (if present).
      4. Ask for the mod's ID.
      5. Launch a background process (with a loading splash) to process the mod.

    Uses:
        - filedialog: For selecting directories/files.
        - messagebox: For prompting user confirmations and showing errors.
        - simpledialog: For getting text input from the user.
        - threading: To run `process_mod` without blocking the UI.

    Notes:
        - Requires `LoadingScreen` class and `process_mod` function to be defined elsewhere.
        - This function is intended for a GUI-based environment, not CLI.
    """
    # Step 1: Select mod folder
    result = messagebox.askokcancel(message="Please select the folder for this mod.")
    if not result:
        return
    mod_dir = filedialog.askdirectory(initialdir=os.getcwd())

    # Step 2: Select and rename data.win patch
    result = messagebox.askokcancel(message="Please select the data.win patch.")
    if result:
        try:
            win_xdelta = filedialog.askopenfilename(
                initialdir=mod_dir, filetypes=[("xdelta files", "*.xdelta")]
            )
            if win_xdelta:
                os.rename(win_xdelta, os.path.join(mod_dir, "data.win.xdelta"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename file: {e}")

    # Step 3: Select and rename exe patch
    result = messagebox.askokcancel(message="Is there an exe patch? If so, please select it.")
    if result:
        try:
            exe_xdelta = filedialog.askopenfilename(
                initialdir=mod_dir, filetypes=[("xdelta files", "*.xdelta")]
            )
            if exe_xdelta:
                os.rename(exe_xdelta, os.path.join(mod_dir, "exe.xdelta"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename exe patch: {e}")

    # Step 4: Ask for mod ID
    ini_id = simpledialog.askstring(title="Mod Conversion Tool", prompt="What is the mod ID for this mod?")
    if not ini_id:
        return

    # Step 5: Show splash screen while processing in a background thread
    splash = LoadingScreen(tk._default_root, total_steps=6)
    splash.grab_set()
    splash.update()  # Ensure it renders immediately

    def threaded_task():
        process_mod(ini_id, mod_dir, splash)
        splash.destroy()
        messagebox.showinfo("Finished", "Mod conversion complete!")

    threading.Thread(target=threaded_task, daemon=True).start()


def is_patch_valid(source_path, patch_path):
    """
    Check whether a given xdelta patch can be applied to a source file.

    Args:
        source_path (str): Path to the original file.
        patch_path (str): Path to the xdelta patch file.

    Returns:
        bool: True if patch applies successfully, False if it fails.
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
    Get a dictionary of placeholder/default mod metadata values.

    Returns:
        dict: Default mod metadata keys and placeholder values.
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
    Fetch and print the thumbnail URL for a GameBanana mod.

    Args:
        mod_id (int | str): ID of the mod on GameBanana.

    Notes:
        - Uses a custom SSLAdapter to ensure secure HTTPS requests.
        - Looks for the `og:image` meta tag on the mod page.
        - Prints the result instead of returning it.
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
    Load an image, resize it, and apply a transparency fade.

    Args:
        path (str): Path to the image file.
        fade_factor (float): 0–1 multiplier for alpha channel opacity.
        size (tuple[int, int]): (width, height) to resize the image to.

    Returns:
        ImageTk.PhotoImage | None: Ready-to-use Tkinter-compatible image, or None if loading fails.
    """
    try:
        image = load_image_safely(path, convert_mode="RGBA", size=size)
        if image is None:
            return None
        alpha = image.split()[3]
        alpha = alpha.point(lambda p: int(p * fade_factor))
        image.putalpha(alpha)
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Image loading failed: {e}")
        return None


def add_scrolling_background(parent_frame, image_path, canvas_size=(1280, 720), scroll_speed=1):
    """
    Add a horizontally scrolling background image to a Tkinter frame.

    Args:
        parent_frame (tk.Frame): Parent container for the background canvas.
        image_path (str): Path to the background image.
        canvas_size (tuple[int, int]): Width and height of the canvas.
        scroll_speed (int): Horizontal movement speed (pixels per frame).

    Returns:
        tuple[tk.Canvas, ImageTk.PhotoImage]: Canvas and image reference (to prevent garbage collection).
    """
    try:
        image = load_image_safely(
            image_path,
            size=(canvas_size[0] * 2, canvas_size[1])
        )
        if image is None:
            raise ValueError("Image could not be loaded.")

        photo = ImageTk.PhotoImage(image)

        canvas = tk.Canvas(parent_frame, width=canvas_size[0], height=canvas_size[1], highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)

        image_item = canvas.create_image(0, 0, image=photo, anchor="nw")

        def scroll():
            canvas.move(image_item, -scroll_speed, 0)
            x, _ = canvas.coords(image_item)
            if x <= -canvas_size[0]:
                canvas.coords(image_item, 0, 0)
            parent_frame.after(20, scroll)  # Schedule next frame

        scroll()
        return canvas, photo
    except Exception as e:
        print(f"Failed to load background: {e}")
        return None, None

# ─────────────
# Main UI Classes
# ─────────────

class LoadingScreen(tk.Toplevel):
    """
    A modal popup window displaying a progress bar and log output
    while a long-running operation executes.

    Attributes:
        progress (ttk.Progressbar): Progress bar widget tracking total steps.
        log_text (tk.Text): Read-only text area showing progress messages.

    Args:
        master (tk.Widget): Parent widget or Tk root.
        total_steps (int): Total number of steps for the progress bar.
    """
    def __init__(self, master, total_steps):
        super().__init__(master)
        self.title("Loading Split Modding Program...")
        self.geometry("500x250")
        self.resizable(False, False)

        # Progress bar for step tracking
        self.progress = ttk.Progressbar(self, mode='determinate', maximum=total_steps)
        self.progress.pack(fill='x', padx=20, pady=(20, 10))

        # Text log window for output messages
        self.log_text = tk.Text(
            self,
            height=8,
            state='disabled',
            bg='black',
            fg='lime',
            font=("Courier", 10)
        )
        self.log_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.update_idletasks()

    def log(self, message):
        """
        Append a message to the log text box.

        Args:
            message (str): The message to append.
        """
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.configure(state='disabled')
        self.log_text.yview_moveto(1.0)  # Scroll to bottom
        self.update()

    def update_progress(self, step):
        """
        Update the progress bar to a specific step value.

        Args:
            step (int): Current step number to set the progress bar to.
        """
        self.progress['value'] = step
        self.update_idletasks()


def process_mod(ini_id, mod_dir, splash: LoadingScreen):
    """
    Fetch a GameBanana mod's information, save metadata to mod.ini,
    and download its thumbnail image.

    Args:
        ini_id (str | int): GameBanana mod ID.
        mod_dir (str): Path to the mod's directory.
        splash (LoadingScreen): Instance of the loading screen to update with logs/progress.
    """
    try:
        splash.log("Creating GameBanana API interface...")
        api = PyBanana()
        splash.update_progress(1)

        splash.log(f"Fetching mod profile for ID {ini_id}...")
        mod = api.get_mod_profile(int(ini_id))
        splash.update_progress(2)

        # Extract mod info
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

        # Write metadata to mod.ini
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

        # Fetch first thumbnail via Selenium
        splash.log("Starting browser to fetch thumbnail...")
        driver = create_driver()
        splash.update_progress(4)

        splash.log("Fetching first thumbnail URL (this may take a while)...")
        thumb_url = get_first_thumbnail(driver, ini_id)
        driver.quit()
        splash.update_progress(5)

        # Download thumbnail if found
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


class MainPage(tk.Frame):
    """
    The main menu page of the Split Modding Program.

    Displays navigation buttons and handles the background animation.

    Args:
        parent (tk.Widget): Parent container (usually the root window or a frame container).
        controller: Object responsible for managing frame switching (e.g., a Tkinter app controller).
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Create main widgets
        self.create_widgets()

        # Load animated background if enabled
        self.load_background()

    def create_widgets(self):
        """Create all widgets and buttons for the main menu."""
        self.title_label = tk.Label(
            self,
            text="Split Modding Program",
            font=("Arial", 35, "bold"),
            anchor="nw",
            fg="black",
            bg="white",
            padx=15,
            pady=15
        )
        self.title_label.place(x=0, y=0)

        # Load faded banner images for buttons
        self.loader_img = create_faded_image(resource_path(os.path.join(current_dir, "assets", "placeholder_banner.jpg")))
        self.browser_img = create_faded_image(resource_path(os.path.join(current_dir, "assets", "banner_dummy.png")))
        self.settings_img = create_faded_image(
            resource_path(os.path.join(current_dir, "assets", "placeholder_banner.jpg")),
            size=(300, 400)
        )

        button_font = ("Arial", 20, "bold")
        button_opts = {
            "font": button_font,
            "compound": "center",
            "borderwidth": 0,
            "highlightthickness": 0
        }

        # Navigation buttons
        button_loader = tk.Button(
            self,
            image=self.loader_img,
            text="Mod Loader",
            command=lambda: self.controller.show_frame("ModLoader"),
            **button_opts
        )
        button_loader.place(x=20, y=100)

        button_browser = tk.Button(
            self,
            image=self.browser_img,
            text="Mod Browser",
            command=lambda: tk.messagebox.showinfo(message="This feature has not yet been implemented."),
            **button_opts
        )
        button_browser.place(x=20, y=400)

        button_settings = tk.Button(
            self,
            image=self.settings_img,
            text="Settings",
            command=lambda: self.controller.show_frame("Settings"),
            **button_opts
        )
        button_settings.place(x=900, y=100)

        # Example sound-playing navigation (commented out)
        # def play_sound_and_switch(frame_name, sound_file):
        #     self.controller.show_frame(frame_name)
        #     wave_path = os.path.join(current_dir, f"Assets/{sound_file}")
        #     try:
        #         wave_obj = sa.WaveObject.from_wave_file(wave_path)
        #         wave_obj.play()
        #     except Exception as e:
        #         print(f"Failed to play sound: {e}")

    def load_background(self):
        """
        Load and optionally animate a tiled background image
        depending on configuration settings.
        """
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read("split.ini")

        bg_enabled = config.getboolean("Toggles", "bg_enabled", fallback=True)

        # If a background canvas already exists, remove it
        if hasattr(self, "canvas"):
            try:
                self.canvas.destroy()
            except:
                pass

        if bg_enabled:
            # Create canvas and place it behind widgets
            self.canvas = tk.Canvas(self, width=1280, height=720, highlightthickness=0, bd=0)
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            self.canvas.tk.call('lower', self.canvas._w)

            # Load background image
            bg_path = resource_path(os.path.join('assets', 'main_class_background.png'))
            self.bg_image = load_image_safely(bg_path)
            self.tk_bg = ImageTk.PhotoImage(self.bg_image)
            self.bg_width, self.bg_height = self.bg_image.size

            # Tile image across canvas
            tiles_x = (1280 // self.bg_width) + 3
            tiles_y = (720 // self.bg_height) + 3

            self.bg_items = []
            for row in range(tiles_y):
                for col in range(tiles_x):
                    x = col * self.bg_width
                    y = row * self.bg_height
                    item = self.canvas.create_image(x, y, anchor="nw", image=self.tk_bg)
                    self.bg_items.append(item)

            self.scroll_speed_x = -1.2
            self.scroll_speed_y = -0.7
            self.animate_background()

    def animate_background(self):
        """Animate the tiled background by moving it diagonally."""
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return  # Stop animation if canvas is gone

        # Move each tile
        for item in self.bg_items:
            self.canvas.move(item, self.scroll_speed_x, self.scroll_speed_y)

        # Wrap tiles when they scroll out of view
        for item in self.bg_items:
            x, y = self.canvas.coords(item)
            if x <= -self.bg_width:
                self.canvas.move(item, self.bg_width * ((1280 // self.bg_width) + 2), 0)
            elif x >= 1280:
                self.canvas.move(item, -self.bg_width * ((1280 // self.bg_width) + 2), 0)

            if y <= -self.bg_height:
                self.canvas.move(item, 0, self.bg_height * ((720 // self.bg_height) + 2))
            elif y >= 720:
                self.canvas.move(item, 0, -self.bg_height * ((720 // self.bg_height) + 2))

        self.after(16, self.animate_background)  # ~60 FPS


class ModLoader(tk.Frame):
    """
    A Tkinter Frame that displays a paginated grid of game mods with thumbnails,
    allowing navigation, refresh, and selection of mods.

    Attributes:
        controller (tk.Tk): The parent controller that manages frame switching.
        bg_canvas (tk.Canvas): Canvas widget used to display the scrolling background.
        bg_photo (ImageTk.PhotoImage): Background image reference to prevent garbage collection.
        current_page (int): Index of the current page in the mod grid.
        mods_per_page (int): Number of mods displayed per page.
        thumbnail_size (tuple): Size (width, height) for mod thumbnails.
        mods_path (str): Path to the folder containing mod subdirectories.
        mod_data (list): List of dictionaries storing metadata and images for each mod.
        button_frame (tk.Frame): Container for mod buttons.
        prev_btn (tk.Button): Button to navigate to the previous page.
        next_btn (tk.Button): Button to navigate to the next page.
    """

    def __init__(self, parent, controller):
        """
        Initialize the ModLoader frame.

        Args:
            parent (tk.Widget): The parent widget.
            controller (tk.Tk): The controller that manages switching between frames.
        """
        super().__init__(parent, bg="white")
        self.controller = controller

        def get_mods_path():
            """Return the correct path to the mods folder whether running from .py or .exe"""
            if getattr(sys, 'frozen', False):
                # Running in a compiled exe
                base_path = os.path.dirname(sys.executable)
            else:
                # Running from a .py file
                base_path = os.path.dirname(os.path.abspath(__file__))

            return os.path.join(base_path, "mods")

        # ────────────────
        # Background Setup
        # ────────────────
        self.bg_canvas = tk.Canvas(self, width=1280, height=720, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        bg_path = resource_path(os.path.join(current_dir, "assets", "loader_class_background.jpg"))
        self.bg_canvas, self.bg_photo = add_scrolling_background(self, bg_path)

        # ────────────────
        # Config
        # ────────────────
        self.current_page = 0
        self.mods_per_page = 6
        self.thumbnail_size = (340, 180)
        self.mods_path = get_mods_path()
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

        refresh_btn = tk.Button(
            self,
            text="Refresh",
            font=("Arial", 20),
            command=self.refresh_mods
        )
        refresh_btn.place(x=980, y=28)

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

    def refresh_mods(self):
        """
        Reload mod data from disk and refresh the displayed mods.
        Resets the current page to the first page.
        """
        self.mod_data = self.load_mods()
        self.current_page = 0
        self.display_mods()

    def load_mods(self):
        """
        Load mod metadata and thumbnails from the mods folder.

        Each mod is expected to be a subdirectory containing:
            - A 'mod.ini' file with metadata under a 'Mod' section.
            - A 'thumbnail.jpg' image for display (optional).

        Returns:
            list: A list of dictionaries representing mods, each containing:
                - name (str)
                - description (str)
                - author (str)
                - date_made (str)
                - version (str)
                - like_count (int)
                - game_version (str)
                - download_count (int)
                - link (str)
                - mod_path (str)
                - image (ImageTk.PhotoImage)
                - image_original (PIL.Image)
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
                    original = load_image_safely(os.path.join(image_path),
                                                 size=self.thumbnail_size)
                    mod_info["image"] = ImageTk.PhotoImage(original)
                    mod_info["image_original"] = original
                except Exception as e:
                    print(f"Failed to load thumbnail image: {e}")
                    mod_info["image"] = None
                    mod_info["image_original"] = None
            else:
                original = load_image_safely(resource_path(os.path.join(current_dir, "Assets/default_mod_icon.png")), size=self.thumbnail_size)
                mod_info["image"] = ImageTk.PhotoImage(original)
                mod_info["image_original"] = original

            mods.append(mod_info)

        return mods

    def display_mods(self):
        """
        Clear the current mod grid and display mods for the current page.
        Arranges mods in a 3-column grid with navigation arrow management.
        """
        # Clear old buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        self.button_frame.config(bg=self["bg"])

        # Get mods for current page
        start = self.current_page * self.mods_per_page
        end = start + self.mods_per_page
        current_mods = self.mod_data[start:end]

        # Layout settings
        max_cols = 3
        button_width = 360
        button_height = 240

        for idx, mod in enumerate(current_mods):
            row = idx // max_cols
            col = idx % max_cols

            wrapper = tk.Frame(
                self.button_frame,
                width=button_width,
                height=button_height,
                bg=self["bg"],
                highlightthickness=0,
                bd=0
            )
            wrapper.grid(row=row, column=col)
            wrapper.grid_propagate(False)

            def button_command(selected_mod):
                self.controller.selected_mod = selected_mod
                self.controller.show_frame("ModPage")

            btn = tk.Button(
                wrapper,
                text=mod["name"],
                font=("Arial", 12, "bold"),
                image=mod["image"],
                compound="top",
                wraplength=button_width - 10,
                relief="flat",
                bd=0,
                bg=wrapper["bg"],
                activebackground=wrapper["bg"],
                command=partial(button_command, mod)
            )
            btn.pack(fill="both", expand=True)

        # Navigation arrows
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")

        total_pages = len(self.mod_data) // self.mods_per_page
        if len(self.mod_data) % self.mods_per_page != 0:
            total_pages += 1

        self.next_btn.config(state="normal" if self.current_page < total_pages - 1 else "disabled")

    def next_page(self):
        """
        Advance to the next page of mods and refresh the display.
        Disables the next button if the last page is reached.
        """
        self.current_page += 1
        self.display_mods()

    def prev_page(self):
        """
        Return to the previous page of mods and refresh the display.
        Disables the previous button if the first page is reached.
        """
        self.current_page -= 1
        self.display_mods()


class ModPage(tk.Frame):
    """
    A Tkinter Frame representing a single mod's detailed view and patching interface.

    Attributes:
        controller (tk.Tk): The main application controller managing frame navigation.
        image_size (tuple): Target size (width, height) for displaying mod images.
        title_label (tk.Label): Label for displaying the mod's title.
        desc (tk.Text): Text widget for displaying the mod's description.
        scrollbar (Scrollbar): Scrollbar linked to the description Text widget.
        image (tk.Label): Label for displaying the mod's image.
        info_label (tk.Label): Label showing author, date, downloads, likes, and link.
        patch_btn (tk.Button): Button to patch the mod into the game directory.
        back_btn (tk.Button): Navigation button to return to the previous frame.
        browser_btn (tk.Button): Button to open the mod folder in system explorer.
    """

    def __init__(self, parent, controller):
        """
        Initializes the ModPage frame with labels, buttons, and text areas.

        Args:
            parent (tk.Widget): The parent Tkinter widget.
            controller (tk.Tk): Controller for frame navigation and mod data access.
        """
        super().__init__(parent, bg="white")
        self.controller = controller
        self.image_size = (640, 250)  # Target width and height for mod images

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
        self.scrollbar.place(x=670, y=355, height=340)

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
        self.desc.place(x=20, y=350, width=650, height=350)
        self.scrollbar.config(command=self.desc.yview)

        # Label for displaying mod image
        self.image = tk.Label(self, padx=15, pady=15)
        self.image.place(x=20, y=75)

        # Label showing metadata (author, date, downloads, likes, link)
        self.info_label = tk.Label(
            self,
            text="",
            font=("Arial", 16),
            fg="black",
            bg="white",
            justify="left",
            anchor="nw"
        )
        self.info_label.place(x=700, y=350)

        # ────────────────
        # Patch Button
        # ────────────────
        self.patch_btn = tk.Button(
            self,
            text="Patch mod!",
            font=("Arial", 35, "bold"),
            command=self.patch_mod
        )
        self.patch_btn.place(x=850, y=600)

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
        self.browser_btn.place(x=950, y=20)

    def open_mod_folder(self):
        """
        Opens the selected mod's folder in the system's file explorer.

        Checks if the mod path exists and uses the appropriate system command
        depending on Windows, macOS, or Linux.
        """
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
        """
        Updates the ModPage widgets with the selected mod's information.

        - Sets the title label and description text.
        - Resizes and displays the mod image.
        - Populates metadata such as author, creation date, downloads, likes, and link.
        """
        mod = self.controller.selected_mod
        self.title_label.config(text=mod["name"])
        self.desc.delete("1.0", tk.END)
        self.desc.insert("1.0", mod["description"])

        # Resize mod image to fit nicely
        original_img = mod.get("image_original")
        if original_img:
            resized = original_img.copy().resize(self.image_size, Image.LANCZOS)
            self.mod_img_resized = ImageTk.PhotoImage(resized)
            self.image.config(image=self.mod_img_resized)
        else:
            self.image.config(image="")

        info_text = f"""Author: {mod.get("author", "")}
Date Created: {mod.get("date_made", "")}
Downloads: {mod.get("download_count", 0)}
Likes: {mod.get("like_count", 0)}
Link: {mod.get("link", "")}"""
        self.info_label.config(text=info_text)

    def patch_mod(self):
        """
        Applies xdelta patches, copies mod assets, deletes obsolete files,
        launches the game, and restores backups.

        Steps:
            1. Load game directory from split.ini.
            2. Locate patch files (.xdelta) and target input files.
            3. Backup critical files (main EXE, data.win).
            4. Apply xdelta patches to target files.
            5. Copy folders like 'lang/' and 'sound/'.
            6. Copy presence DLLs if found.
            7. Delete leftover .po translation files.
            8. Launch the game.
            9. Restore backup files.
        """
        mod = self.controller.selected_mod
        mod_path = mod.get("mod_path")

        if not mod_path or not os.path.isdir(mod_path):
            print("Invalid mod path.")
            return

        # --- Load game_dir from split.ini ---
        game_dir = None
        if os.path.exists(ini_path):
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(ini_path)
            if config.has_section("Paths") and config.has_option("Paths", "game_dir"):
                game_dir = config.get("Paths", "game_dir")
                print(f"Loaded game_dir from split.ini: {game_dir}")

        if not game_dir or not os.path.isdir(game_dir):
            print("Invalid or missing game_dir. Cannot patch.")
            return

        # --- Find patch files and targets ---
        xdelta_files = [f for f in os.listdir(mod_path) if f.endswith(".xdelta")]
        input_candidates = [
            f for f in os.listdir(game_dir)
            if f.lower().endswith((".exe", ".win")) and os.path.isfile(os.path.join(game_dir, f))
        ]

        if not xdelta_files or not input_candidates:
            print("No patches or no valid input files found.")
            return

        # --- Determine main EXE file ---
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

        # --- Backup critical files ---
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

        # --- Apply patches ---
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

        # --- Copy folders like lang/ and sound/ ---
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

        # --- Copy presence DLLs if found ---
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

        # --- Delete leftover .po translation files ---
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

        # --- Launch Game ---
        try:
            print(f"Launching: {main_exe}")
            proc = subprocess.Popen([main_exe], cwd=game_dir)
            proc.wait()
            print("Game closed.")
        except Exception as e:
            print(f"Launch failed: {e}")
            messagebox.showerror("Launch Failed", f"Could not launch the game:\n\n{main_exe}\n\nError: {e}")
            return

        # --- Restore backups ---
        for original, backup in backup_files:
            try:
                shutil.move(backup, original)
                print(f"Restored {backup} → {original}")
            except Exception as e:
                print(f"Failed to restore {backup}: {e}")
                messagebox.showerror("Restore Failed", f"Could not restore file:\n\n{backup}\n\nError: {e}")


class Settings(tk.Frame):
    """
    A Tkinter frame representing the settings page of the application.

    Allows users to:
        - Select a game directory.
        - Convert mods using a `make_compatible` function.
        - Toggle the background feature.
        - Navigate to other pages (MainPage, Groovy, Glooby).
    """

    def __init__(self, parent, controller):
        """
        Initialize the Settings frame.

        Args:
            parent (tk.Widget): The parent widget in which this frame is contained.
            controller (App): The main application controller used for frame navigation.
        """
        super().__init__(parent, bg="white")
        self.controller = controller

        # ────────────────
        # Title Label
        # ────────────────
        title_label = tk.Label(
            self,
            text="Settings",
            font=("Arial", 35, "bold"),
            anchor="nw",
            fg="black",
            bg="white",
            padx=15,
            pady=15
        )
        title_label.place(x=0, y=0)

        # ────────────────
        # Background Toggle Function
        # ────────────────
        def toggle_bg():
            """
            Toggle the background feature on/off in the split.ini configuration.
            Reloads the MainPage background immediately.
            """
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read("split.ini")

            current = config.getboolean("Toggles", "bg_enabled", fallback=True)
            config.set("Toggles", "bg_enabled", str(not current))

            with open("split.ini", "w") as f:
                config.write(f)

            # Reload background in MainPage without destroying it
            main_page = self.controller.frames["MainPage"]
            main_page.load_background()

        # ────────────────
        # Game Directory Selection
        # ────────────────
        def find_game_dir():
            """
            Open a directory dialog to select the game directory.
            Updates the 'game_dir' path in split.ini.
            """
            game_dir = filedialog.askdirectory()
            if not game_dir:
                return

            config = configparser.ConfigParser()
            config.optionxform = str
            config.read("split.ini")

            if not config.has_section("Paths"):
                config.add_section("Paths")

            config.set("Paths", "game_dir", game_dir)

            with open("split.ini", "w") as configfile:
                config.write(configfile)

        # ────────────────
        # Buttons
        # ────────────────
        tk.Button(
            self,
            text="Select directory",
            font=("Arial", 20, "bold"),
            command=find_game_dir
        ).place(x=100, y=200)

        # Converts mods (make_compatible must be defined elsewhere)
        tk.Button(
            self,
            text="Convert Mod",
            font=("Arial", 20, "bold"),
            command=make_compatible
        ).place(x=100, y=300)

        # Navigation: Back to MainPage
        tk.Button(
            self,
            text="Back",
            font=("Arial", 20),
            command=lambda: self.controller.show_frame("MainPage")
        ).place(x=1100, y=28)

        # Toggle the background feature
        tk.Button(
            self,
            text="Toggle BG",
            font=("Arial", 20),
            command=toggle_bg
        ).place(x=100, y=400)


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
    """
    The main application class for the Split Modding Program.

    Responsible for:
        - Initializing the main window.
        - Managing all frames/pages.
        - Tracking the selected mod.
        - Displaying the loading screen on startup.
    """

    def __init__(self):
        """
        Initialize the main application window.
        """
        super().__init__()
        self.frames = None
        self.withdraw()  # Hide window until loading is done
        self.title("Split Modding Program")
        self.geometry("1280x720")
        self.resizable(False, False)
        self.selected_mod = None

        # Container for all frames
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

    def initialize_frames(self, splash):
        """
        Initialize and load all application frames.

        Args:
            splash (LoadingScreen): The splash screen object to update progress.
        """
        # Initialize default mod values
        splash.log("Setting default mod values...")
        default_mod_values()
        splash.update_progress(1)

        # Initialize all frames
        self.frames = {}
        for i, F in enumerate((MainPage, ModLoader, ModPage, Settings,
                              # Groovy, Glooby (Currently unused)
                               ), start=2):
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
        """
        Bring the requested frame to the front.

        Args:
            page_name (str): The name of the frame to show.
        """
        frame = self.frames[page_name]
        if hasattr(frame, 'update_content'):
            frame.update_content()
        frame.tkraise()


if __name__ == "__main__":
    app = App() # Initialise the app
    splash = LoadingScreen(app, total_steps=len(LOADING_STEPS)) # Show the loading screen
    app.after(100, lambda: (
        app.initialize_frames(splash),
        splash.destroy(),
        app.deiconify()
    ))
    app.mainloop() # Start the program