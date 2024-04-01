import time
import sys
import win32pipe, win32file, pywintypes
import threading

pipeName = None
namedPipe = None
testServerName = r'\\.\pipe\Foo'

def create_pipe(pipe_name):
    global pipeName
    global namedPipe
    pipeName = pipe_name
    namedPipe = win32pipe.CreateNamedPipe(
        pipeName,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
        1, 65536, 65536,
        0,
        None)
    if namedPipe is None:
        print(f"Failed to create named pipe {pipeName}")
        return False
    print(f"Named pipe {pipeName} created")
    return True

def close_pipe():
    global namedPipe
    if namedPipe is not None:
        win32file.CloseHandle(namedPipe)
        namedPipe = None
        print(f"Named pipe {pipeName} closed")

def pipe_server_test():
    print("pipe_server_test")
    global namedPipe
    global pipeName
    count = 0
    # pipe = win32pipe.CreateNamedPipe(
    #     r'\\.\pipe\Foo',
    #     win32pipe.PIPE_ACCESS_DUPLEX,
    #     win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
    #     1, 65536, 65536,
    #     0,
    #     None)
    try:
        print("waiting for client to connect pipe: " + pipeName)
        win32pipe.ConnectNamedPipe(namedPipe, None)
        print("got client")

        while count < 10:
            send_message(str(count))
            time.sleep(1)
            count += 1

        print("finished now")
    finally:
        close_pipe()

def send_message(message: str):
    if namedPipe is None:
        print("no pipe")
        return

    try:
        print("sending message {message}")
        # convert to bytes
        pipeData = str.encode(message)
        win32file.WriteFile(namedPipe, pipeData)
        print("Message sent")
    except pywintypes.error as e:
        print(f"Error: {e}")
    finally:
        print("finally")

def pipe_client(stop_event):
    print("pipe client")
    quit = False
    if stop_event is None:
        print("stop_event is None")
        return

    if namedPipe is None:
        print("no pipe")
        return

    while not quit and not stop_event.is_set():
        try:
            handle = win32file.CreateFile(
                pipeName,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
            if res == 0:
                print(f"SetNamedPipeHandleState return code: {res}")
            
            while True and not stop_event.is_set():
                _, available, _ = win32pipe.PeekNamedPipe(handle, 0)
                if available:
                    resp = win32file.ReadFile(handle, 64*1024)
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


if __name__ == '__main__':
    stop_event = threading.Event()
    if create_pipe(testServerName):
        print("pipe created")
    else:
        print("pipe not created")
        exit(1)

    if len(sys.argv) < 2:
        print("need s or c as argument")
    elif sys.argv[1] == "s":
        pipe_server_test()
    elif sys.argv[1] == "c":
        pipe_client(stop_event=stop_event)
    else:
        print(f"no can do: {sys.argv[1]}")