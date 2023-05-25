import time
import threading
from tkinter import Tk, Label, Entry, Button, StringVar

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
        toggle_button.config(text="Start Timer")
    else:
        t = int(entry.get())
        countdown_thread = CountdownThread(t)
        countdown_thread.start()
        toggle_button.config(text="Stop Timer")

root = Tk()
root.geometry("300x150")  # Adjust the window size
root.title("Rocket Countdown Timer")

time_str = StringVar()
countdown_thread = None

Label(root, text="Enter seconds:", font=("Helvetica", 16)).pack()
entry = Entry(root, font=("Helvetica", 14))
entry.pack()

toggle_button = Button(root, text="Start Timer", command=toggle_countdown, font=("Helvetica", 14))
toggle_button.pack()

Label(root, textvariable=time_str, font=("Helvetica", 20)).pack()

root.mainloop()
