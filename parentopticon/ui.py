import tkinter as tk

class NoApplication(tk.Frame):
	"""An application to tell the client 'no'"""
	def __init__(self, master=None):
		super().__init__(master)
		self.master = master
		self.pack()
		self.create_widgets()
		
	def create_widgets(self):
		self.ack_button = tk.Button(self)
		self.ack_button["text"] = "Awwwww."
		self.ack_button["command"] = self.say_hi
		self.ack_button.pack(side="top")
		
		self.quit = tk.Button(self, text="QUIT", fg="red", command=self.master.destroy)
		self.quit.pack(side="bottom")
		
	def say_hi(self):
		print("hi there!")
		
def show_denied(name: str) -> None:
	"""Tell the user they can't open their program."""
	root = tk.Tk()
	app = NoApplication(master=root)
	app.mainloop()

