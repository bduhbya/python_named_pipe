import tkinter as tk
from named_pipe_processing import pipe_client
import threading
# Create the main window
root = tk.Tk()
root.title("Named Pipe Test Utility")
root.geometry("400x400")

startClientText = "Start Client"
stopClientTtext = "Stop Client"

stop_client = threading.Event()
client_thread = None
def toggle_pipe_client():
    global client_thread
    global stop_client
    global startClientText
    global stopClientTtext
    global toggle_client_button
    if client_thread is None:
        client_thread = threading.Thread(target=pipe_client, args=(stop_client, ))
        print("Starting client thread")
        client_thread.start()
        toggle_client_button.config(text=stopClientTtext)
    else:
        print("Stopping client thread")
        stop_client.set()
        client_thread.join()
        toggle_client_button.config(text=startClientText)
        client_thread = None

tk.Label(root, text='Custom Pipe Text').pack()
# tk.Label(root, text='Custom Pipe Text').grid(row=0)
# tk.Label(root, text='Last Name').grid(row=1)
e1 = tk.Entry(root)
# e2 = tk.Entry(root)
e1.pack()
# e1.grid(row=0, column=1)
# e2.grid(row=1, column=1)

# Add a button
toggle_client_button = tk.Button(root, text=startClientText, command=toggle_pipe_client)
toggle_client_button.pack()

msgReceived = tk.Message(root, text="Message Received", width=300, bg='white', fg='black', relief=tk.SUNKEN)
msgReceived.pack()

# Start the event loop
root.mainloop()
