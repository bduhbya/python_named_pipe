import time
import sys
import win32pipe, win32file, pywintypes
import threading
from typing import Callable

ClientCallbackType = Callable[[str], None]
# TODO: Only use one pipe for both client and server

serverPipeName = None
serverNamedPipe = None

clientPipeName = None
clientNamedPipe = None
clientNamedPipeHandle = None

testServerName = r"\\.\pipe\Foo"


def create_pipe(pipeName, source):
    print(f"create_pipe, source: {source}, name: {pipeName}")
    try:
        namedPipe = win32pipe.CreateNamedPipe(
            pipeName,
            win32pipe.PIPE_ACCESS_DUPLEX,  # | win32pipe.PIPE_UNLIMITED_INSTANCES,
            win32pipe.PIPE_TYPE_MESSAGE
            | win32pipe.PIPE_READMODE_MESSAGE
            | win32pipe.PIPE_WAIT,
            2,
            # win32pipe.PIPE_UNLIMITED_INSTANCES,
            65536,
            65536,
            0,
            None,
        )
    except pywintypes.error as e:
        print(f"create_pipe, Failed to create named pipe: {e}")
        return None

    print(f"create_pipe, Named pipe {pipeName} created")

    return namedPipe


def create_server_pipe(pipeName):
    # namedPipe = get_read_pipe_handle(pipeName, "create_server_pipe")

    # if namedPipe is not None:
    #     print(f"create_server_pipe, Named pipe {pipeName} read handle didn't exist.")
    #     win32file.CloseHandle(namedPipe)

    namedPipe = create_pipe(pipeName, "create_server_pipe")
    if namedPipe is None:
        print(f"create_server_pipe, Failed to create named pipe {pipeName}")
    else:
        print(f"create_server_pipe, Named pipe {pipeName} created")

    return namedPipe


def close_pipe(namedPipe, pipeName: str):
    if namedPipe is not None:
        win32file.CloseHandle(namedPipe)
        namedPipe = None
        print(f"Named pipe {pipeName} closed")


def pipe_server_test(wait_for_client=False):
    print("pipe_server_test")
    global serverPipeName
    global serverNamedPipe
    count = 0
    try:
        if wait_for_client:
            print("waiting for client to connect pipe: " + serverPipeName)
            win32pipe.ConnectNamedPipe(serverNamedPipe, None)
            print("got client")

        while count < 10:
            send_message(str(count))
            time.sleep(1)
            count += 1

        print("finished now")
    finally:
        close_pipe(serverNamedPipe, serverPipeName)


def send_message(message: str):
    if serverNamedPipe is None:
        print("send_message, no pipe")
        return

    try:
        print(f"send_message, sending message {message}")
        # convert to bytes
        pipeData = str.encode(message)
        win32file.WriteFile(serverNamedPipe, pipeData)
        print("Message sent")
    except pywintypes.error as e:
        print(f"Error: {e}")
    finally:
        print("send_message, finally")


