import configparser
import os
import tkinter as tk
from io import BytesIO

import requests
from PIL import Image, ImageTk
from pybanana.api import PyBanana
from pybanana.enums import ModelType, OrderResult

current_dir = os.path.dirname(os.path.abspath(__file__))


def create_faded_image(path, fade_factor=0.3, size=(700, 250)):
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
    try:
        # Load and resize the image (must be at least twice as wide as canvas)
        image = Image.open(image_path).resize((canvas_size[0] * 2, canvas_size[1]), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        # Create a canvas and add it to the frame
        canvas = tk.Canvas(parent_frame, width=canvas_size[0], height=canvas_size[1], highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)

        image_item = canvas.create_image(0, 0, image=photo, anchor="nw")

        def scroll():
            canvas.move(image_item, -scroll_speed, 0)
            x, y = canvas.coords(image_item)

            if x <= -canvas_size[0]:
                canvas.coords(image_item, 0, 0)

            parent_frame.after(20, scroll)

        scroll()  # Start scrolling
        return canvas, photo  # Return to keep a reference and allow `.lift()` later

    except Exception as e:
        print(f"Failed to load background: {e}")
        return None, None


class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="grey")
        self.controller = controller

        # Title label
        title_label = tk.Label(self,
                               text="Split Modding Program",
                               font=("Arial", 35, "bold"),
                               anchor="nw",
                               fg="black",
                               bg="grey",
                               padx=15,
                               pady=15)
        title_label.place(x=0, y=0)

        # Load images
        self.loader_img = create_faded_image(os.path.join(current_dir, "assets", "examplebanner.jpg"))
        self.browser_img = create_faded_image(os.path.join(current_dir, "assets", "examplebanner.jpg"))
        self.settings_img = create_faded_image(os.path.join(current_dir, "assets", "examplebanner3.jpg"),
                                               size=(300, 400))

        # Mod Loader button
        button_loader = tk.Button(self,
                                  image=self.loader_img,
                                  text="Mod Loader",
                                  font=("Arial", 20, "bold"),
                                  compound="center",
                                  borderwidth=0,
                                  highlightthickness=0,
                                  command=lambda: controller.show_frame("ModLoader"))
        button_loader.place(x=20, y=100)

        # Mod Browser button
        button_browser = tk.Button(self,
                                   image=self.browser_img,
                                   text="Mod Browser",
                                   font=("Arial", 20, "bold"),
                                   compound="center",
                                   borderwidth=0,
                                   highlightthickness=0,
                                   command=lambda: controller.show_frame("ModBrowser"))
        button_browser.place(x=20, y=400)

        # Settings button
        button_settings = tk.Button(self,
                                    image=self.settings_img,
                                    text="Settings",
                                    font=("Arial", 20, "bold"),
                                    compound="center",
                                    borderwidth=0,
                                    highlightthickness=0)
        button_settings.place(x=900, y=100)


