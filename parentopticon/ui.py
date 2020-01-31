import os
import tkinter as tk

ROOT = os.path.dirname(os.path.dirname(__file__))

class NoApplication(tk.Frame):
	"""An application to tell the client 'no'"""
	def __init__(self, program_name, reason, master=None):
		super().__init__(master)
		self.master = master
		self.program_name = program_name
		self.reason = reason
		self.pack()
		self.create_widgets()
		
	def create_widgets(self):
		image_path = os.path.join(ROOT, "images", "sad-dragon.gif")
		image = tk.PhotoImage(file=image_path)

		content = ("Sorry, you can't play {}.\n"
			"Looks like it's because {}").format(
				self.program_name,
				self.reason)
		self.message = tk.Label(self, text=content)
		# self.message = tk.Label(self, image=image)
		# self.message["image"] = image
		self.message.pack(side="top")
		
		self.ack_button = tk.Button(self, text="Awwww.", command=self.master.destroy)
		self.ack_button.pack(side="bottom")
		
		
def show_denied(program_name: str, reason: str) -> None:
	"""Tell the user they can't open their program."""
	root = tk.Tk(className="parentopticon")
	app = NoApplication(
		master=root,
		program_name=program_name,
		reason=reason)
	app.mainloop()

