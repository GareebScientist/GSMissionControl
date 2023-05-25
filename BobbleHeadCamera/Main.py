import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import json
import pyaudio
import audioop
import math
import threading
import pygame


class ImageCombinationApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Image Combination")
        self.images = [None, None, None]
        self.thumbnails = [None, None, None]
        self.image_paths = [None, None, None]
        self.microphone_inputs = ["Select Microphone"]
        self.microphone_variable = tk.StringVar(self.window, self.microphone_inputs[0])
        self.processing = False
        self.stream = None
        self.image2_position = 0

        self.load_image_paths()

        self.buttons_select_image = []
        self.labels_thumbnails = []
        for i in range(3):
            frame = tk.Frame(self.window)
            frame.pack(pady=10)

            button = tk.Button(frame, text=f"Select Image {i + 1}", command=lambda idx=i: self.select_image(idx))
            button.pack(side=tk.LEFT, padx=5)
            self.buttons_select_image.append(button)

            thumbnail = tk.Label(frame)
            thumbnail.pack(side=tk.LEFT)
            self.labels_thumbnails.append(thumbnail)

        self.button_combine_images = tk.Button(self.window, text="Combine Images", command=self.display_images)
        self.button_combine_images.pack(pady=10)

        self.get_microphone_inputs()

        self.microphone_dropdown = tk.OptionMenu(self.window, self.microphone_variable, *self.microphone_inputs,
                                                 command=self.start_audio_processing)
        self.microphone_dropdown.pack(pady=10)

        self.gradient_canvas = tk.Canvas(self.window, width=200, height=20)
        self.gradient_canvas.pack(pady=10)
        self.gradient_bar = self.gradient_canvas.create_rectangle(0, 0, 0, 20, fill='green')

        self.display_thumbnails()

        self.window.protocol("WM_DELETE_WINDOW", self.close_app)

    def get_microphone_inputs(self):
        audio = pyaudio.PyAudio()
        info = audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        for i in range(0, num_devices):
            device_info = audio.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                self.microphone_inputs.append(device_info['name'])

    def select_image(self, idx):
        path = filedialog.askopenfilename()
        if path:
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            thumbnail = self.create_thumbnail(image)
            self.images[idx] = image
            self.thumbnails[idx] = thumbnail
            self.image_paths[idx] = path
            self.display_thumbnails()
            self.save_image_paths()

    def create_thumbnail(self, image):
        thumbnail_size = (100, 100)
        image_resized = cv2.resize(image, thumbnail_size)
        image_pil = Image.fromarray(cv2.cvtColor(image_resized, cv2.COLOR_BGRA2RGBA))
        thumbnail = ImageTk.PhotoImage(image_pil)
        return thumbnail

    def display_thumbnails(self):
        for i, thumbnail in enumerate(self.thumbnails):
            if thumbnail is not None:
                self.labels_thumbnails[i].config(image=thumbnail)
                self.labels_thumbnails[i].image = thumbnail

    def display_images(self):
        combined_image = self.combine_images()
        if combined_image is not None:
            pygame_thread = threading.Thread(target=self.display_pygame_window, args=(combined_image,))
            pygame_thread.start()

    def combine_images(self):
        if all(image is not None for image in self.images):
            max_height = max(image.shape[0] for image in self.images)
            max_width = max(image.shape[1] for image in self.images)
            combined_image = np.zeros((max_height, max_width, 4), dtype=np.uint8)
            for image in self.images:
                if image.shape[0] != max_height or image.shape[1] != max_width:
                    image = cv2.resize(image, (max_width, max_height))
                combined_image[image[:, :, 3] > 0] = image[image[:, :, 3] > 0]
            return combined_image

    def display_pygame_window(self, combined_image):
        pygame.init()

        max_height, max_width, _ = combined_image.shape
        window = pygame.display.set_mode((max_width, max_height))

        surfaces = []
        for image in self.images:
            if image is not None:
                if image.shape[0] != max_height or image.shape[1] != max_width:
                    image = cv2.resize(image, (max_width, max_height))
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                surface = pygame.image.fromstring(image.tobytes(), image.shape[1::-1], 'RGBA')
                surface = pygame.Surface.convert_alpha(surface)
                surfaces.append(surface)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            window.fill((0, 0, 0))

            for i, surface in enumerate(surfaces):
                position = (0, 0)
                if i == 1:
                    position = (0, self.image2_position)  # Adjust the position of image 2

                window.blit(surface, position)

            pygame.display.flip()

        pygame.quit()

    def load_image_paths(self):
        try:
            with open("paths.json", "r") as f:
                paths = json.load(f)
                for i, path in enumerate(paths):
                    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                    thumbnail = self.create_thumbnail(image)
                    self.images[i] = image
                    self.thumbnails[i] = thumbnail
                    self.image_paths[i] = path
        except FileNotFoundError:
            pass

    def save_image_paths(self):
        with open("paths.json", "w") as f:
            json.dump(self.image_paths, f)

    def start_audio_processing(self, microphone_name):
        if microphone_name != "Select Microphone":
            selected_microphone_index = self.microphone_inputs.index(microphone_name) - 1
            self.stop_audio_processing()
            audio_thread = threading.Thread(target=self.audio_processing, args=(selected_microphone_index,),
                                            daemon=True)
            audio_thread.start()

    def audio_processing(self, selected_microphone_index):
        audio = pyaudio.PyAudio()
        self.stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True,
                                 input_device_index=selected_microphone_index, frames_per_buffer=1024)
        self.processing = True
        while self.processing:
            data = self.stream.read(1024)
            rms = audioop.rms(data, 2)  # measure of the power level
            rms = max(min(int(math.log(rms, 3) * 6), 100), 0)

            # Update the width of the gradient bar
            self.gradient_canvas.coords(self.gradient_bar, 0, 0, rms * 2, 20)  # Multiplied by 2 to get visible change

            # Update the position of image 2 based on the rms value
            self.image2_position = rms

    def stop_audio_processing(self):
        if self.stream is not None:
            self.processing = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def close_app(self):
        self.stop_audio_processing()
        self.window.destroy()


if __name__ == "__main__":
    app = ImageCombinationApp()
    app.window.mainloop()
