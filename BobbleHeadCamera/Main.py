import cv2
import pyvirtualcam
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog


class VirtualCameraApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Image as Virtual Camera")
        self.virtual_cam = None
        self.image = None
        self.camera_on = False
        self.ui_initialized = False

        # Create a button to select the image
        self.button_select_image = tk.Button(self.window, text="Select Image", command=self.select_image)
        self.button_select_image.pack(pady=10)

        # Create a button to start/stop the virtual camera
        self.button_start_camera = tk.Button(self.window, text="Start Camera", command=self.toggle_camera)
        self.button_start_camera.pack(pady=10)

        # Create a label for the camera status indicator
        self.label_status = tk.Label(self.window, text="Camera OFF", fg="red")
        self.label_status.pack(pady=10)

        # Create a label to display the image
        self.label_image = tk.Label(self.window)
        self.label_image.pack()

        self.window.protocol("WM_DELETE_WINDOW", self.close_app)

    def initialize_ui(self):
        self.ui_initialized = True

    def select_image(self):
        path = filedialog.askopenfilename()
        if path:
            # Load the selected image
            self.image = cv2.imread(path)
            # Display the image in the UI
            self.display_image(self.image)

    def display_image(self, image):
        # Convert the OpenCV image to PIL format
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        # Resize the image to fit the UI window
        image = image.resize((640, 480))
        # Create a PhotoImage object to display in the UI
        photo = ImageTk.PhotoImage(image)
        self.label_image.config(image=photo)
        self.label_image.image = photo  # Keep a reference to prevent garbage collection

    def toggle_camera(self):
        if not self.camera_on:
            if self.image is not None:
                self.start_camera()
                self.button_start_camera.config(text="Stop Camera")
                self.label_status.config(text="Camera ON", fg="green")
            else:
                tk.messagebox.showerror("Error", "Please select an image first.")
        else:
            self.stop_camera()
            self.button_start_camera.config(text="Start Camera")
            self.label_status.config(text="Camera OFF", fg="red")

    def start_camera(self):
        if not self.ui_initialized:
            self.initialize_ui()

        self.virtual_cam = pyvirtualcam.Camera(width=self.image.shape[1], height=self.image.shape[0], fps=30)
        self.camera_on = True
        self.window.after(0, self.stream_image)

    def stop_camera(self):
        self.camera_on = False
        if self.virtual_cam is not None:
            self.virtual_cam.close()

    def stream_image(self):
        if self.camera_on:
            # Send the image to the virtual camera
            self.virtual_cam.send(self.image)
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