class ModLoader(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # Load and set up the scrolling background
        self.bg_canvas = tk.Canvas(self, width=1280, height=720, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        bg_path = os.path.join(current_dir, "assets", "background.jpg")
        self.bg_canvas, self.bg_photo = add_scrolling_background(self, bg_path)

        self.current_page = 0
        self.mods_per_page = 6
        self.thumbnail_size = (400, 250)

        self.mods_path = os.path.join(current_dir, "mods")
        self.mod_data = self.load_mods()

        # Title
        title_label = tk.Label(self,
                               text="Mod Loader Page",
                               font=("Arial", 35, "bold"),
                               fg="black",
                               bg="white",
                               anchor="nw",
                               padx=15,
                               pady=15)
        title_label.place(x=0, y=0)

        # Back button
        back_btn = tk.Button(self,
                             text="Back",
                             font=("Arial", 20),
                             command=lambda: controller.show_frame("MainPage"))
        back_btn.place(x=1100, y=28)

        # Mod buttons container
        self.button_frame = tk.Frame(self, bg="white")
        self.button_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Navigation arrows
        self.prev_btn = tk.Button(self,
                                  text="←",
                                  font=("Arial", 20),
                                  command=self.prev_page)
        self.prev_btn.place(x=50, rely=0.95, anchor="sw")

        self.next_btn = tk.Button(self,
                                  text="→",
                                  font=("Arial", 20),
                                  command=self.next_page)
        self.next_btn.place(x=1230, rely=0.95, anchor="se")

        # Load first page
        self.display_mods()

    def load_mods(self):
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

            # Default values
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

            if ini_path and os.path.exists(ini_path):
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(ini_path)

                if config.has_section("Mod"):
                    get = lambda key, fallback="": config.get("Mod", key, fallback=fallback)
                    getint = lambda key, fallback=0: config.getint("Mod", key, fallback=fallback)

                    mod_info["name"] = get("name")
                    mod_info["description"] = get("description")
                    mod_info["video_link"] = get("video_link")
                    mod_info["author"] = get("author")
                    mod_info["date_made"] = get("date_made")
                    mod_info["version"] = get("version")
                    mod_info["like_count"] = getint("like_count")
                    mod_info["game_version"] = get("game_version")
                    mod_info["download_count"] = getint("download_count")
                    mod_info["link"] = get("link")

            # Load the thumbnail image
            if os.path.exists(image_path):
                try:
                    img = Image.open(image_path).resize(self.thumbnail_size, Image.LANCZOS)
                    mod_info["image"] = ImageTk.PhotoImage(img)
                except Exception:
                    pass  # Silently ignore image load errors

            mods.append(mod_info)

        return mods

    def display_mods(self):
        # Clear previous widgets
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Ensure self.button_frame has a fixed size
        self.button_frame.config(width=800, height=500)
        self.button_frame.pack_propagate(False)

        start = self.current_page * self.mods_per_page
        end = start + self.mods_per_page
        current_mods = self.mod_data[start:end]

        for idx, mod in enumerate(current_mods):
            row = idx // 3  # Only 2 buttons per row now due to bigger size
            col = idx % 3

            wrapper = tk.Frame(self.button_frame,
                               width=490,
                               height=480,
                               bg=self["bg"],  # Match parent background (white or canvas bg)
                               highlightthickness=0,
                               bd=0)

            wrapper.grid(row=row, column=col, padx=20, pady=20)
            wrapper.grid_propagate(False)

            btn = tk.Button(wrapper,
                            text=mod["name"],
                            font=("Arial", 24, "bold"),  # Slightly larger font looks better
                            image=mod["image"],
                            compound="top",
                            wraplength=480,  # Almost full width
                            relief="raised",
                            bd=0,
                            bg=wrapper["bg"],
                            activebackground=wrapper["bg"],
                            command=lambda name=mod["name"]: print(f"{name} clicked"))

            btn.pack(fill="both", expand=True)

        # Update navigation arrows
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
        total_pages = len(self.mod_data) // self.mods_per_page
        if len(self.mod_data) % self.mods_per_page != 0:
            total_pages += 1
        self.next_btn.config(state="normal" if self.current_page < total_pages - 1 else "disabled")

    def next_page(self):
        self.current_page += 1
        self.display_mods()

    def prev_page(self):
        self.current_page -= 1
        self.display_mods()


class ModBrowser(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller
        self.api = PyBanana()  # your online API client
        self.current_page = 0
        self.mods_per_page = 6
        self.thumbnail_size = (400, 250)
        self.mod_images = []  # keep refs so they don’t get GC’d

        # scrolling background (same as in ModLoader)
        bg_path = os.path.join(current_dir, "assets", "background.jpg")
        self.bg_canvas, self.bg_photo = add_scrolling_background(self, bg_path)

        # title + back button
        tk.Label(self,
                 text="Mod Browser Page",
                 font=("Arial", 35, "bold"),
                 fg="black", bg="white",
                 anchor="nw",
                 padx=15, pady=15).place(x=0, y=0)

        tk.Button(self,
                  text="Back",
                  font=("Arial", 20),
                  command=lambda: controller.show_frame("MainPage")) \
            .place(x=1100, y=28)

        # where the cards live
        self.button_frame = tk.Frame(self, bg="white")
        self.button_frame.place(relx=0.5, rely=0.5, anchor="center")

        # paging arrows
        self.prev_btn = tk.Button(self, text="←", font=("Arial", 20),
                                  command=self.prev_page)
        self.prev_btn.place(x=50, rely=0.95, anchor="sw")

        self.next_btn = tk.Button(self, text="→", font=("Arial", 20),
                                  command=self.next_page)
        self.next_btn.place(x=1230, rely=0.95, anchor="se")

        # pull down everything from the API once
        self.fetch_and_display_mods()

    def fetch_and_display_mods(self):
        try:
            # fetch a big page of results (up to your API limits)
            results = self.api.search(
                query="pizza tower",
                model=ModelType.MOD,
                order=OrderResult.RELEVANCE,
                page=1,
                per_page=100
            )
            self.all_mods = results.records
            self.display_mods()
        except Exception as e:
            print(f"Error fetching mods: {e}")

    def display_mods(self):
        # clear old cards
        for w in self.button_frame.winfo_children():
            w.destroy()

        # fix the container size
        self.button_frame.config(width=800, height=500)
        self.button_frame.pack_propagate(False)

        start = self.current_page * self.mods_per_page
        end = start + self.mods_per_page
        for idx, mod in enumerate(self.all_mods[start:end]):
            name = getattr(mod, "name", "Unknown Mod")
            img_url = (
                    getattr(mod, "preview_image_url", None)
                    or getattr(mod, "thumbnail_url", None)
            )
            link = getattr(mod, "url", None)

            thumb = None
            if img_url:
                try:
                    resp = requests.get(img_url)
                    resp.raise_for_status()
                    img = Image.open(BytesIO(resp.content)) \
                        .resize(self.thumbnail_size, Image.LANCZOS)
                    thumb = ImageTk.PhotoImage(img)
                    self.mod_images.append(thumb)  # prevent GC
                except Exception as e:
                    print(f"[ModBrowser] failed to load {name!r} thumbnail:", e)

            # each “card” frame
            row, col = divmod(idx, 3)
            card = tk.Frame(self.button_frame,
                            width=490, height=480,
                            bg="white", bd=0,
                            highlightthickness=1,
                            highlightbackground="grey")
            card.grid(row=row, column=col, padx=20, pady=20)
            card.grid_propagate(False)

            btn = tk.Button(card,
                            text=name,
                            image=thumb,  # now uses the real thumbnail
                            compound="top",
                            font=("Arial", 24, "bold"),
                            wraplength=480,
                            bd=0,
                            bg="white",
                            activebackground="white",
                            relief="raised",
                            command=lambda url=link: print(f"Open mod: {url}"))
            btn.pack(fill="both", expand=True)

        # update arrow button states
        total = len(self.all_mods)
        last_page = (total - 1) // self.mods_per_page
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.config(state="normal" if self.current_page < last_page else "disabled")

    def next_page(self):
        self.current_page += 1
        self.display_mods()

    def prev_page(self):
        self.current_page -= 1
        self.display_mods()


class Settings(tk.Frame):
    # This makes the frame
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        # Frame contents
        title_label = tk.Label(self,
                               text="Settings",
                               font=("Arial", 35, "bold"),
                               anchor="nw",
                               fg="black",
                               bg="white",
                               padx=15,
                               pady=15)
        title_label.place(x=0, y=0)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Split Modding Program")
        self.geometry("1280x720")
        self.resizable(False, False)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (MainPage, ModLoader, ModBrowser):
            page_name = F.__name__
            frame = F(container, self)
            self.frames[page_name] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("MainPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()


if __name__ == "__main__":
    app = App()
    app.mainloop()
