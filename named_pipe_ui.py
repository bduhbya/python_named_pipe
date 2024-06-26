import tkinter as tk
from tkinter import simpledialog
import enum
from named_pipe_processing import (
    pipe_client,
    create_pipe,
    testServerName,
    send_message,
    close_pipe,
    listen_for_server_messages,
)
import threading


class ClientState(enum.Enum):
    STOPPED = 0
    RUNNING = 1

class ServerState(enum.Enum):
    STOPPED = 0
    RUNNING = 1


class SendPipeUI:
    def __init__(
        self,
        root: tk.Tk,
        sendPipeName: str,
        sendPipeMessageCallback,
        changePipeNameCallback,
        toggleServerPipeConnection,
    ):
        self.root = root
        self.sendPipeName = sendPipeName  # The name of the pipe to send messages to
        self.sendPipeMessageCallback = (
            sendPipeMessageCallback  # The callback to send messages to the pipe
        )
        self.changePipeNameCallback = changePipeNameCallback
        self.toggleServerPipeConnection = toggleServerPipeConnection
        self.msgReceived = ""
        self.setup_ui()

    def setup_ui(self):
        # Create a sendMessageFrame for the send message button and the server entry
        self.sendMessageFrame = tk.Frame(self.root)
        self.sendMessageFrame.pack()
        # Add space between column 0 and column 1
        self.sendMessageFrame.grid_columnconfigure(0, minsize=200)

        self.sendPipeMessageLabelFrame = tk.LabelFrame(
            self.sendMessageFrame, text="Server Pipe: ", bd=1
        )
        self.sendPipeMessageLabelFrame.grid(row=0, column=0, sticky="w")

        self.sendMessageButton = tk.Button(
            self.sendPipeMessageLabelFrame,
            text="Send Message",
            command=self.send_pipe_message,
        )

        self.sendMessageButton.pack()
        # Disable button until server is connected
        self.sendMessageButton.config(state=tk.DISABLED)

        self.serverEntry = tk.Entry(self.sendPipeMessageLabelFrame)
        self.serverEntry.pack()

        self.serverPipeMessagesLabel = tk.Label(self.sendPipeMessageLabelFrame, text="Messages: ")
        self.serverPipeMessagesLabel.pack()

        self.serverPipeMessages = tk.Message(
            self.sendPipeMessageLabelFrame, width=190, bg="white", fg="black", relief=tk.SUNKEN
        )
        self.serverPipeMessages.pack()

        self.sendPipeNameLabelFrame = tk.LabelFrame(
            self.sendMessageFrame, text="Server Pipe Name: ", bd=1
        )
        self.sendPipeNameLabelFrame.grid(row=0, column=1, sticky="e")

        self.connectDisconnectPipeButton = tk.Button(
            self.sendPipeNameLabelFrame,
            text="Connect Pipe",
            command=self.toggle_connect_pipe,
        )
        self.connectDisconnectPipeButton.pack()

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
        new_name = simpledialog.askstring(
            "Input", "Enter the new pipe name:", initialvalue=self.sendPipeName
        )
        if new_name is not None:  # If the user didn't cancel the dialog
            # TODO: Add validation for the pipe name
            # TODO: Add callback to update the pipe name
            # TODO: Disable button if the server is running
            self.sendPipeName = new_name
            self.changePipeNameCallback(new_name)
            self.sendPipeNameLabel.config(text=self.sendPipeName)

    def send_pipe_message(self):
        message = self.serverEntry.get()
        self.sendPipeMessageCallback(message)
        self.serverEntry.delete(0, tk.END)

    def toggle_connect_pipe(self):
        new_state = self.toggleServerPipeConnection(self.update_server_pipe_messages)
        print(f"toggle_connect_pipe, New state: {new_state}")
        self.connectDisconnectPipeButton.config(text="Disconnect Pipe" if new_state == ServerState.RUNNING else "Connect Pipe")
        self.sendMessageButton.config(state=tk.NORMAL if new_state == ServerState.RUNNING else tk.DISABLED)

    def update_server_pipe_messages(self, message: str):
        self.msgReceived += message + "\n"
        self.serverPipeMessages.config(text=self.msgReceived)


