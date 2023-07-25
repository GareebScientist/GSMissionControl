import socket
import time
import threading
import pytz
from datetime import datetime
import customtkinter

class CountdownThread(threading.Thread):
    def __init__(self, t):
        threading.Thread.__init__(self)
        self.t = t
        self.stop_requested = threading.Event()

    def run(self):
        while self.t > 0 and not self.stop_requested.is_set():  # Countdown phase
            time_str.set(write_time_to_file(self.t, '-'))
            time.sleep(1)
            self.t -= 1

        if not self.stop_requested.is_set():
            time_str.set(write_time_to_file(self.t, '+'))  # The moment of the "launch"
            time.sleep(1)
            self.t += 1

        while not self.stop_requested.is_set():  # Count-up phase
            time_str.set(write_time_to_file(self.t, '+'))
            time.sleep(1)
            self.t += 1

    def join(self, timeout=None):
        self.stop_requested.set()
        threading.Thread.join(self, timeout)

    def increase_time(self, secs):
        self.t += secs

    def decrease_time(self, secs):
        self.t -= secs

    def set_time(self,secs):
        self.t=secs

def write_time_to_file(t, sign):
    mins, secs = divmod(t, 60)
    hours, mins = divmod(mins, 60)
    timeformat = f"{sign}{hours:02d}:{mins:02d}:{secs:02d}"
    with open("counter.txt", "w") as timefile:
        timefile.write(timeformat)
    return timeformat

def toggle_countdown():
    global countdown_thread
    if countdown_thread:
        countdown_thread.join()
        countdown_thread = None
        toggle_button.configure(text="Start Timer")
    else:
        t = 0
        utc_time_str = utc_entry.get()  # Get the entered UTC time
        sec_str = sec_entry.get()

        if utc_time_str:  # If a UTC time was entered
            try:
                utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')  # Parse the string into a datetime object
                utc_time = pytz.utc.localize(utc_time)  # Ensure the datetime object is timezone-aware
                current_time = datetime.now(pytz.utc)  # Get the current time in UTC

                # Calculate the time difference in seconds
                time_diff = utc_time - current_time
                t = time_diff.total_seconds()

                if t < 0:  # If the entered time is in the past, display an error and return
                    time_str.set("Error: Entered time is in the past")
                    return
            except Exception as e:
                print("Error parsing UTC time: ", e)
                if sec_str:
                    t = int(sec_str)
                else:
                    return
        elif sec_str:
            t = int(sec_str)
        else:
            return

        countdown_thread = CountdownThread(int(t))
        countdown_thread.start()
        toggle_button.configure(text="Stop Timer")

<<<<<<< HEAD
def receive_value_from_client():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 12345))
    server_socket.listen(1)

    while True:
        conn, addr = server_socket.accept()
        data = conn.recv(1024)
        if data:
            try:
                # Convert the received data to an integer value and set it as the new timer value
                new_timer_value = int(data.decode())
                countdown_thread.set_time(new_timer_value)
            except ValueError:
                print("Received invalid data from the server.")


root = Tk()
root.geometry("600x500")  # Adjust the window size
=======
customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

root = customtkinter.CTk()
root.geometry("800x400")  # Adjust the window size
>>>>>>> b4b03ed (implementing customtkinter for better ui)
root.title("Rocket Countdown Timer")

time_str = customtkinter.StringVar()
countdown_thread = None

customtkinter.CTkLabel(root, text="Enter UTC time (YYYY-MM-DD HH:MM:SS):", font=("Helvetica", 14)).grid(row=0, column=0, columnspan=5)
utc_entry = customtkinter.CTkEntry(root, font=("Helvetica", 12))
utc_entry.grid(row=1, column=0, columnspan=5,pady=10 ,padx=10)

customtkinter.CTkLabel(root, text="OR Enter seconds:", font=("Helvetica", 14)).grid(row=2, column=0, columnspan=5)
sec_entry = customtkinter.CTkEntry(root, font=("Helvetica", 12))
sec_entry.grid(row=3, column=0, columnspan=5,pady=10 ,padx=10)

toggle_button = customtkinter.CTkButton(root, text="Start Timer", command=toggle_countdown, font=("Helvetica", 14))
toggle_button.grid(row=4, column=0, columnspan=5,pady=10 ,padx=10)

for i in range(1, 6):
    customtkinter.CTkButton(root, text=f"+{i} sec", command=lambda i=i: countdown_thread.increase_time(i) if countdown_thread else None, font=("Helvetica", 14)).grid(row=5, column=i-1,pady=10 ,padx=10)

for i in range(1, 6):
    customtkinter.CTkButton(root, text=f"-{i} sec", command=lambda i=i: countdown_thread.decrease_time(i) if countdown_thread else None, font=("Helvetica", 14)).grid(row=6, column=i-1,pady=10 ,padx=10)

customtkinter.CTkLabel(root, textvariable=time_str, font=("Helvetica", 20)).grid(row=7, column=0, columnspan=5,pady=10 ,padx=10)

client_thread = threading.Thread(target=receive_value_from_client)
client_thread.start()

root.mainloop()