def get_read_pipe_handle(pipeName, source):
    print(f"get_read_pipe_handle, source: {source}, name: {pipeName}")
    try:
        handle = win32file.CreateFile(
            pipeName,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
    except pywintypes.error as e:
        if e.winerror == 2:
            print(f"get_read_pipe_handle, Named pipe {pipeName} not found")
            handle = None
        else:
            print(f"get_read_pipe_handle, Failed to open pipe: {e}")
            handle = None

    if handle is not None:
        print(f"get_read_pipe_handle, opened read handle for {pipeName}")

    return handle


# TODO: Call from client and wait for pipe to be created
def create_client_pipe(pipeName):
    print(f"create_client_pipe: {pipeName}")
    handle = get_read_pipe_handle(pipeName, "create_client_pipe")

    if handle is None:
        print(f"pipe {pipeName} doesn't exist, creating it")
        global clientNamedPipeHandle
        clientNamedPipeHandle = create_pipe(pipeName, "create_client_pipe")
        handle = get_read_pipe_handle(
            pipeName, "create_client_pipe after initial creation"
        )

    if handle is None:
        print(f"Failed to create pipe {pipeName}")
        close_client_pipe()
        return None

    try:
        res = win32pipe.SetNamedPipeHandleState(
            handle,
            win32pipe.PIPE_READMODE_MESSAGE,
            None,
            None,
            # handle, win32pipe.PIPE_READMODE_MESSAGE, None, None
        )
    except pywintypes.error as e:
        print(f"SetNamedPipeHandleState error: {e}")
        close_client_pipe()
        return None

    # print(f"SetNamedPipeHandleState return code: {res}")
    # if res == None:
    return handle

    # print(f"Failed to set pipe handle state, closing handle {handle}")
    # close_client_pipe()
    # return None


def close_client_pipe():
    global clientNamedPipe
    global clientPipeName
    global clientNamedPipeHandle
    if clientNamedPipe is not None:
        win32file.CloseHandle(clientNamedPipe)
        clientNamedPipe = None
        print(f"Named pipe {clientPipeName} closed")

    if clientPipeName is not None:
        clientPipeName = None

    if clientNamedPipeHandle is not None:
        win32file.CloseHandle(clientNamedPipeHandle)
        clientNamedPipeHandle = None
        print(f"Named pipe handle closed")


def pipe_client(stop_event, callback: ClientCallbackType):
    print("pipe client")
    quit = False
    if stop_event is None:
        print("stop_event is None")
        return

    if clientNamedPipe is None:
        print("no pipe")
        return

    while not quit and not stop_event.is_set():
        try:
            while True and not stop_event.is_set():
                _, available, _ = win32pipe.PeekNamedPipe(clientNamedPipe, 0)
                if available:
                    resp = win32file.ReadFile(clientNamedPipe, 64 * 1024)
                    if callback is not None:
                        callback(str(resp[1], "utf-8"))
                    print(f"message: {resp}")
                else:
                    print("no message, waiting for one")
                    time.sleep(1)  # Sleep for a short time to prevent busy waiting
            print("stopping client")
            quit = True
            # win32file.CloseHandle(clientNamedPipe)
        except pywintypes.error as e:
            if e.args[0] == 2:
                print("no pipe, trying again in a sec")
                time.sleep(1)
            elif e.args[0] == 109:
                print("broken pipe, bye bye")
                quit = True


def stop_client_thread(clientThread, stop_event):
    print("Stopping client thread")
    stop_event.set()
    if clientThread is not None:
        clientThread.join()
        clientThread = None


def run_server_first_loopback():
    global serverPipeName
    global serverNamedPipe
    global clientPipeName
    global clientNamedPipe
    stop_event = threading.Event()
    serverNamedPipe = create_server_pipe(testServerName)
    if serverNamedPipe is not None:
        serverPipeName = testServerName
        print("server pipe created")
    else:
        print("server pipe not created")
        exit(1)

    clientNamedPipe = create_client_pipe(testServerName)
    if clientNamedPipe is not None:
        clientPipeName = testServerName
        print("client pipe created")
    else:
        print("client pipe not created")
        exit(1)

    clientThread = threading.Thread(
        target=pipe_client,
        args=(
            stop_event,
            None,
        ),
    )
    print("Starting client thread")
    clientThread.start()
    pipe_server_test(True)
    stop_client_thread(clientThread, stop_event)


def run_client_first_loopback():
    global serverPipeName
    global serverNamedPipe
    global clientPipeName
    global clientNamedPipe
    stop_event = threading.Event()
    clientNamedPipe = create_client_pipe(testServerName)
    if clientNamedPipe is not None:
        clientPipeName = testServerName
        print("client pipe created")
    else:
        print("client pipe not created")
        exit(1)

    clientThread = threading.Thread(
        target=pipe_client,
        args=(
            stop_event,
            None,
        ),
    )
    print("Starting client thread")
    clientThread.start()

    serverNamedPipe = create_server_pipe(testServerName)
    if serverNamedPipe is not None:
        serverPipeName = testServerName
        print("server pipe created")
    else:
        print("server pipe not created")
        stop_client_thread(clientThread, stop_event)
        exit(1)

    pipe_server_test()
    stop_client_thread(clientThread, stop_event)


if __name__ == "__main__":
    print("Hello from named_pipe_processing.py")
    print(f"Arguments: {sys.argv}")
    print("Running server first loopback")
    run_server_first_loopback()
    print("Running client first loopback")
    run_client_first_loopback()
