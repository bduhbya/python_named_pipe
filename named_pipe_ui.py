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


class PipeClientUI:
    def __init__(self, root: tk.Tk, sendPipeName: str, sendPipeMessageCallback):
        self.root = root
        self.sendPipeName = sendPipeName  # The name of the pipe to send messages to
        self.sendPipeMessageCallback = (
            sendPipeMessageCallback  # The callback to send messages to the pipe
        )
        self.setup_ui()

    def setup_ui(self):
        # Create a sendMessageFrame for the send message button and the server entry
        self.sendMessageFrame = tk.Frame(self.root)
        self.sendMessageFrame.pack()
        # Add space between column 0 and column 1
        self.sendMessageFrame.grid_columnconfigure(0, minsize=200)

        self.sendPipeMessageLabelFrame = tk.LabelFrame(
            self.sendMessageFrame, text="Send Pipe Message: ", bd=1
        )
        self.sendPipeMessageLabelFrame.grid(row=0, column=0, sticky="w")

        self.sendMessageButton = tk.Button(
            self.sendPipeMessageLabelFrame,
            text="Send Message",
            command=self.send_server_entry,
        )

        self.sendMessageButton.pack()

        self.serverEntry = tk.Entry(self.sendPipeMessageLabelFrame)
        self.serverEntry.pack()

        self.sendPipeNameLabelFrame = tk.LabelFrame(
            self.sendMessageFrame, text="Send Pipe Name: ", bd=1
        )
        self.sendPipeNameLabelFrame.grid(row=0, column=1, sticky="e")

        self.sendPipeNameLabel = tk.Label(
            self.sendPipeNameLabelFrame, text=self.sendPipeName
        )
        self.sendPipeNameLabel.pack()

        self.changePipeNameButton = tk.Button(
            self.sendPipeNameLabelFrame,
            text="Set Pipe Name",
            command=self.set_send_pipe_name,
        )
        self.changePipeNameButton.pack()

    def set_send_pipe_name(self):
        new_name = simpledialog.askstring("Input", "Enter the new pipe name:")
        if new_name is not None:  # If the user didn't cancel the dialog
            # TODO: Add validation for the pipe name
            # TODO: Add callback to update the pipe name
            self.sendPipeName = new_name
            self.sendPipeNameLabel.config(text=self.sendPipeName)


startClientText = "Start Client"
stopClientTtext = "Stop Client"

stopClient = threading.Event()
clientThread = None
clientPipeName = testServerName
dataReceived = ""
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

sendPipeUi = PipeClientUI(root, testServerName, send_pipe_message)

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
