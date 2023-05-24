import cv2
import pyvirtualcam
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog
import numpy as np

class VirtualCameraApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Image as Virtual Camera")
        self.virtual_cam = None
        self.images = [None, None]
        self.camera_on = False
        self.ui_initialized = False

        # Create buttons to select images
        self.buttons_select_image = []
        for i in range(2):
            button = tk.Button(self.window, text=f"Select Image {i+1}", command=lambda idx=i: self.select_image(idx))
            button.pack(pady=10)
            self.buttons_select_image.append(button)

        # Create a button to start/stop the virtual camera
        self.button_start_camera = tk.Button(self.window, text="Start Camera", command=self.toggle_camera)
        self.button_start_camera.pack(pady=10)

        # Create a label for the camera status indicator
        self.label_status = tk.Label(self.window, text="Camera OFF", fg="red")
        self.label_status.pack(pady=10)

        # Create a label to display the images
        self.label_images = tk.Label(self.window)
        self.label_images.pack()

        self.window.protocol("WM_DELETE_WINDOW", self.close_app)

    def initialize_ui(self):
        self.ui_initialized = True

    def select_image(self, idx):
        path = filedialog.askopenfilename()
        if path:
            # Load the selected image
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if image.shape[2] == 3:  # Convert RGB image to RGBA
                alpha_channel = 255 * (image[:, :, 3] > 0).astype(image.dtype)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
                image[:, :, 3] = alpha_channel
            self.images[idx] = image
            # Display the images in the UI
            self.display_images()

    def display_images(self):
        combined_image = self.combine_images()
        if combined_image is not None:
            # Convert the combined image to PIL format
            combined_image = Image.fromarray(combined_image)
            # Resize the image to fit the UI window
            combined_image = combined_image.resize((640, 480))
            # Create a PhotoImage object to display in the UI
            photo = ImageTk.PhotoImage(combined_image)
            self.label_images.config(image=photo)
            self.label_images.image = photo  # Keep a reference to prevent garbage collection

    def combine_images(self):
        image1 = self.images[0]
        image2 = self.images[1]
        if image1 is None and image2 is None:
            return None
        elif image1 is None:
            return image2
        elif image2 is None:
            return image1
        else:
            # Resize both images to a fixed size
            image1_resized = cv2.resize(image1, (640, 480))
            image2_resized = cv2.resize(image2, (640, 480))

            # Convert image2_resized to RGBA color space
            if image2_resized.shape[2] == 3:
                image2_resized = cv2.cvtColor(image2_resized, cv2.COLOR_RGB2RGBA)

            # Overlay image2_resized onto image1_resized
            overlay_alpha = image2_resized[:, :, 3] / 255.0
            overlay_alpha = overlay_alpha[:, :, np.newaxis]  # Add a new axis for broadcasting
            overlay = (1 - overlay_alpha) * image1_resized + overlay_alpha * image2_resized

            # Remove the alpha channel from the overlay image
            overlay = overlay[:, :, :3]

            return overlay.astype(np.uint8)


    def toggle_camera(self):
        if not self.camera_on:
            if any(image is not None for image in self.images):
                self.start_camera()
                self.button_start_camera.config(text="Stop Camera")
                self.label_status.config(text="Camera ON", fg="green")
            else:
                tk.messagebox.showerror("Error", "Please select at least one image.")
        else:
            self.stop_camera()
            self.button_start_camera.config(text="Start Camera")
            self.label_status.config(text="Camera OFF", fg="red")

    def start_camera(self):
        if not self.ui_initialized:
            self.initialize_ui()

        self.virtual_cam = pyvirtualcam.Camera(width=640, height=480, fps=30)
        self.camera_on = True
        self.window.after(0, self.stream_image)

    def stop_camera(self):
        self.camera_on = False
        if self.virtual_cam is not None:
            self.virtual_cam.close()

    def stream_image(self):
        if self.camera_on:
            combined_image = self.combine_images()
            if combined_image is not None:
                # Send the combined image to the virtual camera
                self.virtual_cam.send(combined_image)
            # Wait for the next frame
            self.virtual_cam.sleep_until_next_frame()
            self.window.after(1, self.stream_image)

    def close_app(self):
        self.stop_camera()
        self.window.destroy()


# Create an instance of the VirtualCameraApp class
app = VirtualCameraApp()

# Start the UI event loop
app.window.mainloop()
