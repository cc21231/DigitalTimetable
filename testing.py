import datetime
import re
import time
import tkinter as tk
from tkinter import font as tkfont
#

var = 0

var1 = 0

d = {'a': 10, 'b': 11}
print(10 in d, 'a' in d)



d.update({var: 0, var1: 0})

print(f'{var:+n}')

exit()
root = tk.Tk()
print(tkfont.families())
# tk.Label(text='test', font=('Calibri', 12, 'bold'))
# root.destroy()
# root.winfo_exists()

t = tk.Text()
t.grid(sticky='nswe')

t.insert(1.0, """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
proident, sunt in culpa qui officia deserunt mollit anim id est laborum.""")

t.focus()
t.tag_add('sel', 1.5, 1.6)
print(t.tag_())

print(root)

root.mainloop()
exit()
from multipledispatch import dispatch
from typing import overload, Type

class Abc:
	def __init__(self):
		self.var = 0

	def test(self):
		num = 0
		while True:
			yield num
			num += 1

	def __iter__(self):
		# for i in [self.var]:
		yield 0

	@dispatch(object)
	def g(self):
		pass

	def __slice__(self):
		print('a')

	def __del__(self):
		del self

# import ctypes
# ctypes.windll.shcore.SetProcessDpiAwareness(window.settings['resolution_scaling'])

print({0, 1, 2, 3, 4, 5} ^ {3, 4, 5, 6, 7, 8})

arr = [0, 1, 2, 3, 3, 3, 4]
arr.remove(3)
print(arr)
exit()


print({v for v in range(10)})

print('a'.join({'0', '1', '2'}))

print({0, 1, 2, 3, 4, 5, 6} - {2, 3, 4})

print({0, 1, 2} in [{0, 1, 2, 3}])
if {2, 3, 4} - {2, 3, 4, 5}:
	print('a')
exit()
#
# arr = [0, 1, 2]
#
# arr = set(filter(lambda v: v < 2, arr))
# print(arr)
# exit()

def func(**kwargs):
	print(kwargs)


f = lambda **k: func(**k)
print(f(test='test'))

exit()
print('%.02f' % (10000, 200))

exit()

a = Abc()
b = Abc()
c = a

del a

print(b)
print(c)

print(tuple(a))

arr[a]


# tmap = str.maketrans(list(range(0, 27)), 'abcdefghijklmnopqrstuv')

# result = int(inputvalue.translate(tmap), 32)
print()