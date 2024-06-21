import tkinter as tk
import math

ANIM_SINE = lambda v: math.sin((v - 0.5) * math.pi) / 2 + 0.5
ANIM_SQRT = lambda v: math.sqrt(v)
ANIM_LINEAR = lambda v: v
ANIM_RECIPROCAL = lambda v: -(1.2 / (5 * v + 1)) + 1.2

class AnimatedLabel(tk.Label):
	def __init__(self, *args, **kwargs):
		self.start = None
		self.end = None
		self.phase = 0
		self.y_func = ANIM_LINEAR
		self.x_func = ANIM_LINEAR
		self.step = 0.05
		self.delay = 10
		self.precision = 3
		self.end_command = None

		self.configure_animation = lambda **k: configure_animation(self, **k)
		self.animate_place = lambda start, end, initial_delay=100, **k: animate_place(self, start, end, initial_delay, **k)
		self.anim_step = lambda: anim_step(self)

		anim_config = self.configure_animation(**kwargs)
		for k in anim_config:
			kwargs.pop(k)

		super().__init__(*args, **kwargs)

		self.x = None
		self.y = None

class AnimatedFrame(tk.Frame):
	def __init__(self, *args, **kwargs):
		self.start = None
		self.end = None
		self.phase = 0
		self.y_func = ANIM_LINEAR
		self.x_func = ANIM_LINEAR
		self.step = 0.05
		self.delay = 10
		self.precision = 3
		self.end_command = None

		self.configure_animation = lambda **k: configure_animation(self, **k)
		self.animate_place = lambda start, end, initial_delay=100, **k: animate_place(self, start, end, initial_delay, **k)
		self.anim_step = lambda: anim_step(self)

		anim_config = self.configure_animation(**kwargs)
		for k in anim_config:
			kwargs.pop(k)

		super().__init__(*args, **kwargs)

		self.x = None
		self.y = None


def animate_place(elem, start, end, initial_delay=100, **kwargs):
	print(elem, start, end, initial_delay, kwargs)
	elem.x, elem.y = start
	elem.start = start
	elem.end = end
	elem.phase = 0

	elem.place(x=start[0], y=start[1], **kwargs)

	elem.after(initial_delay, lambda v=elem: anim_step(v))

def anim_step(elem):
	elem.x = elem.start[0] + (elem.end[0] - elem.start[0]) * elem.x_func(elem.phase)
	elem.y = elem.start[1] + (elem.end[1] - elem.start[1]) * elem.y_func(elem.phase)

	print(elem.y, elem.phase, elem.y_func(elem.phase))

	elem.place(x=elem.x, y=elem.y)
	if round(elem.x, elem.precision) == elem.end[0] and round(elem.y, elem.precision) == elem.end[1]:
		elem.place(x=elem.end[0], y=elem.end[1])
		if elem.end_command:
			elem.end_command()
	elif elem.phase < 1:
		elem.phase += elem.step
		# elem.update_idletasks()
		elem.after(elem.delay, lambda v=elem: anim_step(v))
	elif elem.end_command:
		elem.end_command()


def configure_animation(elem, **kwargs):
	keys = []

	if 'y_func' in kwargs:
		elem.y_func = kwargs['y_func']
		keys.append('y_func')

	if 'x_func' in kwargs:
		elem.x_func = kwargs['x_func']
		keys.append('x_func')

	if 'step' in kwargs:
		elem.step = kwargs['step']
		keys.append('step')

	if 'delay' in kwargs:
		elem.delay = kwargs['delay']
		keys.append('delay')

	if 'precision' in kwargs:
		elem.precision = kwargs['precision']
		keys.append('precision')

	if 'end_command' in kwargs:
		elem.end_command = kwargs['end_command']
		keys.append('end_command')

	return keys

if __name__ == '__main__':
	import ctypes

	window = tk.Tk()

	window.tk.call('tk', 'scaling', 1.9)
	ctypes.windll.shcore.SetProcessDpiAwareness(2)

	window.geometry('300x300')

	pixel = tk.PhotoImage(width=1, height=1)

	l = AnimatedLabel(text='text', background='#ccc', image=pixel, compound='center', height=30, width=100)
	l.configure_animation(y_func=ANIM_RECIPROCAL, delay=5, step=0.05)
	# l.animate_place()
	# l.animate_place()
	l.animate_place((100, 300), (100, 260), 500)

	window.focus()

	window.mainloop()