class PipeClientUI:
    def __init__(self, root: tk.Tk, clientPipeName: str, togglePipeClientCallback):
        self.root = root
        self.clientPipeName = clientPipeName
        self.togglePipeClientCallback = togglePipeClientCallback
        self.startClientText = "Start Client"
        self.stopClientTtext = "Stop Client"
        self.msgReceived = ""
        self.setup_ui()

    def setup_ui(self):
        # Create a clientMessageFrame for the send message button and the server entry
        self.clientMessageFrame = tk.Frame(self.root)
        self.clientMessageFrame.pack()
        # Add space between column 0 and column 1
        self.clientMessageFrame.grid_columnconfigure(0, minsize=200)

        self.toggleClientButton = tk.Button(
            self.clientMessageFrame,
            text=self.startClientText,
            command=self.toggle_pipe_client,
        )
        self.toggleClientButton.grid(row=0, column=0, sticky="w")

        self.msgReceived = tk.Message(
            self.clientMessageFrame, width=190, bg="white", fg="black", relief=tk.SUNKEN
        )
        self.msgReceived.grid(row=1, column=0, sticky="w")

        self.clientPipeNameFrame = tk.LabelFrame(
            self.clientMessageFrame, text="Client Pipe Name: ", bd=1
        )
        self.clientPipeNameFrame.grid(row=0, column=1, sticky="e")
        self.clientPipeNameLabel = tk.Label(
            self.clientPipeNameFrame, text=self.clientPipeName
        )
        self.clientPipeNameLabel.pack()

        self.changePipeNameButton = tk.Button(
            self.clientPipeNameFrame,
            text="Set Pipe Name",
            command=self.set_client_pipe_name,
        )
        self.changePipeNameButton.pack()

    def set_client_pipe_name(self):
        new_name = simpledialog.askstring("Input", "Enter the new pipe name:")
        if new_name is not None:  # If the user didn't cancel the dialog
            # TODO: Add validation for the pipe name
            # TODO: Add callback to update the pipe name
            # TODO: Disable button if the client is running
            self.clientPipeName = new_name
            self.clientPipeNameLabel.config(text=self.clientPipeName)

    def toggle_pipe_client(self):
        new_state = self.togglePipeClientCallback(self.client_callback)
        if new_state == ClientState.RUNNING:
            self.toggleClientButton.config(text=self.stopClientTtext)
        else:
            self.toggleClientButton.config(text=self.startClientText)

    def client_callback(self, response: str):
        self.msgReceived.config(text=response)


stopClient = threading.Event()
clientThread = None
serverThread = None
dataReceived = ""
pipeHandle = None
pipeName = testServerName


def change_pipe_name(newName: str):
    global pipeName
    global pipeHandle
    if pipeHandle is not None:
        close_pipe(pipeHandle, pipeName)
        pipeHandle = None

    if clientThread is not None:
        clientPipeUi.toggle_pipe_client()

    pipeName = newName

def toggle_server_pipe_connection(serverMessageCallback) -> ServerState:
    global pipeName
    global pipeHandle
    global serverThread
    if pipeHandle:
        print("closing pipe")
        close_pipe(pipeHandle, pipeName)
        pipeHandle = None
        if serverThread is not None:
            serverThread.join()
            serverThread = None
    else:
        print("Creating pipe")
        create_pipe_entity()
        print("Starting server message receive thread")
        serverThread = threading.Thread(
            target=listen_for_server_messages,
            args=(pipeHandle, serverMessageCallback),
        )
        serverThread.start()
    
    return ServerState.RUNNING if pipeHandle is not None else ServerState.STOPPED

def create_pipe_entity():
    global pipeHandle
    if pipeHandle is not None:
        print(f"Pipe {pipeName} already created")
        return

    pipeHandle = create_pipe(pipeName, "create_pipe_entity")
    print("Creating server")
    if pipeHandle is not None:
        print("pipe created")
    else:
        print("pipe not created")


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
    if pipeHandle is not None:
        send_message("exit", pipeHandle)
        close_pipe(pipeHandle, pipeName)

    if clientThread is not None:
        stop_pipe_client()

    root.destroy()


def send_pipe_message(message: str):
    if not pipeHandle:
        print("Pipe not created")
        return

    if message is None or message == "":
        print("No message to send")
        return

    print("Sending message to pipe: " + message)
    send_message(message, pipeHandle)


def toggle_pipe_client(clientCallback) -> ClientState:
    global clientThread
    global stopClient
    stopClient.clear()
    if clientThread is None:
        clientThread = threading.Thread(
            target=pipe_client,
            args=(
                pipeName,
                stopClient,
                clientCallback,
            ),
        )
        print("Starting client thread")
        clientThread.start()
        return ClientState.RUNNING
    else:
        stop_pipe_client()
        return ClientState.STOPPED


# Create the main window
root = tk.Tk()
root.title("Named Pipe Test Utility")
root.geometry("400x400")

sendPipeUi = SendPipeUI(root, testServerName, send_pipe_message, change_pipe_name, toggle_server_pipe_connection)
clientPipeUi = PipeClientUI(root, testServerName, toggle_pipe_client)

root.protocol("WM_DELETE_WINDOW", on_close)
# Start the event loop
root.mainloop()
