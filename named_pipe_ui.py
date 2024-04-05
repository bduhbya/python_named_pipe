import tkinter as tk
from tkinter import simpledialog
from named_pipe_processing import (
    pipe_client,
    create_pipe,
    testServerName,
    send_message,
    close_pipe,
)
import threading

startClientText = "Start Client"
stopClientTtext = "Stop Client"

stopClient = threading.Event()
clientThread = None
clientPipeName = testServerName
dataReceived = ""
serverCreated = False

sendPipeName = testServerName


def set_send_pipe_name():
    global sendPipeName
    new_name = simpledialog.askstring("Input", "Enter the new pipe name:")
    if new_name is not None:  # If the user didn't cancel the dialog
        sendPipeName = new_name
        sendPipeNameLabel.config(text=sendPipeName)


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
    global stopClient
    stopClient.set()
    global clientThread
    if clientThread is not None:
        clientThread.join()
        clientThread = None


def on_close():
    print("Closing window")
    if serverCreated:
        send_message("exit")
        close_pipe()

    if clientThread is not None:
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
    serverEntry.delete(0, "end")


def toggle_pipe_client():
    if not serverCreated:
        create_pipe_entity()

    global clientThread
    global stopClient
    global startClientText
    global stopClientTtext
    global toggleClientButton
    if clientThread is None:
        clientThread = threading.Thread(
            target=pipe_client,
            args=(
                stopClient,
                client_callback,
            ),
        )
        print("Starting client thread")
        clientThread.start()
        toggleClientButton.config(text=stopClientTtext)
    else:
        stop_pipe_client()
        toggleClientButton.config(text=startClientText)


def client_callback(response: str):
    global dataReceived
    dataReceived += response
    msgReceived.config(text=dataReceived)


# Create the main window
root = tk.Tk()
root.title("Named Pipe Test Utility")
root.geometry("400x400")

# Create a sendMessageFrame for the send message button and the server entry
sendMessageFrame = tk.Frame(root)
sendMessageFrame.pack()
# Add space between column 0 and column 1
sendMessageFrame.grid_columnconfigure(0, minsize=200)

# Move the send message button and the server entry to the sendMessageFrame
sendMessageButton = tk.Button(
    sendMessageFrame, text="Send Message", command=send_server_entry
)
sendMessageButton.grid(row=0, column=0, sticky="w")
serverEntry = tk.Entry(sendMessageFrame)
serverEntry.grid(row=1, column=0, sticky="w")

# Move the pipe name label to the right of the sendMessageFrame
sendPipeNameFrame = tk.LabelFrame(sendMessageFrame, text="Send Pipe Name: ", bd=1)
sendPipeNameFrame.grid(row=0, column=1, sticky="e")
sendPipeNameLabel = tk.Label(sendPipeNameFrame, text=testServerName)
sendPipeNameLabel.pack()

changePipeNameButton = tk.Button(
    sendPipeNameFrame, text="Set Pipe Name", command=set_send_pipe_name
)
changePipeNameButton.pack()

# Create a clientMessageFrame for the send message button and the server entry
clientMessageFrame = tk.Frame(root)
clientMessageFrame.pack()
# Add space between column 0 and column 1
clientMessageFrame.grid_columnconfigure(0, minsize=200)
# Add toggle client button
toggleClientButton = tk.Button(
    clientMessageFrame, text=startClientText, command=toggle_pipe_client
)
toggleClientButton.grid(row=0, column=0, sticky="w")

msgReceived = tk.Message(
    clientMessageFrame, width=190, bg="white", fg="black", relief=tk.SUNKEN
)
msgReceived.grid(row=1, column=0, sticky="w")

clientPipeNameFrame = tk.LabelFrame(clientMessageFrame, text="Client Pipe Name: ", bd=1)
clientPipeNameFrame.grid(row=0, column=1, sticky="e")
clientPipeNameLabel = tk.Label(clientPipeNameFrame, text=testServerName)
clientPipeNameLabel.pack()

root.protocol("WM_DELETE_WINDOW", on_close)
# Start the event loop
root.mainloop()
