mport tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np

from image_processor import ImageProcessor
from game_logic import GameLogic


class App(tk.Tk):
    def _init_(self):
        super()._init_()
        self.title("Spot the Difference")
        self.configure(bg="#2b2b2b")

        self.processor = ImageProcessor()
        self.game = GameLogic()

        # store tk image refs
        self.img_left = None
        self.img_right = None

        self.offset_x = 0
        self.offset_y = 0

        self.setup_ui()

    def setup_ui(self):
        # top buttons
        btn_frame = tk.Frame(self, bg="#2b2b2b", pady=8)
        btn_frame.pack(fill=tk.X, padx=10)

        tk.Button(
            btn_frame, text="Load Image",
            command=self.load_image,
            bg="#4a90d9", fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT, padx=10, pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, text="Reveal All",
            command=self.reveal_all,
            bg="#888888", fg="white",
            font=("Arial", 11),
            relief=tk.FLAT, padx=10, pady=5
        ).pack(side=tk.LEFT, padx=5)

        # status labels
        info_frame = tk.Frame(self, bg="#2b2b2b")
        info_frame.pack(fill=tk.X, padx=10, pady=4)

        self.lbl_remaining = tk.Label(
            info_frame, text="Remaining: -",
            bg="#2b2b2b", fg="yellow",
            font=("Arial", 12)
        )
        self.lbl_remaining.pack(side=tk.LEFT, padx=10)

        self.lbl_mistakes = tk.Label(
            info_frame, text="Mistakes: 0/3",
            bg="#2b2b2b", fg="#ff6b6b",
            font=("Arial", 12)
        )
        self.lbl_mistakes.pack(side=tk.LEFT, padx=10)

        self.lbl_score = tk.Label(
            info_frame, text="Total Found: 0",
            bg="#2b2b2b", fg="#7bed9f",
            font=("Arial", 12)
        )
        self.lbl_score.pack(side=tk.LEFT, padx=10)

        # canvas area - two images side by side
        canvas_frame = tk.Frame(self, bg="#2b2b2b")
        canvas_frame.pack(padx=10, pady=10)

        tk.Label(canvas_frame, text="Original", bg="#2b2b2b", fg="white",
                 font=("Arial", 10)).grid(row=0, column=0, pady=(0, 4))
        tk.Label(canvas_frame, text="Modified (click here!)", bg="#2b2b2b", fg="#4a90d9",
                 font=("Arial", 10)).grid(row=0, column=1, pady=(0, 4))

        self.canvas_orig = tk.Canvas(
            canvas_frame, width=600, height=480,
            bg="#1a1a1a", highlightthickness=1, highlightbackground="#555"
        )
        self.canvas_orig.grid(row=1, column=0, padx=5)

        self.canvas_mod = tk.Canvas(
            canvas_frame, width=600, height=480,
            bg="#1a1a1a", highlightthickness=1, highlightbackground="#4a90d9",
            cursor="crosshair"
        )
        self.canvas_mod.grid(row=1, column=1, padx=5)

        # bind click on modified canvas only
        self.canvas_mod.bind("<Button-1>", self.on_click)

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", ".jpg *.jpeg *.png *.bmp"), ("All", ".*")]
        )
        if not path:
            return

        ok = self.processor.load(path)
        if not ok:
            messagebox.showerror("Error", "Couldn't load that image, try another.")
            return

        self.game.new_round(self.processor.diff_regions)
        self.draw_images()
        self.update_labels()

    def draw_images(self):
        # draw original
        orig_tk = self.cv2_to_tk(self.processor.original)
        self.img_left = orig_tk
        self.canvas_orig.delete("all")

        h, w = self.processor.original.shape[:2]
        ox = (600 - w) // 2
        oy = (480 - h) // 2
        self.canvas_orig.create_image(ox, oy, anchor=tk.NW, image=orig_tk)

        # draw modified
        mod_tk = self.cv2_to_tk(self.processor.modified)
        self.img_right = mod_tk
        self.canvas_mod.delete("all")

        self.offset_x = (600 - w) // 2
        self.offset_y = (480 - h) // 2
        self.canvas_mod.create_image(self.offset_x, self.offset_y, anchor=tk.NW, image=mod_tk)

    def on_click(self, event):
        if not self.game.active:
            return

        # convert canvas click to image coordinates
        img_x = event.x - self.offset_x
        img_y = event.y - self.offset_y

        result = self.game.check_click(img_x, img_y)

        if result == 'found':
            # find which one was just found and draw circle
            for diff in self.game.differences:
                if diff['found'] and not diff.get('drawn'):
                    self.draw_circle(diff, color='red')
                    diff['drawn'] = True

            if self.game.all_found():
                self.update_labels()
                messagebox.showinfo(
                    "Well done!",
                    f"You found all 5 differences!\nMistakes: {self.game.mistakes}\n\nLoad a new image to play again."
                )
            else:
                self.update_labels()

        elif result == 'wrong':
            self.update_labels()

        elif result == 'gameover':
            self.update_labels()
            messagebox.showwarning(
                "Game Over",
                f"Too many mistakes! You found {5 - self.game.remaining()} out of 5.\n\nLoad a new image to try again."
            )

    def reveal_all(self):
        if self.processor.original is None:
            return

        self.game.reveal()

        for diff in self.game.differences:
            if not diff.get('drawn'):
                self.draw_circle(diff, color='blue')
                diff['drawn'] = True

        self.update_labels()

    def draw_circle(self, diff, color='red'):
        # centre of the region
        cx = diff['x'] + diff['w'] // 2
        cy = diff['y'] + diff['h'] // 2
        r = max(30, max(diff['w'], diff['h']) // 2 + 8)

        # convert back to canvas coordinates
        cx_canvas = cx + self.offset_x
        cy_canvas = cy + self.offset_y

        # draw on both canvases
        for canvas in [self.canvas_orig, self.canvas_mod]:
            canvas.create_oval(
                cx_canvas - r, cy_canvas - r,
                cx_canvas + r, cy_canvas + r,
                outline=color, width=3
            )

    def update_labels(self):
        self.lbl_remaining.config(text=f"Remaining: {self.game.remaining()}")
        self.lbl_mistakes.config(text=f"Mistakes: {self.game.mistakes}/3")
        self.lbl_score.config(text=f"Total Found: {self.game.total_found}")

    def cv2_to_tk(self, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        return ImageTk.PhotoImage(pil)
