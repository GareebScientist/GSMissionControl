import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np

class VirtualCameraApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Image Combination")
        self.images = [None, None]
        self.thumbnails = [None, None]

        # Create buttons and thumbnails for image selection
        self.buttons_select_image = []
        self.labels_thumbnails = []
        for i in range(2):
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

        self.window.protocol("WM_DELETE_WINDOW", self.close_app)

    def select_image(self, idx):
        path = filedialog.askopenfilename()
        if path:
            # Load the selected image
            image = cv2.imread(path)
            thumbnail = self.create_thumbnail(image)
            self.images[idx] = image
            self.thumbnails[idx] = thumbnail
            self.display_thumbnails()

    def create_thumbnail(self, image):
        # Resize the image to a smaller size for thumbnail display
        thumbnail_size = (100, 100)
        image_resized = cv2.resize(image, thumbnail_size)

        # Convert the resized image to PIL format
        image_pil = Image.fromarray(cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB))

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
            # Display the combined image in a separate window using OpenCV
            cv2.imshow("Combined Image", combined_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    def combine_images(self):
        image1 = self.images[0]
        image2 = self.images[1]
        if image1 is None or image2 is None:
            return None
        else:
            # Resize image2 to match the size of image1
            image2_resized = cv2.resize(image2, (image1.shape[1], image1.shape[0]))

            # Overlay image2 onto image1
            combined_image = cv2.addWeighted(image1, 1, image2_resized, 1, 0)

            return combined_image

    def close_app(self):
        self.window.destroy()

# Create an instance of the VirtualCameraApp class
app = VirtualCameraApp()

# Start the UI event loop
app.window.mainloop()
