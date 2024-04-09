import time
import sys
import win32pipe, win32file, pywintypes
import threading
from typing import Callable

ClientCallbackType = Callable[[str], None]

serverPipeName = None
serverNamedPipe = None

clientPipeName = None
clientNamedPipe = None

testServerName = r"\\.\pipe\Foo"


def create_server_pipe(pipeName):
    namedPipe = win32pipe.CreateNamedPipe(
        pipeName,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_MESSAGE
        | win32pipe.PIPE_READMODE_MESSAGE
        | win32pipe.PIPE_WAIT,
        1,
        65536,
        65536,
        0,
        None,
    )
    if namedPipe is None:
        print(f"Failed to create named pipe {pipeName}")
    print(f"Named pipe {pipeName} created")
    return namedPipe


def close_pipe(namedPipe, pipeName: str):
    if namedPipe is not None:
        win32file.CloseHandle(namedPipe)
        namedPipe = None
        print(f"Named pipe {pipeName} closed")


def pipe_server_test():
    print("pipe_server_test")
    global serverPipeName
    global serverNamedPipe
    count = 0
    try:
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
        print("no pipe")
        return

    try:
        print(f"sending message {message}")
        # convert to bytes
        pipeData = str.encode(message)
        win32file.WriteFile(serverNamedPipe, pipeData)
        print("Message sent")
    except pywintypes.error as e:
        print(f"Error: {e}")
    finally:
        print("finally")


def create_client_pipe(pipeName):
    print(f"create_client_pipe: {pipeName}")
    handle = win32file.CreateFile(
        pipeName,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0,
        None,
        win32file.OPEN_EXISTING,
        0,
        None,
    )
    res = win32pipe.SetNamedPipeHandleState(
        handle, win32pipe.PIPE_READMODE_MESSAGE, None, None
    )
    print(f"SetNamedPipeHandleState return code: {res}")
    if res == None:
        return handle
    win32file.CloseHandle(handle)
    return None


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
                    time.sleep(1)  # Sleep for a short time to prevent busy waiting
        except pywintypes.error as e:
            if e.args[0] == 2:
                print("no pipe, trying again in a sec")
                time.sleep(1)
            elif e.args[0] == 109:
                print("broken pipe, bye bye")
                quit = True


if __name__ == "__main__":
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
    pipe_server_test()
    stop_event.set()
    clientThread.join()
