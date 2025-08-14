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