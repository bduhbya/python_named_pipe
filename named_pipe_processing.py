import time
import sys
import win32pipe, win32file, pywintypes
import threading
from typing import Callable
from enum import Enum

ClientCallbackType = Callable[[str], None]

globalPipeName = None
serverNamedPipe = None

readPipeHandle = None

testServerName = r"\\.\pipe\Foo"


class PipeCreationResult(Enum):
    SUCCESS = 1
    FAILURE = 2
    ALREADY_EXISTS = 3
    DOES_NOT_EXIST = 4


def create_pipe(pipeName, source):
    print(f"create_pipe, source: {source}, name: {pipeName}")
    try:
        namedPipe = win32pipe.CreateNamedPipe(
            pipeName,
            win32pipe.PIPE_ACCESS_DUPLEX,  # | win32pipe.PIPE_UNLIMITED_INSTANCES,
            win32pipe.PIPE_TYPE_MESSAGE
            | win32pipe.PIPE_READMODE_MESSAGE
            | win32pipe.PIPE_WAIT,
            1,
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
    global globalPipeName
    global serverNamedPipe
    count = 0
    try:
        if wait_for_client:
            print("waiting for client to connect pipe: " + globalPipeName)
            win32pipe.ConnectNamedPipe(serverNamedPipe, None)
            print("got client")

        while count < 10:
            send_message_internal(str(count))
            time.sleep(1)
            count += 1

        print("finished now")
    finally:
        close_pipe(serverNamedPipe, globalPipeName)


def send_message_internal(message: str):
    if serverNamedPipe is None:
        print("send_message_internal, no pipe")
        return

    send_message(message, serverNamedPipe)


def send_message(message: str, pipeHandle):
    if pipeHandle is None:
        print("send_message, no pipe")
        return

    try:
        print(f"send_message, sending message {message}")
        # convert to bytes
        pipeData = str.encode(message)
        win32file.WriteFile(pipeHandle, pipeData)
        print("Message sent")
    except pywintypes.error as e:
        print(f"Error: {e}")
    finally:
        print("send_message, finally")


def get_read_pipe_handle(pipeName, source):
    print(f"get_read_pipe_handle, source: {source}, name: {pipeName}")
    handle = None
    returnArray = [PipeCreationResult.SUCCESS, None]
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
            returnArray[0] = PipeCreationResult.DOES_NOT_EXIST
        else:
            print(f"get_read_pipe_handle, Failed to open pipe: {e}")
            returnArray[0] = PipeCreationResult.FAILURE

    returnArray[1] = handle

    return returnArray


def create_client_pipe(pipeName, stopEvent):
    print(f"create_client_pipe: {pipeName}")
    while True:
        result = get_read_pipe_handle(pipeName, "create_client_pipe")
        if (
            result[0] == PipeCreationResult.SUCCESS
            or result[0] == PipeCreationResult.FAILURE
            or stopEvent.is_set()
        ):
            break
        time.sleep(1)

    if result[1] is None or result[0] == PipeCreationResult.FAILURE:
        print(f"Failed to create pipe {pipeName}")
        return None

    handle = result[1]
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
        return None

    return handle


def close_client_pipe():
    global readPipeHandle
    if readPipeHandle is not None:
        win32file.CloseHandle(readPipeHandle)
        readPipeHandle = None
        print(f"Read pipe hanldle {globalPipeName} closed")


def pipe_client(pipeName, stop_event, callback: ClientCallbackType):
    print("pipe client")
    quit = False
    if stop_event is None:
        print("stop_event is None")
        return

    # TODO: move handle creation to loop
    global readPipeHandle
    readPipeHandle = create_client_pipe(pipeName, stop_event)
    if readPipeHandle is None:
        print("no pipe, exiting client thread")
        return

    while not quit and not stop_event.is_set():
        try:
            while True and not stop_event.is_set():
                _, available, _ = win32pipe.PeekNamedPipe(readPipeHandle, 0)
                if available:
                    resp = win32file.ReadFile(readPipeHandle, 64 * 1024)
                    if callback is not None:
                        callback(str(resp[1], "utf-8"))
                    print(f"message: {resp}")
                else:
                    print("no message, waiting for one")
                    time.sleep(1)  # Sleep for a short time to prevent busy waiting
            print("stopping client")
            quit = True
        except pywintypes.error as e:
            if e.args[0] == 2:
                print("no pipe, trying again in a sec")
                time.sleep(1)
            elif e.args[0] == 109:
                print("broken pipe, bye bye")
                quit = True
    close_client_pipe()


def stop_client_thread(clientThread, stop_event):
    print("Stopping client thread")
    stop_event.set()
    if clientThread is not None:
        clientThread.join()
        clientThread = None


def run_server_first_loopback():
    global globalPipeName
    global serverNamedPipe
    stop_event = threading.Event()
    serverNamedPipe = create_server_pipe(testServerName)
    if serverNamedPipe is not None:
        globalPipeName = testServerName
        print("server pipe created")
    else:
        print("server pipe not created")
        exit(1)

    clientThread = threading.Thread(
        target=pipe_client,
        args=(
            testServerName,
            stop_event,
            None,
        ),
    )
    print("Starting client thread")
    clientThread.start()
    pipe_server_test(True)
    stop_client_thread(clientThread, stop_event)


def run_client_first_loopback():
    global globalPipeName
    global serverNamedPipe
    stop_event = threading.Event()

    clientThread = threading.Thread(
        target=pipe_client,
        args=(
            testServerName,
            stop_event,
            None,
        ),
    )
    print("Starting client thread")
    clientThread.start()

    serverNamedPipe = create_server_pipe(testServerName)
    if serverNamedPipe is not None:
        globalPipeName = testServerName
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
