import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import json

class ImageCombinationApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Image Combination")
        self.images = [None, None, None]
        self.thumbnails = [None, None, None]
        self.image_paths = [None, None, None]

        # Load image paths from file
        self.load_image_paths()

        # Create buttons and thumbnails for image selection
        self.buttons_select_image = []
        self.labels_thumbnails = []
        for i in range(3):
            frame = tk.Frame(self.window)
            frame.pack(pady=10)

            button = tk.Button(frame, text=f"Select Image {i+1}", command=lambda idx=i: self.select_image(idx))
            button.pack(side=tk.LEFT, padx=5)
            self.buttons_select_image.append(button)

            thumbnail = tk.Label(frame)
            thumbnail.pack(side=tk.LEFT)
            self.labels_thumbnails.append(thumbnail)

        # Create a button to combine and display the images
        self.button_combine_images = tk.Button(self.window, text="Combine Images", command=self.display_images)
        self.button_combine_images.pack(pady=10)
        self.display_thumbnails()

        self.window.protocol("WM_DELETE_WINDOW", self.close_app)

    def select_image(self, idx):
        path = filedialog.askopenfilename()
        if path:
            # Load the selected image
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            thumbnail = self.create_thumbnail(image)
            self.images[idx] = image
            self.thumbnails[idx] = thumbnail
            self.image_paths[idx] = path
            self.display_thumbnails()
            self.save_image_paths()

    def create_thumbnail(self, image):
        # Resize the image to a smaller size for thumbnail display
        thumbnail_size = (100, 100)
        image_resized = cv2.resize(image, thumbnail_size)

        # Convert the resized image to PIL format
        image_pil = Image.fromarray(cv2.cvtColor(image_resized, cv2.COLOR_BGRA2RGBA))

        # Create a PhotoImage object from the resized image
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
            # Create a new window for displaying the combined image
            cv2.namedWindow("Combined Image", cv2.WINDOW_NORMAL)
            cv2.imshow("Combined Image", combined_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    def combine_images(self):
        image1 = self.images[0]
        image2 = self.images[1]
        image3 = self.images[2]
        if image1 is None or image2 is None or image3 is None:
            return None
        else:
            # Resize images to match the size of the largest image
            max_height = max(image1.shape[0], image2.shape[0], image3.shape[0])
            max_width = max(image1.shape[1], image2.shape[1], image3.shape[1])
            image1_resized = cv2.resize(image1, (max_width, max_height))
            image2_resized = cv2.resize(image2, (max_width, max_height))
            image3_resized = cv2.resize(image3, (max_width, max_height))

            # Combine the images by overlaying them on top of each other
            combined_image = image1_resized.copy()
            combined_image[image2_resized[:, :, 3] > 0] = image2_resized[image2_resized[:, :, 3] > 0]
            combined_image[image3_resized[:, :, 3] > 0] = image3_resized[image3_resized[:, :, 3] > 0]

            return combined_image

    def save_image_paths(self):
        with open("image_paths.json", "w") as file:
            json.dump(self.image_paths, file)

    def load_image_paths(self):
        try:
            with open("image_paths.json", "r") as file:
                self.image_paths = json.load(file)
                for idx, path in enumerate(self.image_paths):
                    if path:
                        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                        thumbnail = self.create_thumbnail(image)
                        self.images[idx] = image
                        self.thumbnails[idx] = thumbnail
        except FileNotFoundError:
            pass

    def close_app(self):
        self.save_image_paths()
        self.window.destroy()

# Create an instance of the ImageCombinationApp class
app = ImageCombinationApp()

# Start the UI event loop
app.window.mainloop()
