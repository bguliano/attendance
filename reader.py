import tkinter as tk
import numpy as np
from PIL import ImageTk, Image
from pyzbar.pyzbar import decode, ZBarSymbol
import cv2
from typing import Callable, Optional
from collections import deque


class Reader:
    def __init__(self, callback: Callable[[str], bool], *,
                 allow_repeats: bool = False,
                 necessary_correct: int = 5,
                 show_camera: bool = False,
                 camera_refresh_rate: int = 100,
                 cv2_camera: int = 1,
                 rotate_image: bool = True,
                 auto_start: bool = True):

        self.callback = callback
        self.allow_repeats = allow_repeats
        self.show_camera = show_camera
        self.camera_refresh_rate = camera_refresh_rate
        self.rotate_image = rotate_image

        self.scanner = cv2.VideoCapture(cv2_camera)
        self.last_scanned_queue = deque([], maxlen=necessary_correct)
        self.last_scanned = None
        self.stop_scanning = False

        self.root: Optional[tk.Tk] = None
        self.label: Optional[tk.Label] = None

        if auto_start:
            self.start_decoding()

    def start_decoding(self):
        if self.show_camera:
            self.root = tk.Tk()
            self.label = tk.Label(self.root)
            self.label.pack()
            self.root.after(self.camera_refresh_rate, self._decode_image)
            self.root.mainloop()
        else:
            while not self.stop_scanning:
                self._decode_image()

    def _parse_and_display(self, image, barcode_objects):
        # Add binding box(es)
        image = np.array(image)
        for barcode_obj in barcode_objects:
            n_points = len(barcode_obj.polygon)
            for i in range(n_points):
                image = cv2.line(image,
                                 barcode_obj.polygon[i],
                                 barcode_obj.polygon[(i + 1) % n_points],
                                 color=(0, 255, 0),
                                 thickness=5)

        # Convert image
        ph = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))

        # Display image
        self.label.configure(image=ph)
        self.label.image = ph

    def _handle_callback(self, code: str):
        if self.callback(code):
            self.stop_scanning = True
            if self.show_camera:
                self.root.destroy()

    def _decode_image(self):
        _, current_image = self.scanner.read()
        current_image = Image.fromarray(cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB))

        decoded_objects = []
        final_i = 0

        if self.rotate_image:
            for i in range(0, 65, 5):
                decoded_objects = decode(current_image.rotate(i), [ZBarSymbol.CODE128])  # Find barcodes
                if len(decoded_objects) > 0:
                    final_i = i
                    break
        else:
            decoded_objects = decode(current_image, [ZBarSymbol.CODE128])

        for obj in decoded_objects:
            self.last_scanned_queue.append(obj.data.decode("utf-8"))

        if self.show_camera:
            self._parse_and_display(current_image.rotate(final_i), decoded_objects)

        if len(set(self.last_scanned_queue)) == 1:  # If all of the last scanned codes are the same
            scanned_code = self.last_scanned_queue[0]

            if not self.allow_repeats:  # Prevent the same code from being scanned twice
                if not scanned_code == self.last_scanned:
                    self._handle_callback(scanned_code)
                    self.last_scanned = scanned_code
            else:
                self._handle_callback(scanned_code)

            self.last_scanned_queue.clear()

        if self.show_camera and not self.stop_scanning:
            self.root.after(self.camera_refresh_rate, self._decode_image)
