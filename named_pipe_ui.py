import tkinter as tk
from named_pipe_processing import pipe_client, create_pipe, testServerName, send_message, close_pipe
import threading
# Create the main window
root = tk.Tk()
root.title("Named Pipe Test Utility")
root.geometry("400x400")

startClientText = "Start Client"
stopClientTtext = "Stop Client"

stop_client = threading.Event()
client_thread = None

serverCreated = False

def create_pipe_entity():
    global serverCreated
    if serverCreated:
        return
    serverCreated = create_pipe(testServerName)
    print("Creating server")
    if serverCreated:
        print("pipe created")
    else:
        print("pipe not created")
        # exit(1)

def stop_pipe_client():
    print("Stopping client thread")
    global stop_client
    stop_client.set()
    global client_thread
    if client_thread is not None:
        client_thread.join()
        client_thread = None

def on_close():
    print("Closing window")
    if serverCreated:
        send_message("exit")
        close_pipe()

    if client_thread is not None:
        stop_pipe_client()

    root.destroy()

def send_pipe_message(message: str):
    if not serverCreated:
        create_pipe_entity()

    if message is None or message == "":
        print("No message to send")
        return
    
    print("Sending message to pipe: " + message)
    send_message(message)

def send_server_entry():
    send_pipe_message(serverEntry.get())
    serverEntry.delete(0, 'end')

def toggle_pipe_client():
    if not serverCreated:
        create_pipe_entity()

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
        stop_pipe_client()
        toggle_client_button.config(text=startClientText)

tk.Label(root, text='Custom Pipe Text').pack()
# tk.Label(root, text='Custom Pipe Text').grid(row=0)
# tk.Label(root, text='Last Name').grid(row=1)
serverEntry = tk.Entry(root)
send_message_button = tk.Button(root, text="Send Message",
                                command=send_server_entry)
send_message_button.pack()
# e2 = tk.Entry(root)
serverEntry.pack()
# serverEntry.grid(row=0, column=1)
# e2.grid(row=1, column=1)

# Add a button
toggle_client_button = tk.Button(root, text=startClientText, command=toggle_pipe_client)
toggle_client_button.pack()

msgReceived = tk.Message(root, width=300, bg='white', fg='black', relief=tk.SUNKEN)
msgReceived.pack()

root.protocol("WM_DELETE_WINDOW", on_close)
# Start the event loop
root.mainloop()
