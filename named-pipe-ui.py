import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Named Pipe Test Utility")
root.geometry("400x400")

tk.Label(root, text='Custom Pipe Text').pack()
# tk.Label(root, text='Custom Pipe Text').grid(row=0)
# tk.Label(root, text='Last Name').grid(row=1)
e1 = tk.Entry(root)
# e2 = tk.Entry(root)
e1.pack()
# e1.grid(row=0, column=1)
# e2.grid(row=1, column=1)

# Add a button
my_button = tk.Button(root, text="Click Me!", command=lambda: print("Button clicked"))
my_button.pack()

msgReceived = tk.Message(root, text="Message Received", width=300, bg='white', fg='black', relief=tk.SUNKEN)
msgReceived.pack()

# Start the event loop
root.mainloop()
