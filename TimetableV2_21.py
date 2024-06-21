"""
=========================================
Program Name  : Timetable.py
Author        : Connor Bateman
Version       : v2.26.10
Revision Date : 21-06-2024
Dependencies  : requirements.txt
=========================================
"""
VERSION = '2.26.10'
import re
import sys
from traceback import format_exc
import idlelib.colorizer as ic
import idlelib.percolator as ip
import configurable_image_widgets18 as ci
from tkinter import messagebox as mb
from tkinter import filedialog as fd
from typing import Generator, Literal, Optional, Any
from tkinter import ttk
from tkinter import simpledialog as sd
import platform
import tkinter as tk
import pywinstyles
import datetime
import os.path
import ctypes
import tksvg
import json
import animated_widgets as anim
from toolsV1 import *
from tkinter import font as tkfont
import webbrowser
from multipledispatch import dispatch

from reportlab.lib.colors import HexColor, Color  # noqa
from reportlab.lib import units
from reportlab.platypus import Table
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.ttfonts import TTFont

## Define regex patterns for the supported numbering and dotpoint formats
DASHPOINT_PATTERN = r'(?P<DASHPOINT>[>\-])'
DOTPOINT_PATTERN = r'(?P<DOTPOINT>[•o])'
LETTERING_PATTERN = r'(?P<LETTERING>(([A-Z]{1,2})|([a-z]{1,2}))[\):])'
NUMBERING_PATTERN = r'(?P<NUMBERING>[0-9]{1,2}[\.\):])'

INDENT_PATTERN = rf'(\n|\A)[ \t]*({DOTPOINT_PATTERN}|{NUMBERING_PATTERN}|{LETTERING_PATTERN}|{DASHPOINT_PATTERN})[ \t]+'  # Get the full pattern for colour delegation


class AutoScrollbar(ttk.Scrollbar):
	"""
	:From: https://stackoverflow.com/a/48137257

	A scrollbar that hides itself if it’s not needed. Works only for grid geometry manager.
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		self.target: Optional[tk.Canvas] = kwargs.pop('target') if 'target' in kwargs else None
		self.enabled: Optional[tk.Canvas] = kwargs.pop('enabled') if 'enabled' in kwargs else True
		orient = kwargs['orient'] if 'orient' in kwargs else 'vertical'

		super().__init__(*args, **kwargs)

		## Bind scrolling to the appropriate function based on the orientation of the scrollbar
		if self.target is not None:
			if orient == 'vertical':
				self.bind('<MouseWheel>', lambda e: self.scroll_y)
			else:
				self.bind('<MouseWheel>', lambda e: self.scroll_x)

	def scroll_x(self, e: tk.Event) -> None:
		""" Scroll the target widget on the x-axis """
		self.target.xview_scroll(int(-1 * (e.delta / 120)), 'units')

	def scroll_y(self, e: tk.Event) -> None:
		""" Scroll the target widget on the y-axis """
		self.target.yview_scroll(int(-1 * (e.delta / 120)), 'units')

	def set(self, low: Any, high: Any) -> None:
		""" Set the value of the scrollbar """
		if not self.enabled:  # Return if the scrollbar is not enabled
			return

		## If the bottom of the scrollbar is at 0% scroll and the top of the scrollbar is at 100% scroll (i.e.: the length of the scrollbar covers the entire widget), then hide the widget
		if float(low) <= 0.0 and float(high) >= 1.0:
			self.grid_remove()  # Hide the scrollbar
		else:
			self.grid()  # 'Show' the scrollbar
			ttk.Scrollbar.set(self, low, high)  # Set the position of the scrollbar


class CustomComboBox(ttk.Combobox):
	""" Creates a ttk combobox with a custom themed scrollbar """

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		## Referenced from: https://stackoverflow.com/a/63135420
		window.eval(f'set popdown [ttk::combobox::PopdownWindow {self}]')  # Use tcl to set a variable `popdown` to this widget
		window.eval(f'$popdown.f.sb configure -style {kwargs["style"]}.Vertical.TScrollbar')  # Use tcl to set the style of this widget’s scrollbar


class CustomRadiobutton(tk.Radiobutton):
	"""
	A custom radiobutton widget that allows the user to set a custom foreground colour to use when the radiobutton’s value is selected
	"""

	def __init__(self, *args, **kwargs) -> None:
		self.selectforeground = kwargs.pop('selectforeground') if 'selectforeground' in kwargs else None  # Get the foreground to use when selected

		super().__init__(*args, **kwargs)
		self.variable = kwargs['variable'] if 'variable' in kwargs else None  # Get the tkinter variable to monitor for changes
		self.normalforeground = self.cget('foreground')  # Get the default foreground colour to use when not selected

		kwargs['variable'].trace_add('write', lambda name, index, mode: self.change_val())  # Add a trace to the radiobutton’s variable to call the `change_val` function whenever the variable’s value is changed

		self.change_val()

	def change_val(self) -> None:
		"""
		Updates the foreground and background colour of the widget. Called whenever the value of the radiobutton variable changes.
		"""

		if self.variable.get() == self.cget('value'):  # If the value of the radiobutton’s variable equals the value
			self.configure(foreground=self.selectforeground, background='#2E3274')  # Set the selected colours
		else:
			self.configure(foreground=self.normalforeground, background='#272E35')  # Set the normal colours


class MouseoverButton(tk.Label):
	"""
	A Label subclass that behaves like a button but changes the foreground and background colour when moused-over.
	Being a label widget, rather than a button, allows for setting a highlight background.

	The 'active' state is used to indicate the button is moused over.
	"""

	def __init__(self, *args, **kwargs) -> None:
		## Get the mouseover colours
		self.mouseover_bg = kwargs.pop('mouseoverbackground') if 'mouseoverbackground' in kwargs else None
		self.mouseover_fg = kwargs.pop('mouseoverforeground') if 'mouseoverforeground' in kwargs else None

		## Get the button command
		self.command = kwargs.pop('command') if 'command' in kwargs else None

		super().__init__(*args, **kwargs)
		## Get the default colours
		self.default_bg = self.cget('background')
		self.default_fg = self.cget('foreground')

		## The activeforeground and activebackground don't seem to change the appearance of the widget, so they are used to store the 'clicked' colours
		if 'activeforeground' not in kwargs:
			self.configure(activeforeground=self.default_fg)

		if 'activebackground' not in kwargs:
			self.configure(activebackground=self.default_bg)

		## Bind the mouse cursor entering and leaving the widget
		self.bind('<Enter>', lambda v: self.enter(), add='+')
		self.bind('<Leave>', lambda v: self.leave(), add='+')

		## Bind clicking and releasing the widget
		self.bind('<Button-1>', lambda v: self.pressed(), add='+')
		self.bind('<ButtonRelease-1>', lambda v: self.released(), add='+')

		self.clicked = False

	def pressed(self) -> None:
		""" Update the foreground and background to the active colours. Called when the widget is clicked """

		self.configure(background=self.cget('activebackground'), foreground=self.cget('activeforeground'))
		self.clicked = True

	def released(self) -> None:
		""" Update the foreground and background colours and call the click command. Called when the mouse button is released """

		self.clicked = False
		if self.cget('state') != 'normal':  # Check if the button’s state is active (i.e.: the cursor is inside the widget)
			self.configure(background=self.mouseover_bg, foreground=self.mouseover_fg)  # Set the foreground and background colours to the mouseover colours
			self.command()  # Call the button’s command
		else:
			self.configure(background=self.default_bg, foreground=self.default_fg)  # If the cursor is not inside the widget, reset the foreground and background colour but do not call the command. This allows the user to 'cancel' a buttonpress by moving the cursor off the widget.

	def enter(self) -> None:
		"""
		Called when the mouse cursor enters the widget. Changes the foreground and background colour to the mouseover colours.
		"""

		self.configure(state='active', background=self.mouseover_bg, foreground=self.mouseover_fg)

	def leave(self) -> None:
		"""
		Called when the mouse cursor leaves the widget. Changes the foreground and background colour back to the defaults.
		"""

		if not self.clicked:  # Check if the button is pressed
			self.configure(state='normal', background=self.default_bg, foreground=self.default_fg)  # If the button is not pressed, reset the foreground and background colours
		else:
			self.configure(state='normal')  # Otherwise, reset the state.


class WindowTopbar(tk.Frame):
	"""
	A widget containing the optionmenu at the top of the window and the related functions

	:param root: (Window) The root window element
	"""

	def __init__(self, root, *args, **kwargs) -> None:
		super().__init__(root, *args, **kwargs)
		self.root: Window = root

		self.columnconfigure(10, weight=1)
		self.rowconfigure(0, weight=1)

		icons = root.icons  # Get the icon dictionary from the main window

		## Define default formatting for UI elements
		buttonconfig = {'background': self.cget('background'), 'width': 27, 'height': 27, 'activebackground': '#303841', 'mouseoverbackground': '#303841', 'borderwidth': 0}

		## 'Shortcut' Buttons
		MouseoverButton(self, image=icons['save'], command=lambda: self.root.timetable.save_timetable(), **buttonconfig).grid(row=0, column=2, sticky='nswe', padx=(0, 1))
		MouseoverButton(self, image=icons['saveas'], command=lambda: self.root.timetable.save_as(), **buttonconfig).grid(row=0, column=3, sticky='nswe', padx=(0, 10))

		MouseoverButton(self, image=icons['undo'], command=lambda: self.root.undo(), **buttonconfig).grid(row=0, column=4, sticky='nswe', padx=(0, 1))
		MouseoverButton(self, image=icons['redo'], command=lambda: self.root.redo(), **buttonconfig).grid(row=0, column=5, sticky='nswe', padx=(0, 10))

		MouseoverButton(self, image=icons['settings'], command=lambda: self.root.show_settings(), **buttonconfig).grid(row=0, column=6, sticky='nswe', padx=(0, 10))

		## ------------------------------------------ File Menu -------------------------------------------
		file_menubutton = tk.Menubutton(self, text='File', relief='flat', borderwidth=0, activebackground='#323232', image=self.root.pixel, compound='center', height=13, width=50, background=self.cget('background'), foreground='#D8DEE9', activeforeground='#D8DEE9', font=('Calibri', 13))
		file_menubutton.grid(row=0, column=7, sticky='nswe', padx=(0, 1))

		export_menu = tk.Menu(file_menubutton, tearoff=0, background='#323232', relief='flat', foreground='#fff', borderwidth=0, activeborderwidth=0, type='normal')
		export_menu.add_command(label='CSV', image=icons['csv'], compound='left', command=lambda: self.root.export_timetable('csv'))
		export_menu.add_command(label='Excel Spreadsheet', image=icons['xls'], compound='left', command=lambda: self.root.export_timetable('xls'))
		export_menu.add_command(label='PDF', image=icons['pdf'], compound='left', command=lambda: self.root.export_timetable('pdf'))

		file_menu = tk.Menu(file_menubutton, tearoff=0, background='#323232', relief='flat', foreground='#fff', borderwidth=0, activeborderwidth=0, type='normal')
		file_menu.add_command(label='Save', image=icons['save'], compound='left', hidemargin=True, command=lambda: self.root.timetable.save_timetable())
		file_menu.add_command(label='Save As', image=icons['saveas'], compound='left', hidemargin=True, command=lambda: self.root.timetable.save_as())
		file_menu.add_command(label='Save a Copy', image=icons['savecopy'], compound='left', hidemargin=True, command=lambda: self.root.timetable.save_copy())
		file_menu.add_separator(background='#D4D4D4')
		file_menu.add_command(label='New', image=icons['new'], compound='left', hidemargin=True, command=lambda: self.root.new_timetable())
		file_menu.add_command(label='Load', image=icons['load'], compound='left', hidemargin=True, command=lambda: self.root.load_timetable())
		file_menu.add_separator(background='#D4D4D4')
		file_menu.add_cascade(label='Export', image=icons['export'], compound='left', hidemargin=True, menu=export_menu)
		file_menu.add_separator(background='#D4D4D4')
		file_menu.add_command(label='Settings', image=icons['settings'], compound='left', hidemargin=True, command=lambda: self.root.show_settings())
		file_menubutton.configure(menu=file_menu)

		## ------------------------------------------ Edit Menu -------------------------------------------
		edit_menubutton = tk.Menubutton(self, text='Edit', relief='flat', borderwidth=0, activebackground='#323232', image=self.root.pixel, compound='center', height=13, width=50, background=self.cget('background'), foreground='#D8DEE9', activeforeground='#D8DEE9', font=('Calibri', 13))
		edit_menubutton.grid(row=0, column=8, sticky='nswe', padx=(0, 1))
		edit_menu = tk.Menu(edit_menubutton, tearoff=0, background='#323232', relief='flat', foreground='#fff', borderwidth=0, activeborderwidth=0, type='normal')

		edit_menu.add_command(label='Undo', image=icons['undo'], compound='left', command=lambda: self.root.undo())
		edit_menu.add_command(label='Redo', image=icons['redo'], compound='left', command=lambda: self.root.redo())
		edit_menu.add_command(label='Undo All', image=icons['restore'], compound='left', command=lambda: self.root.undo_all())
		edit_menu.add_separator(background='#D4D4D4')
		edit_menu.add_command(label='New Event', image=icons['new_event'], compound='left', command=lambda: self.root.timetable.create_event())
		edit_menu.add_command(label='New Class', image=icons['new_class'], compound='left', command=lambda: self.root.timetable.new_class())
		edit_menu.add_separator(background='#D4D4D4')
		edit_menu.add_command(label='Delete Events', image=icons['delete_event'], compound='left', command=lambda: self.root.timetable.delete_event())
		edit_menu.add_command(label='Delete Class', image=icons['delete_class'], compound='left', command=lambda: self.root.timetable.delete_class())
		edit_menu.add_separator(background='#D4D4D4')
		edit_menu.add_command(label='Change Week Number', image=icons['calendar'], compound='left', command=lambda: self.root.timetable.change_week())
		edit_menubutton.configure(menu=edit_menu)

		## ------------------------------------------ About Menu ------------------------------------------
		about_menubutton = tk.Menubutton(self, text='About', relief='flat', borderwidth=0, activebackground='#323232', image=self.root.pixel, compound='center', height=13, width=50, background=self.cget('background'), foreground='#D8DEE9', activeforeground='#D8DEE9', font=('Calibri', 13))
		about_menubutton.grid(row=0, column=9, sticky='nswe', padx=(0, 1))
		about_menu = tk.Menu(about_menubutton, tearoff=0, background='#323232', relief='flat', foreground='#fff', borderwidth=10, activeborderwidth=0, type='normal')
		about_menu.add_command(label='About', image=icons['about'], compound='left', command=lambda: self.root.show_about())
		about_menu.add_command(label='Help', image=icons['help'], compound='left', command=lambda: self.root.show_help())
		about_menu.add_separator(background='#D4D4D4')
		about_menu.add_command(label='Report a Bug', image=icons['bug'], compound='left', command=lambda: self.root.report_bug())
		about_menu.add_command(label='Suggest a Feature', image=icons['feature'], compound='left', command=lambda: self.root.report_feature())
		about_menubutton.configure(menu=about_menu)

		self.filename_display = tk.Label(self, text=self.root.filename, background=self.cget('background'), foreground='#666', font=('Calibri', 10, 'bold'), anchor='center', image=self.root.pixel, compound='center')
		self.filename_display.grid(row=0, column=10, sticky='nswe', padx=(0, 1))


class FormattingOption(tk.Frame):
	"""
	A widget containing and displaying a line of formatting information for a reportlab Table style config

	:param root: (ExportAsPDFMenu) The export as pdf toplevel widget
	"""

	def __init__(self, root, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		self.root: ExportAsPDFMenu = root
		self.style_option = tk.StringVar(self)  # Define a stringvar for the selected style option

		## Create a dropdown to select the style option
		class_dropdown = CustomComboBox(self, style='TCombobox', textvariable=self.style_option, values=['GRID', 'ALIGN', 'VALIGN', 'FONT', 'TOPPADDING', 'FONTSIZE', 'TEXTCOLOR', 'BACKGROUND', 'SPAN', 'BOTTOMPADDING'])
		class_dropdown.pack(side='left', fill='y', padx=1, pady=1)

		tk.Frame(self, background='#000', width=12).pack(side='left', fill='y')  # Spacer

		## Top Left Corner
		tk.Label(self, background='#303841', foreground='#D8DEE9', text='X₁', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)

		self.x1_entry = ttk.Entry(self, style='stipple.TEntry', width=2, validate='focusout')
		self.x1_entry.configure(invalidcommand=lambda: self.invalid_input(self.x1_entry, 'Must be an integer within the bounds of the table.'), validatecommand=lambda v: self.validate_pos(self.x1_entry, 'x'))
		self.x1_entry.pack(side='left', fill='y', padx=(1, 0), pady=1)

		tk.Label(self, background='#303841', foreground='#D8DEE9', text='Y₁', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)

		self.y1_entry = ttk.Entry(self, style='stipple.TEntry', width=2, validate='focusout')
		self.y1_entry.configure(invalidcommand=lambda: self.invalid_input(self.y1_entry, 'Must be an integer within the bounds of the table.'), validatecommand=lambda v: self.validate_pos(self.y1_entry, 'y'))
		self.y1_entry.pack(side='left', fill='y', padx=(1, 1), pady=1)

		tk.Frame(self, background='#000', width=12).pack(side='left', fill='y')  # Spacer

		## Bottom Right Corner
		tk.Label(self, background='#303841', foreground='#D8DEE9', text='X₂', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)

		self.x2_entry = ttk.Entry(self, style='stipple.TEntry', width=2, validate='focusout')
		self.x2_entry.configure(invalidcommand=lambda: self.invalid_input(self.x2_entry, 'Must be an integer within the bounds of the table.'), validatecommand=lambda v: self.validate_pos(self.x2_entry, 'x'))
		self.x2_entry.pack(side='left', fill='y', padx=(1, 0), pady=1)

		tk.Label(self, background='#303841', foreground='#D8DEE9', text='Y₂', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)

		self.y2_entry = ttk.Entry(self, style='stipple.TEntry', width=2, validate='focusout')
		self.y2_entry.configure(invalidcommand=lambda: self.invalid_input(self.y2_entry, 'Must be an integer within the bounds of the table.'), validatecommand=lambda v: self.validate_pos(self.y2_entry, 'y'))
		self.y2_entry.pack(side='left', fill='y', padx=(1, 1), pady=1)

		tk.Frame(self, background='#000', width=12).pack(side='left', fill='y')  # Spacer

		## Value entry
		tk.Label(self, background='#303841', foreground='#D8DEE9', text='Value ', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)

		self.value_entry = ttk.Entry(self, style='stipple.TEntry', validate='focusout')
		self.value_entry.configure(invalidcommand=lambda: self.invalid_input(self.value_entry, 'Invalid Value'), validatecommand=lambda: self.validate_value())
		self.value_entry.pack(side='left', expand=True, fill='both', padx=(1, 1), pady=1)

		## Bind the widget’s children to select the widget when clicked
		self.bind_class(f'click:{id(self)}', '<Button-1>', lambda v: self.clicked())
		self.bindtags((f'click:{id(self)}', *self.bindtags()))
		for i in self.winfo_children():
			i.bindtags((f'click:{id(self)}', *i.bindtags()))

	def clicked(self) -> None:
		"""
		Selects / deselects the formatting option
		"""

		if self.root.selected_format_option == self:
			self.deselect()
			self.root.selected_format_option = None
		else:
			if self.root.selected_format_option is not None:
				self.root.selected_format_option.deselect()
			self.root.selected_format_option = self
			self.select()

	def select(self) -> None:
		""" Changes the background colour to a selected colour """
		self.configure(background='#F9AE58')

	def deselect(self) -> None:
		""" Changes the background colour to the normal colour """
		self.configure(background='#3B434C')

	def select_style_class(self) -> None:
		""" Adds template text to the value entry when the user selects the style option to edit """
		## Todo: This should add a formatting template to the value entry when a new style option is selected
		pass

	def validate_pos(self, elem: ttk.Entry, mode: Literal['x', 'y']) -> bool:
		"""
		Validates that the X or Y position in the input entry are within the bounds of the table.

		:param elem: The entry whose value to check
		:param mode: Whether to treat the value as an X coordinate or Y coordinate

		:return: Whether or not the input value is an integer within the bounds of the table
		"""

		val = elem.get()  # Get the contents of the entry
		if not val.removeprefix('-').isnumeric():  # Check if the value is an integer
			return False

		## Validate the coordinate is within the bounds of the table
		if mode == 'x':
			return -7 <= int(val) <= 6
		else:
			return -(len(self.root.timetable_data['sessions'])) <= int(val) <= (len(self.root.timetable_data['sessions']) - 1)

	@staticmethod
	def invalid_input(elem: tk.Entry, text: str) -> None:
		"""
		This function is called when an input into an entry does not pass validation.
		It sets the cursor back into the entry and displays a message to the user.

		:param elem: The entry to set the cursor into
		:param text: The message to display to the user
		"""

		cursor_pos = elem.index(tk.INSERT)
		mb.showinfo('Invalid Input', text)
		elem.focus()
		elem.icursor(cursor_pos)

	def validate_value(self) -> bool:
		"""
		Evaluate the contents of the value entry as python code and validate the result.
		"""

		val = self.value_entry.get()  # Get the contents of the value entry

		try:  # Attempt to evaluate the value
			eval(f'[{val}]')
			return True
		except Exception:
			return False


## todo: add font, colours, margin, to export PDF

class VerticalText(Flowable):
	"""
	Rotates a text in a table cell.
	From: https://stackoverflow.com/a/40349017

	:param text: The text to display
	:bottompadding: The spacing on the bottom of the text that becomes the padding on the right-hand side.
	"""

	def __init__(self, text: str, bottompadding: float | int = 0) -> None:
		Flowable.__init__(self)
		self.text = text
		self.bottompadding = bottompadding

	def draw(self) -> None:
		"""
		Add the text to the canvas
		"""

		canvas = self.canv
		canvas.rotate(90)
		fs = canvas._fontsize
		canvas.translate(1, -fs / 1.2)  # canvas._leading?
		canvas.drawString(0, self.bottompadding, self.text)

	def wrap(self, a_w: float, a_h: float) -> tuple[float, float]:
		"""
		Wrap the text on the canvas
		"""

		canv = self.canv
		fn, fs = canv._fontname, canv._fontsize
		return canv._leading, 1 + canv.stringWidth(self.text, fn, fs)


class Entry(ttk.Entry):
	"""
	A ttk entry with some custom methods and parameters that allow for cleaner coding
	"""

	def __init__(self, *args, **kwargs) -> None:
		default_val = kwargs.pop('text') if 'text' in kwargs else None  # Get the default text to use
		super().__init__(*args, **kwargs)

		if default_val is not None:
			self.insert(0, default_val)  # Add the default text to the entry

	def set(self, value: str) -> None:
		"""
		Set the contents of the entry to the input string

		:param value: The string to set
		"""

		self.delete(0, tk.END)
		self.insert(0, value)

	def replace(self, start: int | str, end: int | str, value: str) -> None:
		"""
		Replace a range of characters with the input string

		:param start: The starting index of the characters to replace
		:param end: The ending index of the characters to replace
		:param value: The string to insert
		"""

		self.delete(start, end)
		self.insert(start, value)


class ScrollableFrame:
	"""
	A frame that can be scrolled horizontally and vertically and scales based on the size of its contents

	Config for the outer (static) container can be defined by specifying arguments with the prefix "c_" and config for the inner (scrollable) container can be defined by specifying arguments with the prefix "f_".

	:param master: The parent widget
	"""

	def __init__(self, master, **kwargs) -> None:
		## Get the scrollbars
		hscrollbar: tk.Scrollbar = kwargs.pop('hscrollbar') if 'hscrollbar' in kwargs else None
		vscrollbar: tk.Scrollbar = kwargs.pop('vscrollbar') if 'vscrollbar' in kwargs else None

		## Get the config kwargs for the scrolling frame and canvas based on their respective prefix
		canvas_config = {k.removeprefix('c_'): v for k, v in kwargs.items() if k.startswith('c_')}
		frame_config = {k.removeprefix('f_'): v for k, v in kwargs.items() if k.startswith('f_')}

		## Create a canvas element to hold the scrolling frame
		self.canvas = tk.Canvas(master, **canvas_config)
		self.grid = self.canvas.grid

		## Bind the scrollbar(s) if they exist
		if vscrollbar is not None:
			self.canvas.configure(yscrollcommand=vscrollbar.set)
			vscrollbar.configure(command=self.canvas.yview)

		if hscrollbar is not None:
			self.canvas.configure(xscrollcommand=hscrollbar.set)
			hscrollbar.configure(command=self.canvas.xview)

		## Reset the scroll position of the widget.
		self.canvas.xview_moveto(0)
		self.canvas.yview_moveto(0)

		## Create a frame to be scrolled
		self.frame = tk.Frame(self.canvas, **frame_config)

		## Add the frame to the canvas
		self._scrollable_frame = self.canvas.create_window(0, 0, window=self.frame, anchor='nw')

		## Bind changes in size for both components to the appropriate functions
		self.frame.bind('<Configure>', lambda v: self._configure_interior())
		self.canvas.bind('<Configure>', lambda v: self._configure_canvas())

	def _configure_interior(self) -> None:
		"""
		Update the canvas scroll region to match the size of the scrolling frame and update the width of the canvas to match the scrolling frame

		From: https://stackoverflow.com/a/16198198
		"""

		# Update the scrollbars to match the size of the inner frame.
		self.canvas.config(scrollregion=(0, 0, self.frame.winfo_reqwidth(), self.frame.winfo_reqheight()))
		if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
			# Update the canvas’s width to fit the inner frame.
			self.canvas.config(width=self.frame.winfo_reqwidth())

	def _configure_canvas(self) -> None:
		"""
		Update the width of the scrolling frame to match the canvas

		From: https://stackoverflow.com/a/16198198
		"""

		if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
			# Update the inner frame’s width to fill the canvas.
			self.canvas.itemconfigure(self._scrollable_frame, width=self.canvas.winfo_width())


class ExportAsPDFMenu(tk.Toplevel):
	"""
	A window that allows converting a timetable file to PDF and configuring the formatting of the resulting PDF.

	:param root: (Window) The root window widget
	"""

	def __init__(self, root, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.root: Window = root

		self.attributes('-topmost', True)  # Set the window to the topmost window
		self.grab_set()  # Disable interaction with the main window until this window is closed
		self.title('Convert to PDF')  # Set the title of the window
		self.geometry(f'+{self.root.winfo_x() + int(self.root.winfo_width() // 3)}+{self.root.winfo_y() + int(self.root.winfo_height() // 3)}')  # Set the position of the window to roughly the centre of the main window
		self.root.call('wm', 'iconphoto', str(self), self.root.icons['window_icon2'])  # Set the icon of the window

		self.configure(background='#222', padx=1, pady=1)  # Set the background colour and internal padding of the window
		self.columnconfigure(2, weight=1)
		self.rowconfigure(10, weight=1)

		self.selected_format_option: Optional[FormattingOption] = None
		self.formatting_elems: list[FormattingOption] = []

		## Load the current timetable
		self.timetable_data: Optional[dict] = None

		with open(self.root.filename, encoding='utf-8') as input_file:
			timetable = json.load(input_file)
			self.timetable_data = timetable

		## Define basic style elements
		self.tablestyle = [
			('SPAN', (-2, 2), (-2, -1)),
			('SPAN', (-1, 2), (-1, -1)),
		]

		## Layout formatting presets for the output PDF. Other presets can be added here and be used by the program
		self.preset_options = {
			# Preset Name   |  Width | Height | Table width | Table height | Horizontal margin | Vertical margin | Size units | Table size units | Margin Units  # noqa
			'2x1 Timetable' : (22,     12,      'Auto',       'Auto',        1.0,                1.0,              'cm',        'cm',              'cm'),        # noqa
			'A4 (Portrait)' : (29.7,   40,      'Auto',       'Auto',        1.5,                1.5,              'cm',        'cm',              'cm'),        # noqa
			'A5 (Portrait)' : (21,     29.7,    'Auto',       'Auto',        1.5,                1.5,              'cm',        'cm',              'cm'),        # noqa
			'A4 (Landscape)': (29.7,   40,      'Auto',       'Auto',        1.0,                1.0,              'cm',        'cm',              'cm'),        # noqa
			'A5 (Landscape)': (21,     29.7,    'Auto',       'Auto',        1.0,                1.0,              'cm',        'cm',              'cm'),        # noqa
		}

		## Define default formatting for each part of the output timetable
		self.formatting = {
			'first_row': {
				'BACKGROUND': '#D3D3D3',
				'FOREGROUND': '#000000',
				'GRID': (1, '#000000'),
				'FONT': ('Calibri-Bold',),
				'FONTSIZE': 'Auto',
				'ORIENT': 'horizontal',
				'ALIGN': ('CENTER',),
				'VALIGN': ('MIDDLE',),
				'BOTTOMPADDING': (0,),
			},

			'first_column': {
				'BACKGROUND': '#D3D3D3',
				'FOREGROUND': '#000000',
				'GRID': (1, '#000000'),
				'FONT': ('Calibri-Bold',),
				'FONTSIZE': 'Auto',
				'ORIENT': 'vertical',
				'ALIGN': ('CENTER',),
				'VALIGN': ('MIDDLE',),
				'BOTTOMPADDING': (0,),
			},

			'break': {
				'BACKGROUND': '#D3D3D3',
				'FOREGROUND': '#000000',
				'GRID': (0.5, '#000000'),
				'FONT': ('Calibri-Bold',),
				'FONTSIZE': 'Auto',
				'ORIENT': 'horizontal',
				'ALIGN': ('CENTER',),
				'VALIGN': ('MIDDLE',),
				'BOTTOMPADDING': (0,),
			},

			'sessionname': {
				'BACKGROUND': '#FFFFFF',
				'FOREGROUND': '#000000',
				'GRID': (0.5, '#000000'),
				'FONT': ('Calibri-Bold',),
				'FONTSIZE': 'Auto',
				'ORIENT': 'horizontal',
				'ALIGN': ('CENTER',),
				'VALIGN': ('MIDDLE',),
				'BOTTOMPADDING': (0,),
			},

			'body': {
				'BACKGROUND': '#FFFFFF',
				'FOREGROUND': '#000000',
				'GRID': (0.5, '#000000'),
				'FONT': ('Calibri',),
				'FONTSIZE': 'Auto',
				'ORIENT': 'horizontal',
				'ALIGN': ('CENTER',),
				'VALIGN': ('MIDDLE',),
				'BOTTOMPADDING': (0,),
			}
		}

		## Define default formatting for UI elements
		labelconfig = dict(background='#303841', foreground='#D8DEE9', image=self.root.pixel, font=('Calibri', 11), compound='center', height=14)
		buttonconfig = dict(background='#303841', foreground='#D8DEE9', activebackground='#2E3238', mouseoverbackground='#3B434C', font=('Calibri', 11), compound='center', highlightbackground='#4F565E')

		## ======================================== User Interface ========================================

		## ---------------------------------------- Filename input ----------------------------------------
		outfile_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		outfile_frame.grid(row=0, column=0, columns=3, sticky='NSWE', padx=0, pady=(0, 0))
		outfile_frame.columnconfigure(1, weight=1)

		tk.Label(outfile_frame, text='Output File', width=60, **labelconfig).grid(row=0, column=0, sticky='NSWE', padx=(0, 1), pady=0)

		self.outfile_entry = Entry(outfile_frame, text=self.root.filename.removesuffix('.json').removesuffix('.txt') + '.pdf', style='stipple.TEntry')
		self.outfile_entry.grid(row=0, column=1, sticky='NSWE', padx=(0, 1), pady=0)

		MouseoverButton(outfile_frame, command=lambda: self.browse_filename(), image=self.root.icons['load'], width=25, height=20, **buttonconfig).grid(row=0, column=2, sticky='nswe', padx=(0, 0), pady=0)

		## ----------------------------------------- Page Options -----------------------------------------
		page_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		page_options_frame.grid(row=1, column=0, sticky='nswe', padx=0, pady=(7, 0))

		tk.Label(page_options_frame, text='Page Size', **labelconfig).pack(side='top', padx=(0, 0), pady=(0, 1), fill='x')
		tk.Frame(page_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		self.presets_selector = CustomComboBox(page_options_frame, state='readonly', style='TCombobox', values=list(self.preset_options.keys()), width=5)
		self.presets_selector.pack(side='top', padx=(0, 0), pady=(0, 1), fill='x')
		self.presets_selector.bind('<<ComboboxSelected>>', lambda v: self.select_preset())
		self.presets_selector.set('A4 (Portrait)')

		self.width_entry = Entry(page_options_frame, text='29.7', style='stipple.TEntry', width=5)
		self.width_entry.configure(validatecommand=lambda: self.validate_num(self.width_entry), validate='focusout', invalidcommand=lambda: self.invalid_input(self.width_entry, 'TODO'))
		self.width_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')

		tk.Label(page_options_frame, text='x', width=10, **labelconfig).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.height_entry = Entry(page_options_frame, text='40', style='stipple.TEntry', width=5)
		self.height_entry.configure(validatecommand=lambda: self.validate_num(self.height_entry), validate='focusout', invalidcommand=lambda: self.invalid_input(self.height_entry, 'TODO'))
		self.height_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')

		self.page_units = CustomComboBox(page_options_frame, state='readonly', style='TCombobox', values=['px', 'pt', 'cm', 'mm', 'in'], width=3)
		self.page_units.pack(side='left', padx=0, pady=0, fill='both')
		self.page_units.set('cm')

		## ----------------------------------------- Table Options ----------------------------------------
		table_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		table_options_frame.grid(row=2, column=0, sticky='nswe', padx=0, pady=(7, 0))

		tk.Label(table_options_frame, text='Table Size', **labelconfig).pack(side='top', anchor='w', padx=0, pady=0, fill='x')
		tk.Frame(table_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		self.table_width_entry = Entry(table_options_frame, text='Auto', style='stipple.TEntry', width=5)
		self.table_width_entry.configure(validatecommand=lambda: self.validate_num(self.table_width_entry, special_vals=['Auto']), validate='focusout', invalidcommand=lambda: self.invalid_input(self.table_width_entry, 'TODO'))
		self.table_width_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')

		tk.Label(table_options_frame, text='x', width=10, **labelconfig).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.table_height_entry = Entry(table_options_frame, text='Auto', style='stipple.TEntry', width=5)
		self.table_height_entry.configure(validatecommand=lambda: self.validate_num(self.table_height_entry, special_vals=['Auto']), validate='focusout', invalidcommand=lambda: self.invalid_input(self.table_height_entry, 'TODO'))
		self.table_height_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')

		self.table_units = CustomComboBox(table_options_frame, state='readonly', style='TCombobox', values=['px', 'pt', 'cm', 'mm', 'in', '%'], width=3)
		self.table_units.pack(side='left', padx=0, pady=0, fill='both')
		self.table_units.set('cm')

		## ---------------------------------------- Margin Options ----------------------------------------
		margin_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		margin_options_frame.grid(row=3, column=0, sticky='nswe', padx=0, pady=(7, 0))

		tk.Label(margin_options_frame, text='Margins', **labelconfig).pack(side='top', padx=0, pady=(0, 0), fill='x')
		tk.Frame(margin_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		tk.Label(margin_options_frame, text='↔', width=15, **labelconfig).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.h_margin_entry = Entry(margin_options_frame, text='1.5', style='stipple.TEntry', width=5)
		self.h_margin_entry.configure(validatecommand=lambda: self.validate_num(self.h_margin_entry), validate='focusout', invalidcommand=lambda: self.invalid_input(self.h_margin_entry, 'TODO'))
		self.h_margin_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')

		tk.Label(margin_options_frame, text='↕', width=15, **labelconfig).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.v_margin_entry = Entry(margin_options_frame, text='1.5', style='stipple.TEntry', width=5)
		self.v_margin_entry.configure(validatecommand=lambda: self.validate_num(self.v_margin_entry), validate='focusout', invalidcommand=lambda: self.invalid_input(self.v_margin_entry, 'TODO'))
		self.v_margin_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')

		self.margin_units = CustomComboBox(margin_options_frame, state='readonly', style='TCombobox', values=['px', 'pt', 'cm', 'mm', 'in', '%'], width=3)
		self.margin_units.pack(side='left', padx=0, pady=0, fill='both')
		self.margin_units.set('cm')

		## ------------------------------------ Bottom Padding Options ------------------------------------
		## Note: Changing the font size of the text causes """unique""" behaviour with vertical alignment, so this option exists to adjust it.
		bottompad_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		bottompad_options_frame.grid(row=4, column=0, sticky='nswe', padx=0, pady=(7, 0))

		tk.Label(bottompad_options_frame, text='Bottom Padding', **labelconfig).pack(side='top', padx=0, pady=(0, 0), fill='x')
		tk.Frame(bottompad_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		self.bottom_padding_0 = Entry(bottompad_options_frame, text='5', style='stipple.TEntry', width=5)
		self.bottom_padding_0.configure(validatecommand=lambda: self.validate_num(self.bottom_padding_0), validate='focusout', invalidcommand=lambda: self.invalid_input(self.bottom_padding_0, 'TODO'))
		self.bottom_padding_0.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')

		self.bottom_padding_1 = Entry(bottompad_options_frame, text='15', style='stipple.TEntry', width=5)
		self.bottom_padding_1.configure(validatecommand=lambda: self.validate_num(self.bottom_padding_1), validate='focusout', invalidcommand=lambda: self.invalid_input(self.bottom_padding_1, 'TODO'))
		self.bottom_padding_1.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')

		self.bottom_padding_2 = Entry(bottompad_options_frame, text='25', style='stipple.TEntry', width=5)
		self.bottom_padding_2.configure(validatecommand=lambda: self.validate_num(self.bottom_padding_2), validate='focusout', invalidcommand=lambda: self.invalid_input(self.bottom_padding_2, 'TODO'))
		self.bottom_padding_2.pack(side='left', padx=(0, 0), pady=0, expand=True, fill='both')

		## ------------------------------------ Corner Rounding Options -----------------------------------
		round_corner_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		round_corner_options_frame.grid(row=5, column=0, sticky='nswe', padx=0, pady=(7, 0))

		tk.Label(round_corner_options_frame, text='Round Corners', **labelconfig).pack(side='top', padx=0, pady=(0, 0), fill='x')
		tk.Frame(round_corner_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		self.corner_units = CustomComboBox(round_corner_options_frame, state='readonly', style='TCombobox', values=['px', 'pt', 'cm', 'mm', 'in', '%'], width=3)
		self.corner_units.pack(side='top', padx=0, pady=(0, 1), fill='both')
		self.corner_units.set('cm')

		corner_radius_entry_frame = tk.Frame(round_corner_options_frame, background='#3B434C')
		corner_radius_entry_frame.pack(side='top', expand=True, fill='both')

		tk.Label(corner_radius_entry_frame, text='◴', **labelconfig, width=10).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.nw_corner_radius = Entry(corner_radius_entry_frame, text='2.5', style='stipple.TEntry', width=5)
		self.nw_corner_radius.configure(validatecommand=lambda: self.validate_corner(self.nw_corner_radius), validate='focusout', invalidcommand=lambda: self.invalid_input(self.nw_corner_radius, 'TODO'))
		self.nw_corner_radius.pack(side='left', padx=(0, 1), expand=True, fill='both')

		tk.Label(corner_radius_entry_frame, text='◷', **labelconfig, width=10).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.ne_corner_radius = Entry(corner_radius_entry_frame, text='2.5', style='stipple.TEntry', width=5)
		self.ne_corner_radius.configure(validatecommand=lambda: self.validate_corner(self.ne_corner_radius), validate='focusout', invalidcommand=lambda: self.invalid_input(self.ne_corner_radius, 'TODO'))
		self.ne_corner_radius.pack(side='left', padx=(0, 0), expand=True, fill='both')

		corner_radius_entry_frame = tk.Frame(round_corner_options_frame, background='#3B434C')
		corner_radius_entry_frame.pack(side='top', expand=True, fill='both')

		tk.Label(corner_radius_entry_frame, text='◵', **labelconfig, width=10).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.sw_corner_radius = Entry(corner_radius_entry_frame, text='2.5', style='stipple.TEntry', width=5)
		self.sw_corner_radius.configure(validatecommand=lambda: self.validate_corner(self.sw_corner_radius), validate='focusout', invalidcommand=lambda: self.invalid_input(self.sw_corner_radius, 'TODO'))
		self.sw_corner_radius.pack(side='left', padx=(0, 1), expand=True, fill='both')

		tk.Label(corner_radius_entry_frame, text='◶', **labelconfig, width=10).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.se_corner_radius = Entry(corner_radius_entry_frame, text='2.5', style='stipple.TEntry', width=5)
		self.se_corner_radius.configure(validatecommand=lambda: self.validate_corner(self.se_corner_radius), validate='focusout', invalidcommand=lambda: self.invalid_input(self.se_corner_radius, 'TODO'))
		self.se_corner_radius.pack(side='left', padx=(0, 0), expand=True, fill='both')

		self.match_corner_radius = tk.BooleanVar(self, True)
		ttk.Checkbutton(round_corner_options_frame, style='Custom.TCheckbutton', text='Match Radius', variable=self.match_corner_radius).pack(side='top', fill='both', pady=(0, 1))

		## -------------------------------- Advanced Formatting Input Frame -------------------------------
		## A frame that allows direct editing of the table style options.
		frame = tk.Frame(self, background='#222')
		frame.grid(row=1, column=1, columns=1, rows=5, sticky='NSWE', padx=(10, 0), pady=(7, 0))
		frame.rowconfigure(1, weight=1)
		frame.columnconfigure(1, weight=1, minsize=500)

		tk.Label(frame, text='Advanced Formatting', **labelconfig, highlightthickness=1, highlightbackground='#3B434C').grid(row=0, column=0, columns=3, sticky='NSWE', pady=(0, 1))

		self.vscrollbar = ttk.Scrollbar(frame, orient='vertical', style='Custom.Vertical.TScrollbar')
		self.vscrollbar.grid(row=1, column=2, sticky='ns', padx=(0, 0), pady=0)

		self.scrollable_frame = ScrollableFrame(frame, vscrollbar=self.vscrollbar, c_highlightthickness=1, c_background='#000', c_highlightbackground='#3B434C', f_background='#000')
		self.scrollable_frame.grid(row=1, column=0, columns=2, sticky='NSWE', padx=(0, 1), pady=0)

		MouseoverButton(frame, text='+', command=lambda: self.add_formatting(), image=self.root.pixel, width=18, height=18, highlightthickness=1, **buttonconfig).grid(row=2, column=0, sticky='nw', padx=(0, 1), pady=(1, 0))
		MouseoverButton(frame, text='-', command=lambda: self.remove_formatting(), image=self.root.pixel, width=18, height=18, highlightthickness=1, **buttonconfig).grid(row=2, column=1, sticky='nw', padx=(0, 0), pady=(1, 0))

		## Add existing formatting options to the formatting options frame
		for i in self.tablestyle:
			elem = FormattingOption(self, self.scrollable_frame.frame, background='#3B434C')
			elem.pack(side='top', fill='x', padx=1, pady=(1, 0))
			elem.style_option.set(i[0])
			elem.x1_entry.insert(0, str(i[1][0]))
			elem.x2_entry.insert(0, str(i[2][0]))
			elem.y1_entry.insert(0, str(i[1][1]))
			elem.y2_entry.insert(0, str(i[2][1]))
			elem.value_entry.insert(0, str(list(i[3:]))[1:-1])

			self.formatting_elems.append(elem)

		## ------------------------------------ Cancel and Export Buttons ---------------------------------

		frame = tk.Frame(self, background='#222')
		frame.grid(row=6, column=1, sticky='NSE', pady=(0, 0))

		MouseoverButton(frame, text='Cancel', command=lambda: self.destroy(), image=self.root.pixel, width=50, height=18, highlightthickness=1, **buttonconfig).pack(side='left', padx=0, fill='y')  # .grid(row=1, column=1, sticky='nswe', padx=(0, 1), pady=(0, 0))
		MouseoverButton(frame, text='Export', command=lambda: self.convert(), image=self.root.pixel, width=50, height=18, highlightthickness=1, **buttonconfig).pack(side='left', padx=(1, 0), fill='y')  # .grid(row=1, column=0, sticky='nswe', padx=(0, 1), pady=(0, 0))

	def select_preset(self) -> None:
		"""
		Sets the values of all page formatting entries when a preset is selected from the dropdown
		"""

		## Get the preset name and data
		preset_name = self.presets_selector.get()
		preset_data = self.preset_options[preset_name]

		## Get the widgets to update (in order)
		elems = [
			self.width_entry,
			self.height_entry,
			self.table_width_entry,
			self.table_height_entry,
			self.h_margin_entry,
			self.v_margin_entry,
			self.page_units,
			self.table_units,
			self.margin_units
		]

		## Update each widget
		for elem, i in zip(elems, preset_data):
			elem.set(i)

	def browse_filename(self) -> None:
		""" Open an 'open file' dialogue and set the outfile entry to the chosen file """

		filename = fd.askopenfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.root.filename), initialfile=self.root.filename, parent=self)
		if filename:  # If a file was chosen, update the outfile entry.
			self.outfile_entry.set(filename)

	@staticmethod
	def invalid_input(element: Entry, text: str) -> None:
		"""
		This function is called when an input into an entry does not pass validation.
		It sets the cursor back into the entry and displays a message to the user.

		:param element: The entry to set the cursor into
		:param text: The message to display to the user
		"""

		cursor_pos = element.index(tk.INSERT)
		mb.showinfo('Invalid Input', text)
		element.focus()
		element.icursor(cursor_pos)

	@staticmethod
	def validate_num(elem: Entry, dtype=float, allow_negative: bool = False, special_vals: Optional[list[str]] = None) -> bool:
		"""
		Evaluates a number or simple equation in an entry widget and validates the result based on the input parameters.
		Sets the value of the entry to the evaluated string if the string is valid.

		:param elem: The entry from which to get the string to validate.
		:param dtype: The data type that the evaluated string should match.
		:param allow_negative: Weather or not to allow the result to be negative.
		:param special_vals: An optional list of values for which to skip validation and always return `True`.
							 This parameter should be a list of strings in Title Case or `None`.

		:return: Whether or not the value in the entry is valid.
		"""

		value = elem.get()  # Get the string to validate
		if special_vals is not None:  # Check if the string matches any of the `special vals`
			if value.title().strip(' \t\n') in special_vals:
				elem.set(value.title().strip(' \t\n'))
				return True

		if value.strip('0123456789.+-/*() '):  # Check for invalid characters
			return False
		else:
			## Attempt to evaluate the string
			try:
				value = eval(value)
				if type(value) is not dtype:  # If the resulting value does not match the valid data type
					## Allow integers to be used as floats
					if dtype is float and type(value) is int:  # If the valid data type is `float` and the evaluated data type is `int` convert the result to a float
						value = float(value)
					else:  # Otherwise, return that the input is invalid.
						return False

				if not allow_negative and value < 0:  # If the result is negative, and negatives are not allowed, return that the result is invalid
					return False
				else:  # Otherwise, set the value of the entry to the evaluated string and return that the input is valid.
					elem.set(str(value))
					return True
			except Exception:  # If the program fails to evaluate the input string, return that the input is invalid. Note: the `eval` function runs any python code, so the exception could be anything.
				return False

	def convert(self) -> None:
		"""
		Converts a timetable file to a table in a PDF
		"""
		# if append:
		# 	canvas = Canvas(dir_name + '/img2pdf_tmp.pdf', (doc_w, doc_h))
		# else:

		## Get the filename of the output pdf
		output_filename = self.outfile_entry.get()
		if not output_filename.endswith('.pdf'):
			output_filename += '.pdf'

		## If the output file already exists, check for permission to write.
		if file_exists(output_filename):
			permission_error = True
			while permission_error:
				try:
					open(output_filename, 'w').close()  # Attempt to write to the file
					permission_error = False
				except PermissionError:
					ans = mb.askretrycancel('Permission Denied', f'Could not save {os.path.basename(output_filename)}, because it is open\nin another program.')  # Warn the user that the file is open in another program
					if not ans:  # If the user presses the 'x' or 'cancel' buttons, stop the function.
						return

		self.tablestyle = []  # Define an array for the table style options

		data = [['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']]  # Define an array for the table text data

		sessionname_idxs = [((-2, 1), (-1, -1))]  # Define a list for the indexes of 'session name' cells
		break_idxs = []  # Define a list for the indexes of the 'session break' cells
		break_count = 0  # Define a counter for the number of 'break' cells
		v_header_indexes = []  # Define a list for the indexes of the session name headers

		## Iterate through each session in the timetable data
		for n, i in enumerate(self.timetable_data['sessions']):
			if i[1]:  # If the session is not a session break
				## Add the indexes of the session name and session header to their respective lists
				sessionname_idxs.append([(1, len(data)), (-3, len(data))])
				v_header_indexes.append([(0, len(data)), (0, len(data) + 2)])

				self.tablestyle.append(('SPAN', (0, len(data)), (0, len(data) + 2)))  # Configure the session header to span three rows

				line_data = [[i[0]], [''], ['']]  # Initiate a list for the row’s text with the values of the first column

				## Add the text for each class in the session’s time slot to the text list
				for day_num, day in enumerate(self.timetable_data['timetable']):
					class_index = day[n - break_count]
					line_data[0].append(self.timetable_data['classes'][class_index])
					line_data[1].append(self.timetable_data['teachers'][class_index])
					line_data[2].append(self.timetable_data['rooms'][class_index])

				data.extend(line_data)  # Add the session text to the table data
			else:  # Otherwise (the session is a break)
				break_count += 1  # Increment the number of breaks
				break_idxs.append([(0, len(data)), (-3, len(data))])  # Add the indexes of the break to the respective list

				self.tablestyle.append(('SPAN', (0, len(data)), (-3, len(data))))  # Configure the table to span to the 1st to 3rd last columns
				data.append(i[0])  # Add the break text to the table data

		data[1].extend(['Homework'] * 2)  # Add the text for saturday and sunday

		page_unit = {'cm': units.cm, 'mm': units.mm, 'pt': units.pica, 'px': 1, 'in': units.inch}[self.page_units.get()]  # Get the multiplier corresponding to the units selected for the page size

		## Calculate the document dimensions
		doc_w = float(self.width_entry.get()) * page_unit
		doc_h = float(self.height_entry.get()) * page_unit

		## Calculate the size of the margins for the document
		if self.margin_units.get() == '%':  # If the input value is a percentage, calculate the margins as a percentage of the document dimensions
			margin = [doc_w * (float(self.h_margin_entry.get()) / 100), doc_h * (float(self.v_margin_entry.get()) / 100)]
		else:
			margin_unit = {'cm': units.cm, 'mm': units.mm, 'pt': units.pica, 'px': 1, 'in': units.inch}[self.page_units.get()]  # Get the multiplier for the units selected for the margins
			margin = [float(self.h_margin_entry.get()) * margin_unit, float(self.v_margin_entry.get()) * margin_unit]  # Calculate the margins

		table_unit = {'cm': units.cm, 'mm': units.mm, 'pt': units.pica, 'px': 1, 'in': units.inch, '%': 1}[self.table_units.get()]  # Get the multiplier for the units selected for the table size. '%' is given a multiplier of 1 as a placeholder

		if self.table_width_entry.get().lower() == 'auto':  # If the table width is 'Auto', set the table width to the document width minus the margins
			tablewidth = doc_w - margin[0] * 2
		else:
			if self.table_units.get() == '%':  # Otherwise, if the selected unit is '%', calculate the table width as a percentage of the document width, minus the margins.
				tablewidth = (doc_w - margin[0] * 2) * (float(self.table_width_entry.get()) / 100)
			else:
				tablewidth = float(self.table_width_entry.get()) * table_unit  # Calculate the table width

		if self.table_height_entry.get().lower() == 'auto':  # If the table height is 'Auto', set the table height to the document height minus the margins
			tableheight = doc_h - margin[1] * 2
		else:
			if self.table_units.get() == '%':  # Otherwise, if the selected unit is '%', calculate the table height as a percentage of the document height, minus the margins.
				tableheight = (doc_h - margin[1] * 2) * (float(self.table_height_entry.get()) / 100)
			else:
				tableheight = float(self.table_height_entry.get()) * table_unit  # Calculate the table height

		## todo: add column and row size distribution to export config

		cw = [0.055] + [0.135] * 7  # Get relative column widths
		cw = [v * tablewidth for v in cw]  # Multiply the relative column widths by the table width

		rows = len(data) - 1  # Calculate the number of rows in the table
		header_column_width = cw[0] / tableheight  # Get the pixel size of the first column’s width as a percentage of the table height so the first row and first column can be the same size
		rh = [header_column_width] + [(1 - header_column_width) / rows] * rows  # Get the relative row heights
		rh = [v * tableheight for v in rh]  # Multiply the relative row heights by the table height

		font_sizes = dict()  # Define a dictionary to store the maximum font size corresponding to a certain height

		## Register the fonts to use
		pdfmetrics.registerFont(TTFont(f'Calibri-Bold', 'calibrib.ttf'))
		pdfmetrics.registerFont(TTFont(f'Calibri', 'calibri.ttf'))

		## Loop through the formatting options and the indexes of the row with the height to fit to.
		for key, row in [('first_row', 0), ('first_column', 1), ('body', 1), ('sessionname', 1), ('break', 1)]:
			if self.formatting[key]['FONTSIZE'] == 'Auto':
				height = rh[row]  # Get the height at the formating option’s row index
				font = self.formatting[key]['FONT'][0]  # Get the font of the formatting option

				if f'{height}.{font}' not in font_sizes:  # Check if the font size has already been calculated for the font name and row height
					font_size = 1  # Declare a variable for the font size

					face = pdfmetrics.getFont(font).face  # Get the size of the font size
					face = (face.ascent - face.descent) / 1000  # Get the difference between the font’s ascent and descent

					while face * (font_size + 0.5) < height / 2:  # While if the height of the font at the current size, plus 0.5, is less than half the available height.
						font_size += 0.5  # Add 0.5 to the current font size
					font_sizes.update({f'{height}.{font}': font_size})  # Add the calculated font size to the dictionary, indexed by the available height and face name

		## Add the formatting options for each cell type
		for key, ranges in [('body', [((1, 1), (-3, -1))]), ('first_row', [((0, 0), (-1, 0))]), ('first_column', v_header_indexes), ('sessionname', sessionname_idxs), ('break', break_idxs)]:  # For each of the style options and their calculated ranges
			for pos in ranges:  # Iterate through each index of the current cell type
				for k, v in self.formatting[key].items():  # Iterate through each style option and the corresponding value for the cell type
					## Match the style option
					match k:
						case 'FONTSIZE':
							if v == 'Auto':  # If the font size is 'Auto', use the pre-calculated font size for the height
								if key == 'first_row':
									font_size = font_sizes[str(rh[0]) + '.' + self.formatting[key]['FONT'][0]]
								else:
									font_size = font_sizes[str(rh[1]) + '.' + self.formatting[key]['FONT'][0]]
							else:  # Otherwise, use the font size as is.
								font_size = float(v)
							self.tablestyle.append((k, *pos, font_size))  # Add the font size formatting to the table style array
						case 'ORIENT':
							if v.lower() == 'vertical':  # If the orientation is vertical
								updated_lines = []  # Declare an empty array to hold the updated text
								for y in data[pos[0][1]:pos[1][1] + (1 if pos[1][1] >= 0 else -1)]:  # Iterate through the rows in the current index range
									line = y  # Copy the current row
									vertical_slice = slice(pos[0][0], pos[1][0] + (1 if pos[1][0] >= 0 else -1))  # Pre-calculate a slice for the columns in the current index range
									line[vertical_slice] = [x if x.strip('\n\t ') == '' else VerticalText(x, self.formatting[key]['BOTTOMPADDING'][0]) for x in line[vertical_slice]]  # Iterate through the columns in the current index range and convert the string to a VerticalText widget if it is not empty. Insert the result into the current line
									updated_lines.append(line)  # Add the current line into the `updated_lines` array
								data[pos[0][1]:pos[1][1] + (1 if pos[1][1] >= 0 else -1)] = updated_lines  # Replace the lines in the current index range in the data array with the corresponding lines in the `updated_lines` array
						case 'BOTTOMPADDING':
							if self.formatting[key]['ORIENT'].lower() != 'vertical':  # If the orientation is not vertical, add the bottom padding to the style config (If the orientation is vertical, the bottom padding is added to the VerticalText class)
								self.tablestyle.append((k, *pos, *v))
						## Calculate the colour object using the input hex data and add the result to the table style array
						case 'GRID':
							self.tablestyle.append((k, *pos, v[0], HexColor(v[1])))
						case 'BACKGROUND':
							self.tablestyle.append((k, *pos, HexColor(v)))
						case 'FOREGROUND':
							self.tablestyle.append((k, *pos, HexColor(v)))
						case _:
							self.tablestyle.append((k, *pos, *v))

		corner_unit = {'cm': units.cm, 'mm': units.mm, 'pt': units.pica, 'px': 1, 'in': units.inch, '%': min(tablewidth, tableheight) / 200}[self.corner_units.get()]  # Get the multiplier for the units selected for the table size. '%' is calculated as a percentage of half of the shortest side length of the page (the maximum possible radius)
		corners = [float(i.get()) * corner_unit for i in [self.nw_corner_radius, self.ne_corner_radius, self.sw_corner_radius, self.se_corner_radius]]  # Calculate the radius for each corner

		## Get the custom style options from the config window and add them to the end of the table formatting
		for i in self.formatting_elems:
			line = (i.style_option.get().upper(), (int(i.x1_entry.get()), int(i.y1_entry.get())), (int(i.x2_entry.get()), int(i.y2_entry.get())), *eval(f'[{i.value_entry.get()}]'))
			self.tablestyle.append(line)

		canvas = Canvas(output_filename, (doc_w, doc_h))  # Create a new PDF

		table = Table(
			data, style=self.tablestyle,
			colWidths=cw, rowHeights=rh,
			cornerRadii=corners
		)  # Create a new table object with the data calculated above

		table.wrapOn(canvas, 0, 0)  # Set the wrap for the canvas
		table.drawOn(canvas, margin[0], doc_h - margin[1] - tableheight)  # Add the table to the canvas at the top left cornet, plus the margins
		canvas.save()  # Save the output PDF

		mb.showinfo('Success', f'Successfully converted {self.root.filename} to PDF.')  # Prompt the user that the conversion was successful

		webbrowser.open('file://' + self.outfile_entry.get())  # Open the PDF

		## todo: add omit weekends, omit rooms, omit teachers to export PDF config.
		## todo: Add events to PDF conversion

		self.destroy()  # Destroy the window

	def validate_corner(self, elem: Entry) -> bool:
		"""
		Evaluates the number or simple equation in a corner radius entry widget and validates the result.
		If match corner radius is enabled, this function updates the value of all corner radius entries.

		:param elem: The entry from which to get the string to validate
		:return: Whether or not the value in the entry is valid.
		"""

		result = self.validate_num(elem)  # Validate the text in the corner entry
		val = elem.get()  # Get the updated text in the corner entry

		if result and self.match_corner_radius.get():  # If the text in the entry is valid and match corner radius is enabled
			## Iterate through each corner radius entry and set the value to the new text in the modified corner entry
			for i in [self.nw_corner_radius, self.ne_corner_radius, self.sw_corner_radius, self.se_corner_radius]:
				i.set(val)

		return result  # Return the validation result

	def add_formatting(self) -> None:
		""" Add a table formatting option """

		## Create a formatting option widget and add it at the bottom of the scrollable frame
		elem = FormattingOption(self, self.scrollable_frame.frame, background='#3B434C')
		elem.pack(side='top', fill='x', padx=1, pady=(1, 0))

		self.formatting_elems.append(elem)  # Add the formatting option widget to the list of formatting options
		self.scrollable_frame.canvas.yview_moveto(10)  # Scroll the scrollable frame canvas by a large amount so the new formatting option is visible

	def remove_formatting(self) -> None:
		""" Removes a table formatting option """

		## Todo: Save PDF formatting config

		if self.selected_format_option is not None:  # If a formatting option is selected
			idx = self.formatting_elems.index(self.selected_format_option)  # Get the index of the formatting option in the list
			self.formatting_elems.pop(idx).destroy()  # Remove the option from the list and destroy the widget
			if len(self.formatting_elems):  # If there are other elements in the formatting option list
				## Select the previous formatting option
				self.selected_format_option = self.formatting_elems[max(0, idx - 1)]
				self.selected_format_option.select()


## todo: loading bar: ⡿⢿⣻⣽⣾⣷⣯⣟


class IndentText(tk.Text):
	"""
	A tkinter text widget that supports numbering, indentation, and dotpoints.
	Features 'syntax highlighting' for dotpoints, auto indent, auto numbering, and auto dotpoints.

	:param parent: (TimeTable) The root timetable widget
	"""

	def __init__(self, parent, *args, **kwargs) -> None:
		self.parent: TimeTable = parent  # Get the parent element
		self.tab_spaces = kwargs.pop('tab_spaces') if 'tab_spaces' in kwargs else 4  # Get the tab size in spaces

		## Get the widget’s font as a `Font` object
		if 'font' in kwargs:
			if isinstance(kwargs['font'], tkfont.Font):
				self.font = kwargs['font']
			else:
				self.font = tkfont.Font(font=kwargs['font'])
		else:
			self.font = tkfont.Font(font=('Consolas', 10))

		kwargs.update({'font': self.font, 'tabs': self.font.measure(' ' * self.tab_spaces)})  # Update the widget’s font and calculate the tab size in pixels based on the width of the tab size in spaces.

		super().__init__(*args, **kwargs)

		self.cdg = ic.ColorDelegator()  # Create a colour delegator for highlighting dotpoints.
		self.cdg.tagdefs = dict()  # Remove the colour delegator’s default tags

		self.cdg.prog = re.compile(INDENT_PATTERN, re.S)  # Compile the calculated pattern and set it as the prog for the colour delegator.
		self.cdg.idprog = re.compile(r'\s+(?P<Words>\w+)', re.S)  # Define the pattern for words in the colour delegator

		## Define the formatting for each dotpoint and numbering format
		self.cdg.tagdefs['DASHPOINT'] = {'foreground': '#F9AE57'}
		self.cdg.tagdefs['DOTPOINT'] = {'foreground': '#B8BBBE'}
		self.cdg.tagdefs['NUMBERING'] = {'foreground': '#60B4B4'}
		self.cdg.tagdefs['LETTERING'] = {'foreground': '#99C794'}

		## Create a percolator for performing syntax highlighting for the dotpoints and numbering
		self.percolator = ip.Percolator(self)
		self.percolator.insertfilter(self.cdg)

		self.bind('<KeyPress>', lambda v: self.keypress_event_manager(v))  # Bind all key-presses to a function

	def custom_update_callback(self) -> None:
		"""
		Called every time a keypress is detected after any edits have been performed.
		Calls external functions in the parent widget and updates the scroll position.
		"""

		self.see(self.index(tk.INSERT))
		self.parent.on_edit()
		self.parent.update_button_states()

	def keypress_event_manager(self, event: tk.Event) -> Optional[Literal['break']]:
		"""
		Provides 'smart functions' for dotpoints, indents and numbering, such as auto indentation and auto numbering.
		Called whenever a key is pressed.

		Notes:
			- Returning 'break' means that the event will be ignored by tkinter’s builtin event manager.
			- This function always calls `custom_update_callback`.
			  This happens after any changes to the widget’s text have been completed.

		:param event: The tkinter event generated by the keypress
		"""

		self.parent.pause_text_event = False  # Re-enable updating the formatting button states in the parent

		cursor_pos = self.index(tk.INSERT)  # Get the index of the cursor
		linenum = cursor_pos.split('.')[0]  # Get the line number part of the cursor index

		## TODO: Key-presses should have a different behaviour when text is selected
		## Todo: add delete to indent text keypress manager
		## todo: Finish commenting keypress manager

		## Match the pressed key
		match event.keysym:
			case 'Return':
				indent = self.get_indent(linenum)  # Get the indent text
				if indent is not None:
					self.insert(cursor_pos, '\n' + increment_numbering(indent))  # Add a new line, plus the indent text from the previous line.
					if event.state == 4:  # If the `ctrl` key was pressed at the same time, set the cursor to the position it was previously.
						self.mark_set(tk.INSERT, cursor_pos)
					self.custom_update_callback()
					return 'break'  # Prevent further updates
			case 'BackSpace':
				match event.state:
					case 1:  # Shift
						## `Shift + Backspace` should delete the previous character, unless the line is blank except for the indent, in which case it should remove the indent.
						line = self.get(f'{linenum}.0', f'{linenum}.end')  # Get the text at the line that the cursor is on
						indent = self.get_indent(line=line)  # Get the indent string for the line
						if indent == line:  # If the only thing on the line is the indent, delete the indent and prevent further updates.
							self.delete(f'{linenum}.0', f'{linenum}.end')
							self.custom_update_callback()
							return 'break'
					case 4:  # Control
						## Ctrl + Backspace should delete the part of the current word that is left of the cursor position, or delete all non-word characters left of the cursor position.
						line = self.get(f'{linenum}.0', cursor_pos)  # Get text on the same line as the cursor from the start of the line to the cursor position

						if cursor_pos != f'{linenum}.0':  # If the cursor is not at the start of the line
							re_match = re.match(r'\w+', line[::-1])  # Find the first match in the line text left of the cursor position.
							## Delete the range of characters directly left of the cursor position and prevent further updates.
							if re_match.start() == 0:
								self.delete(f'{cursor_pos}-{re_match.end()}c', cursor_pos)
							else:
								self.delete(f'{cursor_pos}-{re_match.start()}c', cursor_pos)
							self.custom_update_callback()
							return 'break'

					case 5:  # Control + Shift
						pass

					case _:
						indent = self.get_indent(linenum)  # Get the indent string for the line
						if indent is not None and cursor_pos == f'{linenum}.{len(indent)}':  # If the cursor is at the end of the indent
							location = re.match('[^\t ]+', indent)  # Find starting whitespace of the indent
							if location is None:  # If there is whitespace at the start of the indentation string
								## Decrease the size of the indentation at the start of the indent string by one tab or 4 spaces
								if indent[-1] != '\t':
									self.delete(cursor_pos + f'-{min(self.tab_spaces, len(indent))}c', cursor_pos)
									self.custom_update_callback()
									return 'break'

							else:
								## Otherwise, remove the text part of the indent string and replace it with one tab or 4 spaces
								location = location.span()  # Get the location of the indent
								if indent[location[1]] == '\t' or indent[0] == '\t':  # Check the indent type (tabs or spaces)
									self.replace(f'{linenum}.{location[0]}', f'{linenum}.{len(indent)}', '\t')
								else:
									self.replace(f'{linenum}.{0}', f'{linenum}.{len(indent)}', ' ' * len(indent))

								self.custom_update_callback()
								return 'break'
			case 'Tab':
				sel_range = self.tag_ranges('sel')  # Get the selection range in the text entry
				if sel_range:  # Check if there is selected text
					length_change = dict()  # Declare a dictionary to store the change in the length of the selection’s starting and ending lines. This is used to properly reset the selection
					## Todo: reset numbering and lettering when indent is changed
					lines = set()  # Declare a set to hold the lines in the selection
					for start, end in zip(sel_range[::2], sel_range[1::2]):  # Get the line number of each line in the selection (Note: the tag ranges for the selection are a list of starting and ending index. Every second index is the start of a selection)
						## Get the line number for the starting and ending index of the selection
						start_line = int(str(start).split('.')[0])
						end_line = int(str(end).split('.')[0])

						length_change.update({start_line: None, end_line: None})  # Add the starting and ending line numbers to the length change dictionary as keys

						lines += set(range(start_line, end_line + 1))  # Add the range of line numbers between the start and end index to the list of line numbers

					lines = list(lines)  # Convert the set of lines to a list
					for linenum in lines:  # Iterate through the line numbers in the selection
						line = self.get(f'{linenum}.0', f'{linenum}.end')  # Get the line at the current line number
						indent = self.get_indent(line=line)  # Get the indent at the current line number

						if event.state == 1 and indent is not None:  # If shift is pressed and the line has an indent
							if indent[0] == '\t':  # If the first character of the line indent is a tab, delete the first character.
								self.delete(f'{linenum}.0', f'{linenum}.1')
							elif indent[0] == ' ':  # If the first character of the line indent is a space, delete up to 4 spaces from the start of the line
								self.delete(f'{linenum}.0', f'{linenum}.{min(self.tab_spaces, re.match(r' +', indent).end())}')
							else:  # Otherwise, delete the indent.
								self.delete(f'{linenum}.0', f'{linenum}.{len(indent)}')

							self.custom_update_callback()
							return 'break'  # Prevent further updates to the widget text

						else:  # Shift is not pressed
							if indent is None or indent[0] == '\t':  # If the line does not have an indent, or the first character in the indent is a tab.
								new_line = '\t'  # Set the characters to add to a tab character
							else:
								new_line = ' ' * self.tab_spaces  # Otherwise, set the characters to add to 4 spaces

							if indent is not None and ('•' in indent or 'o' in indent or '' in indent):  # If the indent character is a 'cycling dotpoint' (i.e.: each indent level has a different dotpoint character)
								new_line += indent  # Add the current indent to the new line
								self.delete(f'{linenum}.0', f'{linenum}.{len(indent)}')  # Remove the old indent string from the line
								new_line = new_line.replace('•', 'o').replace('o', '').replace('', '•')  # Cycle the dot point character

							self.insert(f'{linenum}.0', new_line)  # Add the new characters to the output line

						## If the current line contains the start or end of a selection range, store the change in length for the line.
						if linenum in length_change:
							length_change.update({linenum: len(self.get(f'{linenum}.0', f'{linenum}.end')) - len(line)})  # Update the change in length of the line

					## Update the selections in the text widget
					new_sel_range = []  # Declare a list to hold the new selection range
					for i in sel_range:  # Iterate through the previous selection ranges
						ln = int(str(i).split('.')[0])  # Get the line number of the previous selection
						new_sel_range.append(f'{i}{length_change[ln]:+n}c')  # Add the change in line length to the selection range and add it to the list of new selection ranges

					self.tag_remove('sel', 1.0, tk.END)  # Remove the existing selection from the text element
					self.tag_add('sel', *new_sel_range)  # Add back the selections

					self.custom_update_callback()
					return 'break'  # Prevent further updates to the text entry widget

				else:  # If there is no selection
					indent = self.get_indent(linenum)  # Get the indent string of the line the cursor is on

					if event.state == 1 and indent is not None:  # If shift is pressed and the line has an indent
						if indent[0] == '\t':  # If the first character of the line is a tab, delete the first character
							self.delete(f'{linenum}.0', f'{linenum}.1')
						elif indent[0] == ' ':  # If the first character of the line is a space, delete up to 4 spaces
							self.delete(f'{linenum}.0', f'{linenum}.{min(self.tab_spaces, re.match(r' *', indent).end())}')
						else:  # Otherwise, delete the entire indent
							self.delete(f'{linenum}.0', f'{linenum}.{len(indent)}')

						self.custom_update_callback()
						return 'break'  # Prevent further updates to the text element for this event

		self.custom_update_callback()

	def get_indent(self, linenum: Optional[int | str] = None, line: Optional[str] = None) -> Optional[str]:
		"""
		Get the part of the input line that matches the supported indent, dotpoint and numbering formats

		:param linenum: The line number of the text element to check for an indent
		:param line: The string to check for an indent
		:returns: The indent portion of the line, if any.
		"""

		## Get the line text if only the line number is supplied
		if line is None:
			line = self.get(f'{linenum}.0', f'{linenum}.end')

		## Match the indentation pattern
		re_match = re.match(r'[ \t]*(?P<dotpoints_and_numbering>(?P<CAP_Lettering>[A-Z]{1,2}[):])|(?P<LOW_Lettering>[a-z]{1,2}[):])|(?P<Numbering>[0-9]{1,2}[.):])|[>•o-])?[ \t]+', line)

		## If there is a match, return the matching portion of the line.
		if re_match is not None and re_match.start() == 0:
			return line[slice(*re_match.span())]


class WeekFrame(tk.Frame):
	"""
	A frame that displays a week number and the events and event types on said week

	:param parent: (TimeTable) The root timetable widget
	:param week: The week number for the widget
	"""

	def __init__(self, parent, week: int, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.week = week
		self.parent: TimeTable = parent

		self.indicator_elems: list[Optional[tk.Label]] = [None] * len(self.parent.event_types)  # Define an array to hold the session event indicators for the week

		self.event_data = {(v.day, v.session): v.type() for v in filter(lambda v: v.week == week, parent.events)}  # Create a dictionary of all events in the week, indexed by the day and session number

		types = list(self.event_data.values())  # Create a list of all the event types that occur in the week
		event_type_counts = [(n, i, types.count(i)) for n, i in enumerate(self.parent.event_types)]  # Create an array containing the index, name, and count for the week, of all possible event types

		self.event_num_texts = [tk.StringVar(self, str(i[2])) for i in event_type_counts]  # Create a string variable to display the count of each event type

		## Create an event class to bind all the widget’s children to.
		self.bind_class(f'click:wk{self.week}', '<Button-1>', lambda v: self.set_week())
		self.bindtags((f'click:wk{self.week}', *self.bindtags()))

		## Adjust the grid geometry
		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, weight=1, minsize=8)

		## ======================================== User Interface ========================================

		## ------------------------------------------ Week number -----------------------------------------
		self.numlabel = tk.Label(self, text=f'Week {week + 1}{" (Current)" if week == self.parent.week else ""}', background='#303841', foreground='#D8DEE9', height=15, image=self.parent.master.pixel, compound='center', font=('Arial', 11, 'bold' if week == self.parent.week else ''), anchor='nw')
		self.numlabel.bindtags((f'click:wk{self.week}', *self.numlabel.bindtags()))
		self.numlabel.grid(row=0, column=0, sticky='nswe')

		## ----------------------------------- Event type display frame -----------------------------------
		self.indicator_frame = tk.Frame(self, background='#303841', height=8)
		self.indicator_frame.bindtags((f'click:wk{self.week}', *self.indicator_frame.bindtags()))
		self.indicator_frame.grid(row=1, column=0, sticky='nswe')

		## Add a blank image for formatting purposes
		self.formatting_image = tk.Label(self.indicator_frame, image=parent.master.pixel, compound='center', width=8, height=8, background='#303841')
		self.formatting_image.bindtags((f'click:wk{self.week}', *self.formatting_image.bindtags()))
		self.formatting_image.grid(row=0, column=len(self.parent.event_types), padx=(0, 1), pady=(1, 0), sticky='NW')

		## --------------------------------------- Event indicators ---------------------------------------
		## Iterate through the calculated event counts for the week that are above one, and add a corresponding indicator to the indicator frame
		for idx, e_type, count in filter(lambda v: v[2] > 0, event_type_counts):
			indicator = tk.Label(self.indicator_frame, textvariable=self.event_num_texts[idx], image=parent.master.icons[e_type], compound='left', width=15, height=8, background='#303841', foreground='#D8DEE9', font=('Calibri', 12))
			indicator.grid(row=0, column=idx, padx=(0, 1), pady=(1, 0), sticky='W')
			indicator.bindtags((f'click:wk{self.week}', *indicator.bindtags()))

			self.indicator_elems[idx] = indicator

	def set_week(self) -> None:
		"""
		Update the parent element’s current week number to this widget’s week number.
		Called whenever the widget is clicked.
		"""

		self.parent.week_slider.set(self.week)

	def edit_event_type(self, event) -> None:
		"""
		Update the count for the previous and new event types whenever an event’s type is changed.

		:param event: The updated event to process
		"""

		if self.event_data[(event.day, event.session)] != event.type():  # If the stored event type and actual event type do not match
			self.remove_event(event, event_type=self.event_data[(event.day, event.session)])  # Decrement the counter for the stored event type for the event’s session and day number
			self.add_event(event)  # Add the event to the widget’s stored events and increment the appropriate event type counter

	def add_event(self, event) -> None:
		"""
		Increment the counter for the event type of the input event and add the event to the event dictionary

		:param event: The event object to add
		"""

		idx = self.parent.event_types.index(event.event_type.get())  # Get the index of the event’s type

		text = self.event_num_texts[idx]  # Get the event type counter to update
		val = int(text.get())  # Get the current stored event count

		if val == 0:  # If no events of the input type are currently stored
			## Add a new counter to the indicator display
			indicator = tk.Label(self.indicator_frame, textvariable=text, image=self.parent.master.icons[event.type()], compound='left', width=15, height=8, background='#303841', foreground='#D8DEE9', font=('Calibri', 12))
			indicator.grid(row=0, column=idx, padx=(0, 1), pady=(1, 0), sticky='W')
			self.indicator_elems[idx] = indicator
			indicator.bindtags((f'click:wk{self.week}', *indicator.bindtags()))

		text.set(str(val + 1))  # Increment the counter
		self.event_data.update({(event.day, event.session): event.type()})  # Add the event type at the session and day number to the event dictionary

	def remove_event(self, event, event_type: Optional[str] = None) -> None:
		"""
		Decrement the counter for the input event’s type and remove the stored event type from the event type dictionary.

		:param event: (Event) The event object to add
		:param event_type: The key of the event counter to decrement
		"""

		## Get the event type from the input event if necessary
		if event_type is None:
			event_type = event.type()

		idx = self.parent.event_types.index(event_type)  # Get the index of the input event type

		text = self.event_num_texts[idx]  # Get the event type counter to update
		val = int(text.get())  # Get the current stored event count

		if val == 1:  # If only one event of the input type is stored
			## Remove the indicator corresponding to the event type
			self.indicator_elems[idx].destroy()
			self.indicator_elems[idx] = None

		text.set(str(val - 1))  # Decrement the counter for the type
		self.event_data.pop((event.day, event.session))  # Remove the event from the event data dictionary


class Event:
	"""
	Stores timetable event data for a single day.

	:param week: The week number of the event.
	:param day: The day number of the event (Monday = 0, Sunday = 6).
	:param session: The session number of the event.
	:param text: The event text to store.
	:param tags: The tags for the event (currently does nothing).
	:param event_type: The type string of the event.
	"""

	def __init__(self, week: int, day: int, session: int, text: str, tags: Optional[list], event_type: str) -> None:
		## Get the week, day, and session number for the event
		self.week = week
		self.day = day
		self.session = session

		## Get the formatting for the event
		self.text = text
		self.tags = tags
		self.event_type = tk.StringVar(value=event_type)
		self.type = self.event_type.get

	@dispatch(tuple)
	def __eq__(self, other) -> bool:
		"""
		Check if the event’s timeslot matches the input timeslot

		:param other: The timeslot to compare to in (week, day, session) format
		"""

		return other == (self.week, self.day, self.session)

	@dispatch(object)
	def __eq__(self, other) -> bool:
		"""
		Check if the event’s timeslot matches the input timeslot

		:param other: The timeslot to compare to in (week, day, session) format
		"""

		return tuple(other) == (self.week, self.day, self.session)

	def __iter__(self) -> Generator[int, int, int]:
		""" Yield the event timeslot as an iterable """
		yield self.week
		yield self.day
		yield self.session

	def get_data(self) -> dict:
		"""
		Get the event’s data in dictionary form to be written to a timetable JSON file
		"""

		data = {
			'week': self.week,
			'day': self.day,
			'session': self.session,
			'data': enclose(multireplace(self.text, {'"': '\\"', '\n': '\\n', '\t': '\\t'}), '"'),
			'tags': list(map(lambda v: v.replace('"', '\\"'), self.tags)) if self.tags is not None else None,
			'type': enclose(self.type(), '"')
		}
		return data

	def __gt__(self, other) -> bool:
		""" Check if the event occurs after the input event """
		return self.day > other.day or (self.day == other.day and self.session > other.session)

	def __lt__(self, other) -> bool:
		""" Check if the event occurs before the input event """
		return self.day < other.day or (self.day == other.day and self.session < other.session)

	def __ge__(self, other) -> bool:
		""" Check if the event occurs at the same time or later than the input event """
		return self.day > other.day or (self.day == other.day and self.session >= other.session)

	def __le__(self, other) -> bool:
		""" Check if the event occurs at the same time or earlier than the input event """
		return self.day < other.day or (self.day == other.day and self.session <= other.session)


class TimetableCell:
	"""
	A base class representing a cell in a timetable.

	:param root: (TimeTable) The root timetable widget.
	:param master: The parent element.
	:param day: The day index of the cell.
	:param session: The session index of the cell.
	:param class_data_idx: The index of the cell’s class data.
	:param weekend: Whether or not the cell is on a weekend day.
	"""

	def __init__(self, root, master, day: int, session: int, class_data_idx: Optional[int], weekend: bool = False) -> None:
		self.root: TimeTable = root  # The root timetable object
		self.master = master  # The parent element

		self.day = day
		self.session = session
		self.class_data_idx = class_data_idx
		self.weekend = weekend

		self.state = 'normal'
		self.current_event: Optional[Event] = None
		self.events_indicator: Optional[tk.Label] = None

		## Create a frame to hold the elements of the cell
		self.frame = tk.Frame(master, background='#3B434C')
		self.frame.columnconfigure(0, weight=1)
		self.frame.rowconfigure(0, weight=1)

		## Bind mouseover to highlight the cell
		self.frame.bind('<Enter>', lambda v: self.enter())
		self.frame.bind('<Leave>', lambda v: self.leave())

		## Create an event class and bind clicking to toggle selection.
		self.frame.bind_class(f'click:{id(self)}', '<Button-1>', lambda v: self.toggle_selected())

	def add_event_indicator(self) -> None:
		"""
		Adds an event type indicator to the cell
		"""

		self.events_indicator = tk.Label(self.frame, image=self.root.master.pixel, compound='center', width=8, height=8, background='#303841')
		self.events_indicator.grid(row=0, column=0, padx=(0, 1), pady=(1, 0), sticky='NE')

	def set_event(self, event) -> None:
		"""
		Sets the event currently displayed by the cell and updates the event indicator accordingly

		:param event: The event to set
		"""

		self.current_event = event  # Set the current event variable to the input event

		## Update the event indicator with the appropriate image
		if event is None:
			self.events_indicator.configure(image=self.root.master.pixel)
		else:
			self.events_indicator.configure(image=self.root.master.icons[event.type()])

	def update_event(self) -> None:
		"""
		Update the event currently stored and displayed by the cell
		"""

		events = list(filter(lambda v: v == (self.root.week, self.day, self.session), self.root.events))  # Get a list of events that occur on the same timeslot as the cell and on the current week.

		if not events:  # If no events occur on the same timeslot as the cell, update the event indicator and current event
			self.events_indicator.configure(image=self.root.master.pixel)
			self.current_event = None

		elif events:  # Otherwise, set the current event to the first event in the list and set the event indicator’s image to the event type
			self.current_event = events[0]
			self.events_indicator.configure(image=self.root.master.icons[self.current_event.type()])

		if self.state == 'active':  # If the cell is active, update the root’s active event
			self.root.update_active_event()

	def grid(self) -> None:
		""" Add the cell to the position on the grid corresponding to the cell’s timeslot """
		self.frame.grid(column=self.day + 1, row=self.session + sum(map(lambda v: self.session > v, self.root.session_break_idxs[1])) + 1, sticky='nswe', padx=(int(self.day == 0), 1), pady=(int(self.session == 0), 1), rows=len(self.root.sessions) if self.weekend else 1)

	def enter(self) -> None:
		""" Highlight the cell colours and update the state """
		if self.state == 'normal':
			self.state = 'highlighted'
			self.update_elems()

	def leave(self) -> None:
		""" Un-highlight the cell colours and update the state """
		if self.state == 'highlighted':
			self.state = 'normal'
			self.update_elems()

	def toggle_selected(self) -> None:
		"""
		Toggle the cell’s selection status
		"""

		if self.state == 'active':  # If the cell is already selected, deselect it
			self.state = 'highlighted'
			self.root.active_cell = None
		else:
			## Otherwise, deselect the currently selected cell
			if self.root.active_cell is not None:
				self.root.active_cell.state = 'normal'
				self.root.active_cell.update_elems()

			## Set the cell as the currently selected cell
			self.root.active_cell = self
			self.state = 'active'

		self.update_elems()  # Update the cell’s formatting
		self.root.update_active_event()  # Update the root’s active cell data

	def update_elems(self) -> None:
		""" Updates the colours of the cell and its children to match the current state """
		formatting = self.root.cell_state_config[self.state]  # Get the formatting config for the current state

		self.frame.configure(background=formatting[1])  # Set the cell’s border colour
		for elem in self.frame.winfo_children():  # Set the cell’s children’s background colour
			elem.configure(**formatting[0])


class WeekendCell(TimetableCell):
	"""
	A class representing the 'body' cells displayed under the saturday and sunday headings

	:param root: (TimeTable) The root timetable widget
	:param master: The parent element
	:param weekend_day: The index of the day of the weekend to represent (i.e.: 0 for saturday or 1 for sunday)
	"""

	def __init__(self, root, master, weekend_day: int) -> None:
		self.name = ['Saturday', 'Sunday'][weekend_day]  # Get the text to display

		super().__init__(root, master, weekend_day + 5, 0, None, True)

		## Create a label to display the contents of the cell
		self.name_display = tk.Label(self.frame, text='Homework', relief='flat', wraplength=75, font=('Calibri', 12, 'bold'), background='#303841', foreground='#D8DEE9', anchor='n')
		self.name_display.grid(row=0, column=0, padx=1, pady=1, sticky='NSWE')
		self.name_display.bindtags((f'click:{id(self)}', *self.name_display.bindtags()))

		self.add_event_indicator()  # Add an event indicator


class SessionCell(TimetableCell):
	"""
	A class representing a single timeslot for a weekday in a timetable.

	:param root: (TimeTable) The root timetable widget.
	:param master: The parent element.
	:param day: The day index of the cell.
	:param session: The session index of the cell.
	:param class_data_idx: The index of the cell’s class data.
	"""

	def __init__(self, root, master, day: int, session: int, class_data_idx: int) -> None:
		## Get the text variables corresponding to the class in the timeslot
		self.name = root.classes[class_data_idx]
		self.room = root.rooms[class_data_idx]
		self.teacher = root.teachers[class_data_idx]

		super().__init__(root, master, day, session, class_data_idx)

		## Create a label to display the name of the class
		self.name_display = tk.Label(self.frame, textvariable=self.name, relief='flat', wraplength=100, font=('Calibri', 12, 'bold'), background='#303841', foreground='#D8DEE9')
		self.name_display.grid(row=0, column=0, padx=1, pady=1, sticky='NSWE')
		self.name_display.bindtags((f'click:{id(self)}', *self.name_display.bindtags()))

		## Create a label to display the name of the classroom
		self.room_display = tk.Label(self.frame, textvariable=self.room, relief='flat', font=('Calibri', 12), background='#303841', foreground='#D8DEE9')
		self.room_display.grid(row=1, column=0, padx=1, pady=(0, 1), sticky='NSWE')
		self.room_display.bindtags((f'click:{id(self)}', *self.room_display.bindtags()))

		## Create a label to display the name of the teacher
		self.teacher_display = tk.Label(self.frame, textvariable=self.teacher, relief='flat', font=('Calibri', 12), background='#303841', foreground='#D8DEE9')
		self.teacher_display.grid(row=2, column=0, padx=1, pady=(0, 1), sticky='NSWE')
		self.teacher_display.bindtags((f'click:{id(self)}', *self.teacher_display.bindtags()))

		self.add_event_indicator()  # Add an event indicator

	def update_sessiondata(self) -> None:
		""" Update the display labels to either display the current event or display empty and update the class data appropriately. """

		if self.class_data_idx is None:  # If no class data is assigned to the cell
			## Reset the class data variables
			self.name = None
			self.room = None
			self.teacher = None

			## Configure the display labels to be blank
			self.name_display.configure(textvariable=self.root.null_text_variable)
			self.teacher_display.configure(textvariable=self.root.null_text_variable)
			self.room_display.configure(textvariable=self.root.null_text_variable)
		else:
			## Set the class data variables to the values of the class
			self.name = self.root.classes[self.class_data_idx]
			self.room = self.root.rooms[self.class_data_idx]
			self.teacher = self.root.teachers[self.class_data_idx]

			## Update the class data variables to display the class data
			self.name_display.configure(textvariable=self.name)
			self.teacher_display.configure(textvariable=self.teacher)
			self.room_display.configure(textvariable=self.room)


class TimeTable:
	"""
	Manages a single timetable and its supporting UI elements

	:param master: (Window) The root window widget
	:param classes: The names of each class in the timetable
	:param teachers: The corresponding teacher name for each class in the timetable
	:param rooms: The corresponding room name for each class in the timetable
	:param class_mapping: The mapped class for each timeslot in the timetable
	:param event_data: A dictionary containing data for each event saved in the timetable
	:param day_start_time: The time at which the first timeslot on the timetable column starts
	:param sessions: The mapping for the names, types, and times for each class in the timetable in the format [name, type (is not break), end time]
	:param start_date: The start timestamp from which to calculate the current week
	"""

	def __init__(self, master, classes: list[str], teachers: list[str], rooms: list[str], class_mapping: list[list[int]], event_data: list[dict], day_start_time: str, sessions: list[tuple[str, bool, str]], start_date: int) -> None:
		self.master: Window = master

		# self.classname_str = classes  # Store the names of each class as strings  # Todo: depreciated, can be removed
		self.class_mapping = class_mapping
		self.start_timestamp = start_date
		self.day_start_time = day_start_time

		self.events = list(map(lambda v: Event(*list(v.values())), event_data))  # Create an event object for each event in the event data dictionary and add them to a list

		## Create a container to hold the entire timetable
		self.display_frame = tk.Frame(master, background='#222')
		self.display_frame.columnconfigure(1, weight=1)
		self.display_frame.columnconfigure(2, minsize=352)
		self.display_frame.rowconfigure(0, weight=1)
		self.grid = self.display_frame.grid

		## Convert the class data to tkinter stringvariables
		self.classes = list(map(lambda v: tk.StringVar(self.display_frame, v), classes))
		self.teachers = list(map(lambda v: tk.StringVar(self.display_frame, v), teachers))
		self.rooms = list(map(lambda v: tk.StringVar(self.display_frame, v), rooms))

		## Add traces to each stringvariable so the UI can be updated when changes are made
		for n, i in enumerate(zip(self.classes, self.teachers, self.rooms)):
			i[0].trace('w', lambda a, b, c, idx=n: self.edit_class_names(idx))
			i[1].trace('w', lambda a, b, c: self.check_saved(self.get_json()))
			i[2].trace('w', lambda a, b, c: self.check_saved(self.get_json()))

		self.active_cell: Optional[WeekendCell | SessionCell] = None
		self.day = 0
		self.pause_text_event = False
		self.event_types = ['Event', 'Info', 'Reminder', 'Bookmark', 'Assignment', 'Test']
		self.current_savefile_contents: Optional[str] = None
		self.events_saved = True
		self.formatting_update_after: Optional[str] = None

		## Create empty and null text string variables to use as placeholders (e.g.: when an event is added or deleted)
		self.empty_text_variable = tk.StringVar(self.display_frame, '')
		self.null_text_variable = tk.StringVar(self.display_frame, '<Null>')

		## Define default and state based formatting for UI elements
		self.cell_state_config = {
			'normal': ({'background': '#303841', 'foreground': '#D8DEE9'}, '#3B434C'),
			'active': ({'background': '#4F565E', 'foreground': '#D4D6D7'}, '#62686F'),
			'highlighted': ({'background': '#343C44', 'foreground': '#D4D6D7'}, '#3B434C')
		}

		self.active_header_config = {'background': '#8C3841', 'foreground': '#D4D6D7', 'font': ('Calibri', 13, 'bold'), 'highlightbackground': '#963D49'}
		self.inactive_header_config = {'background': '#424D59', 'foreground': '#D4D6D7', 'font': ('Calibri', 13), 'highlightbackground': '#4F565E'}

		self.week = self.get_week(datetime.datetime.now().timestamp())  # Calculate the current week number
		self.sessions, self.sessiontimes = self.get_sessiontimes(sessions)  # Calculate the time index for each session and get the session data to display

		self.timeslot_idx = self.get_session(datetime.datetime.now())  # Declare a variable containing the session to calculate time (will never be NULL)
		if self.timeslot_idx is None:
			self.timeslot_idx = 11

		self.timeslot_idx -= 1

		## ======================================== User Interface ========================================

		## ----------------------------------------- Week Display -----------------------------------------
		frame = tk.Frame(self.display_frame, background='#222')
		frame.grid(row=0, column=0, sticky='NSWE', padx=(1, 2))
		frame.columnconfigure(0, weight=1)
		frame.rowconfigure(1, weight=1)

		tk.Label(frame, background='#303841', borderwidth=0, relief='flat', foreground='#D8DEE9', font=('Calibri', 12, 'bold'), text='Week', highlightthickness=1, highlightbackground='#3B434C').grid(row=0, columnspan=2, column=0, sticky='nswe', pady=(1, 0))

		self.week_slider = tk.Scale(frame, orient='vertical', resolution=1, command=self.update_week, from_=0, to=11, borderwidth=0, relief='flat', border=0, showvalue=False, sliderlength=50, sliderrelief='flat', width=10, troughcolor='#444B53', highlightthickness=0, background='#696F75', activebackground='#858C93')
		self.week_slider.grid(row=1, column=0, sticky='ns', padx=(0, 1), pady=(1, 1), rowspan=12)
		self.week_slider.set(self.week)  # Set the week slider to the current week number

		self.weekframe = tk.Frame(frame, background='#222')
		self.weekframe.grid(row=1, column=1, sticky='NSWE', pady=(0, 0))
		self.weekframe.rowconfigure(list(range(12)), weight=1)
		self.weekframe.columnconfigure(1, weight=1, minsize=133)
		self.week_elems = []

		for i in range(12):
			frame = WeekFrame(self, i, self.weekframe, background='#303841', highlightbackground='#3B434C', highlightthickness=1)
			frame.grid(row=i, column=1, sticky='nswe', padx=(0, 0), pady=(int(i == 0), 1))
			self.week_elems.append(frame)

		## ------------------------------------------ Edit Sidebar ----------------------------------------

		self.sidebar = tk.Frame(self.display_frame, background='#222', width=352)
		self.sidebar.grid(column=2, row=0, sticky='NSWE')
		self.sidebar.rowconfigure(11, weight=1)
		self.sidebar.columnconfigure(0, weight=1)

		## ----------------------------------------- Event Edit UI ----------------------------------------

		tk.Label(self.sidebar, text='Events', background='#303841', foreground='#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Calibri', 14), image=master.pixel, compound='center', height=19).grid(row=0, column=0, sticky='NSWE', padx=1, pady=(1, 0))

		entryborder = tk.Frame(self.sidebar, background='#4F565E')
		entryborder.grid(row=1, column=0, sticky='NSWE', pady=(1, 0), padx=1)
		entryborder.columnconfigure(0, weight=1)
		entryborder.rowconfigure(1, weight=1)

		self.formatting_frame = tk.Frame(entryborder, background='#4F565E')
		self.formatting_frame.grid(row=0, column=0, sticky='NSWE', padx=1, pady=(1, 0))

		self.numbering_format = tk.IntVar(self.display_frame, 0)

		self.entry_font = tkfont.Font(family=self.master.settings['editor.font'][0], size=self.master.settings['editor.font'][1], weight='bold' if 'bold' in self.master.settings['editor.font'][2] else 'normal', slant='italic' if 'italic' in self.master.settings['editor.font'][2] else 'roman')

		## Todo: complete dotpoint formatting bar
		CustomRadiobutton(self.formatting_frame, font=('Segoe UI', 9, 'bold'), image=self.master.pixel, padx=5, pady=5, indicatoron=False, relief='flat', borderwidth=0, foreground='#aaa', background='#272E35', activebackground='#3E4244', width=20, height=9, compound='center', selectcolor='#323B44', selectforeground='#6FB0DB', text='None', value=0, variable=self.numbering_format, command=lambda: self.update_list_format()).grid(row=0, column=0, padx=(0, 1), pady=0, sticky='nswe')
		CustomRadiobutton(self.formatting_frame, image=self.master.icons['dotpoints'], padx=5, pady=5, indicatoron=False, relief='flat', borderwidth=0, foreground='#aaa', background='#272E35', activebackground='#3E4244', width=20, height=9, compound='center', selectcolor='#323B44', selectforeground='#09f', value=1, variable=self.numbering_format, command=lambda: self.update_list_format()).grid(row=0, column=1, padx=(0, 1), pady=0, sticky='nswe')
		CustomRadiobutton(self.formatting_frame, image=self.master.icons['numbering'], padx=5, pady=5, indicatoron=False, relief='flat', borderwidth=0, foreground='#aaa', background='#272E35', activebackground='#3E4244', width=20, height=9, compound='center', selectcolor='#323B44', selectforeground='#09f', value=2, variable=self.numbering_format, command=lambda: self.update_list_format()).grid(row=0, column=2, padx=(0, 1), pady=0, sticky='nswe')
		CustomRadiobutton(self.formatting_frame, image=self.master.icons['lettering'], padx=5, pady=5, indicatoron=False, relief='flat', borderwidth=0, foreground='#aaa', background='#272E35', activebackground='#3E4244', width=20, height=9, compound='center', selectcolor='#323B44', selectforeground='#09f', value=3, variable=self.numbering_format, command=lambda: self.update_list_format()).grid(row=0, column=3, padx=(0, 1), pady=0, sticky='nswe')

		self.event_entry = IndentText(self, entryborder, background='#303841', undo=True, foreground='#D8DEE9', highlightthickness=0, highlightbackground='#4F565E', insertbackground='#F9AE58', borderwidth=0, font=self.entry_font, width=1, height=7, tab_spaces=8)
		self.event_entry.grid(row=1, column=0, sticky='NSWE', padx=1, pady=(1, 1))

		self.event_scrollbar = AutoScrollbar(entryborder, orient='vertical', command=self.event_entry.yview, style='Custom.Vertical.TScrollbar')
		self.event_scrollbar.grid(row=1, column=1, sticky='NS', padx=(0, 1), pady=(1, 1))

		self.event_entry.configure(yscrollcommand=self.event_scrollbar.set)

		self.event_entry._orig = str(self.event_entry) + '_orig'
		self.event_entry.tk.createcommand(str(self.event_entry), self._proxy)

		self.event_entry.bind('<<Edit>>', lambda v: self.update_button_states())
		self.event_entry.bind('<<Change>>', lambda v: self.on_edit())

		self.event_info_label = tk.Label(self.sidebar, text='No Selection', background='#303841', foreground='#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Calibri', 12))
		self.event_info_label.grid(row=1, column=0, sticky='NSWE', padx=1, pady=(1, 0))
		self.event_info_label.bind('<Button-1>', lambda v: self.create_event())

		self.buttonframe = tk.Frame(self.sidebar, background='#4F565E')
		self.buttonframe.grid(row=2, column=0, sticky='NSWE', padx=1, pady=(0, 0))
		self.buttonframe.columnconfigure(4, weight=1)

		self.saveas_button = ttk.Button(self.buttonframe, text='Save As', style='text.stipple.TButton', command=lambda: self.save_as(), width=10, state='disabled')
		self.saveas_button.grid(row=0, column=0, padx=(1, 1), pady=(0, 1), sticky='nswe')

		self.save_button = ttk.Button(self.buttonframe, text='', style='symbol.stipple.TButton', command=lambda: self.save_timetable(), width=1, state='disabled')
		self.save_button.grid(row=0, column=1, padx=(0, 1), pady=(0, 1), sticky='nswe')

		tk.Frame(self.buttonframe, background='#222', width=10).grid(row=0, column=2, sticky='nswe')

		self.delete_button = ttk.Button(self.buttonframe, text='', style='symbol.stipple.TButton', state='disabled', command=lambda: self.delete_event(False), width=1)
		self.delete_button.grid(row=0, column=3, padx=(1, 1), pady=(0, 1), sticky='nswe')

		tk.Frame(self.buttonframe, background='#222').grid(row=0, column=4, sticky='nswe')

		tk.Label(self.buttonframe, background='#424D59', foreground='#D8DEE9', font=('Calibri', 12), text='Type', width=5).grid(row=0, column=5, padx=(1, 1), pady=(0, 1), sticky='nswe')

		self.event_type_combobox = ttk.Combobox(self.buttonframe, style='Custom.TCombobox', background='#303841', foreground='#D8DEE9', values=self.event_types, state='disabled')
		self.event_type_combobox.grid(row=0, column=6, sticky='nswe', padx=(0, 1), pady=(0, 1))
		self.event_type_combobox.bind('<<ComboboxSelected>>', lambda v: self.edit_event_type())
		self.tt_elements: list[list[SessionCell | WeekendCell]] = []

		## ----------------------------------------- Class Edit UI ----------------------------------------

		tk.Frame(self.sidebar, background='#4F565E', height=1).grid(row=3, column=0, sticky='we', padx=5, pady=10)

		tk.Label(self.sidebar, text='Class', background='#303841', foreground='#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Calibri', 13), image=master.pixel, compound='center', height=19).grid(row=5, column=0, sticky='NSWE', padx=1, pady=(0, 2))

		self.class_edit_frame = tk.Frame(self.sidebar, background='#222')
		self.class_edit_frame.grid(row=6, column=0, sticky='NSWE')
		self.class_edit_frame.columnconfigure(1, weight=1)

		buttonframe = tk.Frame(self.class_edit_frame, background='#4F565E')
		buttonframe.grid(row=0, column=0, sticky='nswe', padx=(1, 1), pady=(0, 1))
		buttonframe.rowconfigure(3, weight=1)

		tk.Label(buttonframe, background='#424D59', foreground='#D8DEE9', font=('Calibri', 12), text='Session', width=7).grid(row=0, column=0, padx=(1, 1), pady=(1, 1), sticky='nswe')

		self.class_name_combobox = ttk.Combobox(buttonframe, style='Custom.TCombobox', background='#303841', foreground='#D8DEE9', values=classes, state='disabled')
		self.class_name_combobox.grid(row=0, column=1, sticky='nswe', padx=(0, 1), pady=(1, 1), columnspan=2)
		self.class_name_combobox.bind('<<ComboboxSelected>>', lambda v: self.edit_class())

		tk.Frame(buttonframe, background='#222', height=1).grid(row=1, column=0, columns=3, sticky='nswe')

		self.new_class_button = ttk.Button(buttonframe, text='New', style='text.stipple.TButton', state='normal', command=lambda: self.new_class(), width=1, image=self.master.pixel, compound='center')
		self.new_class_button.grid(row=2, column=0, padx=(1, 1), pady=(1, 1), sticky='nswe', columnspan=2)

		self.delete_class_button = ttk.Button(buttonframe, text='Delete', style='text.stipple.TButton', state='disabled', command=lambda: self.delete_class(), width=1, image=self.master.pixel, compound='center')
		self.delete_class_button.grid(row=2, column=2, padx=(0, 1), pady=(1, 1), sticky='nswe')

		tk.Frame(buttonframe, background='#222').grid(row=3, column=0, columns=3, sticky='nswe')

		entryframe = tk.Frame(self.class_edit_frame, background='#4F565E')
		entryframe.grid(row=0, column=1, sticky='nswe', padx=(2, 1), pady=(0, 1))
		entryframe.columnconfigure(1, weight=1)

		tk.Label(entryframe, background='#424D59', foreground='#D8DEE9', font=('Calibri', 12), text='Name', width=5).grid(row=0, column=0, padx=(1, 0), pady=(1, 0), sticky='nswe')

		self.name_entry = ttk.Entry(entryframe, style='stipple.TEntry')
		self.name_entry.grid(row=0, column=1, sticky='nswe', padx=1, pady=(1, 0))

		tk.Label(entryframe, background='#424D59', foreground='#D8DEE9', font=('Calibri', 12), text='Room', width=5).grid(row=1, column=0, padx=(1, 0), pady=(1, 0), sticky='nswe')

		self.room_entry = ttk.Entry(entryframe, style='stipple.TEntry')
		self.room_entry.grid(row=1, column=1, sticky='nswe', padx=1, pady=(1, 0))

		tk.Label(entryframe, background='#424D59', foreground='#D8DEE9', font=('Calibri', 12), text='Teacher', width=7).grid(row=2, column=0, padx=(1, 0), pady=(1, 1), sticky='nswe')

		self.teacher_entry = ttk.Entry(entryframe, style='stipple.TEntry')
		self.teacher_entry.grid(row=2, column=1, sticky='nswe', padx=1, pady=(1, 1))

		## ----------------------------------------- Table Display ----------------------------------------

		self.table_frame = tk.Frame(self.display_frame, background='#222')
		self.table_frame.grid(column=1, row=0, sticky='NSWE')
		self.table_frame.columnconfigure(list(range(1, 8)), weight=1)
		self.table_frame.rowconfigure(list(range(1, len(self.sessions))), weight=1)

		## ---------------------------------------- Table Generation --------------------------------------

		self.dotw_headers: list[tk.Label] = []  # Define a list to store the 'day of the week' headers
		self.active_dotw_header: Optional[int] = None  # Define a variable to store the active 'day of the week' header

		## Add a header for each day of the week
		for n, dotw in enumerate(['Mon', 'Tue', 'Wed', 'Thr', 'Fri', 'Sat', 'Sun']):
			## Add a header label
			header = tk.Label(self.table_frame, text=dotw, background='#424D59', foreground='#D4D6D7', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Calibri', 13), image=master.pixel, compound='center', height=19)
			header.grid(row=0, column=n + 1, sticky='NSWE', padx=(int(n == 0), 1), pady=(1, 0))
			self.dotw_headers.append(header)  # Add the header to the list

		self.session_headers: list[tk.Label] = []  # Define a list to store the session headers
		self.active_session_header: Optional[int] = None  # Define a variable to store the active session header

		self.session_break_idxs = [[], []]  # Define a list to store the index of session breaks and the total row offset from session breaks

		## Add a header for each period in the day, plus the breaks between sessions
		for n, session_data in enumerate(self.sessions):  # Iterate through each session in the timetable data
			name, is_normal = session_data  # Get the data for the session

			## Add a header label
			header = tk.Label(self.table_frame, text=name, background='#424D59' if is_normal else '#303841', foreground='#D4D6D7' if is_normal else '#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Calibri', 13), image=master.pixel, compound='center', width=15, height=19)
			header.grid(row=n + 1, column=0, columns=1 if is_normal else 6, sticky='NSWE', padx=(1, int(not is_normal)), pady=(int(n == 0), 1))

			## Add the label to the corresponding list depending on weather or not it is a session break
			if is_normal:
				self.session_headers.append(header)
			else:
				self.session_break_idxs[0].append(n)  # Add the grid index to the session break list
				self.session_break_idxs[1].append(n - len(self.session_break_idxs[0]))  # Add the total row offset to the session break list
				self.table_frame.rowconfigure(n + 1, weight=0)  # Configure the grid so that session breaks do not expand

		## Add the timetable cells for the table body
		for daynum, sessions in enumerate(self.class_mapping):  # Iterate through the columns (days) in the class mapping
			self.tt_elements.append([])  # Add a new empty list to the timetable cell array
			for sessionnum, ttclass in enumerate(sessions):  # Iterate through the session mapping for the day
				cell = SessionCell(self, self.table_frame, daynum, sessionnum, ttclass)  # Create a cell for at the current column and row index with the corresponding class mapping
				self.tt_elements[-1].append(cell)  # Add the cell to the list
				cell.grid()  # Add the cell to the display grid

		## Add a cell for each of the weekends
		for i in range(2):
			cell = WeekendCell(self, self.table_frame, i)
			self.tt_elements.append([cell])
			cell.grid()

		## Add a marker for the current session
		self.current_session_marker = tk.Frame(self.table_frame, background='#8C3841', highlightthickness=1, highlightbackground='#969CA3')
		self.current_session_marker.bind('<Button-1>', lambda v: self.select(self.day, self.timeslot_idx))
		pywinstyles.set_opacity(self.current_session_marker.winfo_id(), 0.2)

		self.increment_timeslot()  # Update the displayed timeslot

	def change_week(self) -> None:
		""" Change the current start timestamp and update the week accordingly """
		self.start_timestamp = self.master.get_start_week(allow_cancel=True)
		self.week = self.get_week(datetime.datetime.now().timestamp())
		self.update_week(self.week)

	def get_sessiontimes(self, data: list[tuple[str, bool, str]]) -> tuple[list[list[str, bool]], list[list[int]]]:
		"""
		Get the timestamp of each 'period change' and format the session data for use by the program.

		:param data: The session data to process
		:return: A list containing each session’s name and type, as well as a list containing the 'period change' indexes
		"""

		session_times = [list(map(int, self.day_start_time.split(':')))]  # Define a list to contain the hour and minute of each 'period change' with an initial value of the day start timestamp.

		for idx, time in enumerate(swapaxes(data)[2]):  # Iterate through the session data
			if time == '-1':  # If the session’s end time is '-1' (i.e.: until the end of the day), add [-1, -1] to the 'period change' time list
				session_times.append([-1, -1])
			else:
				## Add the session’s end time to the 'period change' time list
				t = list(map(int, time.split(':')))
				session_times.append(t)

		return swapaxes(swapaxes(data)[:2]), session_times

	def get_week(self, now: float) -> int:
		"""
		Get the week number from the current timestamp.

		:param now: The current timestamp.
		:return: The number of weeks since the starting timestamp (ie: the current week number).
		"""

		return int((now - self.start_timestamp) // (86400 * 7))

	@staticmethod
	def validate_session(now: datetime.datetime, h1: int, m1: int, h2: int, m2: int) -> bool:
		"""
		Check if the input time is within the input time range

		:param now: The input time to compare.
		:param h1: The 'hours' part of the start of the time range.
		:param m1: The 'minutes' part of the start of the time range.
		:param h2: The 'hours' part of the end of the time range.
		:param m2: The 'minutes' part of the end of the time range.
		:return: Whether or not the input time is within the input time range.
		"""

		if h2 == -1 and m2 == -1:  # If the time range extends until the end of the day
			return now.hour > h1 or now.hour == h1 and now.minute > m2
		elif h1 == h2:
			return now.hour == h1 and m1 <= now.minute <= m2
		else:
			return (now.hour == h1 and now.minute >= m1) or (now.hour == h2 and now.minute < m2)

	def get_session(self, now: datetime.datetime) -> Optional[int]:
		"""
		Get the index of the session at the input time.

		:param now: The time to check
		:return: The index of the session at the input time
		"""

		for n, i in enumerate(zip(*swapaxes(self.sessiontimes[:-1]), *swapaxes(self.sessiontimes[1:]))):  # Iterate through the session start and end times
			if self.validate_session(now, *i):  # If the input time is within the session start and end times, return the index of the session
				return n

		## If the current time is not within any session
		if now.hour > 14 or (now.hour == 45 and now.minute > 45):  # Check if the session is after 14:45 and if so, return the index of the last session, otherwise return None.
			return 10
		else:
			return None

	def update_list_format(self) -> None:
		""" Update the numbering type of the selected text or current line to match the value set by the user. """
		tags = self.event_entry.tag_ranges('sel')  # Get the selection range

		if not tags:  # If there is no selection
			positions = [[int(self.event_entry.index(tk.INSERT).split('.')[0])] * 2]  # Set the position range to the line that the cursor is on
		else:
			positions = [[int(str(a).split('.')[0]), int(str(b).split('.')[0])] for a, b in zip(tags[:-1:2], tags[1::2])]  # Add the range of each selection to a list of position ranges

		for pos in positions:  # Iterate through each range of lines in the selection
			lines = self.event_entry.get(f'{pos[0]}.0', f'{pos[1]}.end').split('\n')  # Get all lines in the current range
			indent = self.event_entry.get_indent(line=lines[0])  # Get the indent of the first line in the range
			if indent is None:  # If the first line has no indent
				numbering_loc = [0, 1]  # Set the location of the numbering to the first character
				indent = ' \t'  # Set the indent to a space and a tab
			else:
				numbering_loc = re.match(rf'[^ \t]+', indent)  # Find the location of the numbering within the indent
				if numbering_loc is None:  # If the indent has no numbering, set the location of the indent to the last character
					numbering_loc = [len(indent) - 1] * 2
				else:
					numbering_loc = numbering_loc.span()  # Otherwise, set the location of the numbering to the match position of the pattern above

			new_lines = []  # Create a list to hold the new lines to insert
			maxlen = None  # Create a variable to hold the maximum length of the numbering

			for ln, line in list(enumerate(lines))[::-1]:  # Iterate through each line in the range
				numbering = ''  # Define a variable to hold the numbering string

				## Get the indent of the current line
				line_indent = self.event_entry.get_indent(line=line)
				if line_indent is None:
					line_indent = ''

				## Get the numbering string corresponding to the selected numbering format
				match self.numbering_format.get():
					case 0:  # No numbering
						numbering = ''
					case 1:  # Dotpoints
						numbering = '•'
					case 2:  # Numbers
						numbering = str(ln + 1) + '.'
					case 3:  # Letters
						## Convert the line number to base 26
						numbering = []  # Define an array to hold the numbering characters
						val = ln + 1  # Calculate the remaining 'value' to add the base-26 number

						while val > 0:  # While there is a remaining value
							numbering.append(chr(ord('a') + (val % 26) - 1))  # Add the character corresponding to mod 26 of the remaining value to the numbering character list
							val //= 26  # Divide the remaining value by 26
						numbering = ''.join(numbering[::-1]) + ')'  # Join the numbering characters into a string

				## Work out the padding to apply to the indent numbering
				if maxlen is None:
					maxlen = len(numbering)

				new_line = list(indent)  # Split the indent into a list of characters
				new_line[slice(*numbering_loc)] = list(numbering.rjust(maxlen))  # Add the numbering to the indent
				new_lines.append(''.join(new_line) + line.removeprefix(line_indent))  # Join the indent text into a string and add it to the rest of the line. Remove the previous indent.

			self.event_entry.replace(f'{pos[0]}.0', f'{pos[1]}.end', '\n'.join(new_lines[::-1]))  # Add the updated lines to the text widget
			self.event_entry.tag_add('sel', f'{pos[0]}.0', f'{pos[1]}.end')  # Select the updated lines

	def on_edit(self, skip_after: bool = False) -> None:
		"""
		Update the numbering mode and syntax highlighting when the text widget is modified.

		:param skip_after: Whether to skip calling this function again after a delay
		"""

		cursor_position = self.event_entry.index(tk.INSERT).split('.')[0]  # Get the line number of the cursor position
		tags = self.event_entry.tag_names(cursor_position + '.0')  # Get the text tags for the same line as the cursor

		## TODO: behaviour with text selection

		list_mode = ['DOTPOINT' in tags, 'NUMBERING' in tags, 'LETTERING' in tags]  # Check weather any of the supported dotpoint / numbering formats are in the selected line

		if any(list_mode):  # If the selected line has numbering, update the current numbering format to the numbering format in the line
			self.numbering_format.set(list_mode.index(True) + 1)
		else:
			self.numbering_format.set(0)  # Otherwise, set the numbering format to disabled

			## The colouriser in the IndentText widget creates a 'TO​DO' tag, for updating colouration data on the next frame when the contents of the text widget are changed.
			## This code detects that tag and updates the formatting.
			if 'TODO' in tags and not skip_after:  # If the colouriser has marked the current line to update the syntax highlighting, call the function again after 2 ms, unless disabled.
				if self.formatting_update_after is not None:
					self.event_entry.after_cancel(self.formatting_update_after)
				self.formatting_update_after = self.event_entry.after(2, lambda: self.on_edit(True))

	def select(self, day: int, session: int, get_index: bool = True) -> None:
		"""
		Select the cell at the given day and session index

		:param day: The day index to select
		:param session: The session index to select or a timeslot number
		:get_index: Whether to treat the session parameter as a session index or a timeslot index
		"""

		if get_index:
			session = self.get_session_index(session)

		if day is not None and session is not None:
			self.tt_elements[day][session].toggle_selected()

	def increment_timeslot(self) -> None:
		"""
		Increment the current session number, update the displayed session and day, and get the time to the next period change
		"""

		now = datetime.datetime.now()  # Get the current time

		## TODO: make sure this works correctly
		if now.weekday() > 4:  # Check if the current day is a weekend
			self.timeslot_idx = 0  # Set the current timeslot to 0
			update_time = self.sessiontimes[0]
		else:
			self.timeslot_idx = (self.timeslot_idx + 1) % (len(self.sessions) + 1)  # Increment the current timeslot index
			update_time = (self.sessiontimes[:-1] + [24, 1])[self.timeslot_idx]  # Get the timestamp for the end of the current timeslot

		update_ms = (3600000 * (update_time[0] - now.hour)) + (60000 * (update_time[1] - now.minute)) - now.second  # Calculate the time in milliseconds until the end of the timeslot
		self.update_timeslot_display()  # Update the displayed timeslot

		self.display_frame.after(update_ms, self.increment_timeslot)  # Call the function again after the calculated time

	def update_timeslot_display(self) -> None:
		""" Update the displayed timeslot in the timetable """

		now = datetime.datetime.now()  # Get the current time
		self.day = now.weekday()  # Get the current day of the week

		## If the previous active header is different to the current, change the configuration of the previous header to inactive
		if self.active_dotw_header is not None and self.active_dotw_header != self.day:
			self.dotw_headers[self.active_dotw_header].configure(**self.inactive_header_config)
			self.active_dotw_header = None

		if self.active_session_header is not None:
			self.session_headers[self.active_session_header].configure(**self.inactive_header_config)
			self.active_session_header = None

		## If the current week is the same as the displayed week
		if self.week == self.get_week(now.timestamp()):
			if self.active_dotw_header is None:
				self.active_dotw_header = self.day  # Update the index of the active header
				self.dotw_headers[self.active_dotw_header].configure(**self.active_header_config)  # Configure the colours of the active header

			if self.timeslot_idx != len(self.sessions):  # If the current timeslot is visible in the timetable
				session = self.get_session_index()  # Get the session number from the timeslot index
				if session is not None:  # If the session has an associated row header
					self.active_session_header = session  # Update the index of the active row header
					self.session_headers[session].configure(**self.active_header_config)  # Configure the colours of the active row header

				## Add the timeslot marker to the current session
				self.current_session_marker.grid_configure(row=self.timeslot_idx + 1, column=self.day + 1, sticky='NSWE', padx=(int(self.day == 0), 1), pady=(int(self.timeslot_idx == 0), 1), rows=len(self.sessions) if self.day > 4 else 1)
			else:  # If the current timeslot is not visible on the timetable, remove the timeslot marker.
				self.current_session_marker.grid_remove()

	def save_as(self) -> None:
		"""
		Prompt the user for a file path, update the active filename to said path, and save the timetable file.
		"""

		## Prompt the user to enter a path to save as
		name = fd.asksaveasfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.master.filename), confirmoverwrite=True, initialfile=self.master.filename, parent=self.master)

		if name:  # If the user did not cancel
			self.master.filename = name  # Update the stored path
			self.master.top_bar.filename_display.configure(text=name)  # Update the displayed path
			self.master.settings.update({'default.path': name})  # Update the default path
			self.save_timetable()  # Save the timetable

	def save_copy(self) -> None:
		"""
		Prompt the user for a filename and save a copy of the timetable at the specified location
		"""

		## Prompt the user to enter a file path
		name = fd.asksaveasfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.master.filename), confirmoverwrite=True, initialfile=self.master.filename, parent=self.master)

		if name:  # If the user did not cancel, save a copy of the timetable at the input location
			self.save_timetable(name)

	def save_timetable(self, filename: Optional[str] = None, encoding: str = 'utf-8') -> None:
		"""
		Get all timetable data and save as a JSON file
		"""

		## Get the path to save at
		if filename is None:
			filename = self.master.filename

		json_data = self.get_json()  # Get the json formatted text to save

		try:  # Attempt to save the file
			with open(filename, 'w', encoding=encoding) as writefile:  # Open the output file and write the json text
				writefile.write(json_data)

			self.master.display_popup('Saved Successfully')  # Display a popup that the file was saved
			self.current_savefile_contents = multireplace(json_data, {'\n': '', '    ': '', '\t': ''})  # Update the string containing the timetable data that is currently saved
			self.events_saved = True
			self.update_save_buttons()  # Disable save button
		except PermissionError:
			self.master.display_popup('Could not save: Permission Denied')  # Display a popup that the file could not be saved due to a permission error

	def update_save_buttons(self) -> None:
		"""
		Update the state of the `save` and `save as` buttons based on the save state of the timetable
		"""

		state = 'disabled' if self.events_saved else 'normal'  # Get the state to use

		## Update the buttons
		self.saveas_button.configure(state=state)
		self.save_button.configure(state=state)

	def check_saved(self, json_data: str) -> bool:
		"""
		Check if the current timetable data matches the saved timetable data.

		:param json_data: The JSON formatted timetable data to check
		"""

		if self.current_savefile_contents is None:  # If the savefile contents string is empty, set its value to the contents of the existing timetable data file
			with open(self.master.filename, encoding='utf-8') as file:
				self.current_savefile_contents = multireplace(''.join(file.readlines()), {'\n': '', '    ': '', '\t': ''})

		self.events_saved = multireplace(json_data, {'\n': '', '    ': '', '\t': ''}) == self.current_savefile_contents  # Check if the saved timetable matches the current timetable
		self.update_save_buttons()  # Update the state of the `save` and `save as` buttons
		return self.events_saved  # Return the result

	def edit_event_type(self) -> None:
		"""
		Update the displayed event type icons whenever the event type of the current event is changed
		"""

		self.check_saved(self.get_json())  # Check if the file is saved to update the save/saveas buttons
		self.week_elems[self.week].edit_event_type(self.active_cell.current_event)  # Update the event type count for the selected event’s week.

		if self.active_cell is not None and self.active_cell.current_event is not None:  # If a cell is selected which has an event
			self.active_cell.events_indicator.configure(image=self.master.icons[self.active_cell.current_event.type()])  # Update the displayed event type icon for the cell

	def get_session_index(self, timeslot: int = None) -> int | None:
		"""
		Get the session index corresponding to the input timeslot

		:param timeslot: The input timeslot to process. Leave blank for the current timeslot
		:return: The session index corresponding to the input timeslot
		"""

		## Get the timeslot
		if timeslot is None:
			timeslot = self.timeslot_idx

		if timeslot == len(self.sessions) or timeslot in self.session_break_idxs[0]:  # Check if the current timeslot is a break or is not displayed on the table
			return None
		else:
			return timeslot - sum(map(lambda v: timeslot > v, self.session_break_idxs[0]))  # Otherwise, subtract the offset caused by the session breaks

	def update_week(self, value: str | int) -> None:
		"""
		Update current displayed week and associated information.

		:param value: The index of the new week to use
		"""

		events = list(filter(lambda v: v.week in [int(value), self.week], self.events))  # Get all events that occur in the current and new week

		## Configure the formatting of the week displays to match the new week
		self.week_elems[self.week].numlabel.configure(font=('Arial', 11))
		self.week_elems[int(value)].numlabel.configure(font=('Arial', 11, 'bold'))

		self.week = int(value)  # Convert the value string returned by the slider element to an integer and update the current week number

		## Iterate through events that occur in the new and current weeks and update the associated cells
		for event in events:
			cell = self.tt_elements[event.day][event.session]
			cell.update_event()

		## Update the data displayed on the timetable
		if self.week != self.get_week(datetime.datetime.now().timestamp()):  # If the current displayed week is not the actual week
			if self.current_session_marker.grid_info():  # If the timeslot marker is displayed, hide it and reset the formatting of the active headers
				self.current_session_marker.grid_remove()
				session = self.get_session_index()
				if session is not None:
					self.session_headers[session].configure(**self.inactive_header_config)
				self.dotw_headers[self.day].configure(**self.inactive_header_config)

		else:  # If the new week is the actual week
			if not self.current_session_marker.grid_info():  # If the timeslot marker is not displayed, add it to the grid and update the formatting of the headers for the current timeslot
				self.current_session_marker.grid()
				session = self.get_session_index()
				if session is not None:
					self.session_headers[session].configure(**self.active_header_config)
				self.dotw_headers[self.day].configure(**self.active_header_config)

	def create_event(self) -> None:
		"""
		Create an event for the current selected cell
		"""

		## TODO: test behaviour when an event already exists
		if self.active_cell is not None:  # If a cell is selected
			event = Event(self.week, self.active_cell.day, self.active_cell.session, '', None, 'Event')  # Create an event
			self.events.append(event)  # Add the new event object to the event list
			self.active_cell.set_event(event)  # Set the event of the current cell to the newly created event
			self.update_active_event()  # Update the timetable’s active event
			self.event_entry.focus_set()  # Set the focus into the event text entry widget
			self.check_saved(self.get_json())  # Update the save state for the timetable
			self.week_elems[self.week].add_event(event)  # Add the event to its corresponding week to update the appropriate event type counter

	def _proxy(self, *args: tuple[Any]) -> Any:
		""" Called whenever an event occurs in the element. Raises an '<<Edit>>' event when the text is edited and a '<<Change>> event when the cursor is moved'. """
		cmd = (self.event_entry._orig,) + args  # Get the tk command to run

		## Attempt to call the tk command based on the input arguments
		try:
			result = self.event_entry.tk.call(cmd)
		except tk.TclError:
			result = None

		## If the command is inserting text (typing, pasting, inserting, etc), raise an '<<Edit>>' event
		if args[0] in ('insert', 'replace', 'delete'):
			self.event_entry.event_generate('<<Edit>>', when='tail')

		## If the command is moving the cursor, raise a '<<Change>>' event
		if args[0:3] == ('mark', 'set', 'insert'):
			self.event_entry.event_generate('<<Change>>', when='tail')

		return result  # Return the result of running the input tk command

	def delete_event(self, confirm: bool = True) -> None:
		"""
		Delete the current active event.

		:param confirm: Weather or not to ask the user for confirmation before deleting the event
		"""

		## Ask the user to confirm deletion
		if confirm and mb.askokcancel('Delete Event?', 'Do you really want to delete all events on the selected session?') is not True:
			return

		if self.active_cell is not None and self.active_cell.current_event is not None:  # If the selected cell with an event
			event = self.active_cell.current_event  # Get the event object of the selected cell
			self.events.remove(event)  # Remove the event from the event list
			self.week_elems[self.week].remove_event(event)  # Remove the event from the stored events in the week element corresponding to the event’s week
			self.active_cell.set_event(None)  # Reset the selected cell’s current event
			self.update_active_event()  # Update the timetable’s displayed event
			self.check_saved(self.get_json())  # Update the timetable’s save-state

	def get_json(self) -> str:
		"""
		Get the JSON formatted text representing the timetable data
		"""

		## Todo: behaviour when quoting characters are in text

		## Get the name, room, and teacher of each class
		classes = list(map(lambda v: v.get().replace("'", "\\'").replace('"', '\\"'), self.classes))
		rooms = list(map(lambda v: v.get().replace("'", "\\'").replace('"', '\\"'), self.rooms))
		teachers = list(map(lambda v: v.get().replace("'", "\\'").replace('"', '\\"'), self.teachers))

		## Initiate a buffer with the names, rooms, and events of each class represented in JSON format
		buffer = (
			'{\n'
			f'    "classes": {classes},\n'
			f'    "teachers": {teachers},\n'
			f'    "rooms": {rooms},\n'
			'    "timetable": [\n'
		)

		## Add the class mapping to the buffer
		for i in self.class_mapping:
			buffer += f'        {i},\n'

		## Add the 'events' key to the buffer
		buffer = buffer[:-2] + '\n    ],\n    "events": ['

		## Add the events to the buffer
		for num, event in enumerate(self.events):  # Iterate through all of the stored events
			buffer += ',' if buffer[-1] == '}' else ''  # Add a comma to the buffer
			event_data = []  # Define an empty list to store the lines of event data
			for k, v in event.get_data().items():  # Get the event data from the event and add each item to the event data list as a string
				event_data.append(f'"{k}": {v}')
			buffer += f'\n        {{\n            ' + ',\n            '.join(event_data) + '\n        }'  # Add the event data to the buffer with the appropriate formatting

		## .replace("'", '"')
		buffer += '\n    ],\n    "sessions": [\n'  # Add the 'sessions' key to the buffer

		session_data = []  # Define a list to store the lines of session data
		for session, time in zip(self.sessions, self.sessiontimes[1:]):  # Iterate through each session
			session_data.append(f'        ["{session[0]}", {"true" if session[1] else "false"}, "' + (f'{time[0]:>02n}:{time[1]:<02n}' if time[0] != -1 else '-1') + '"]')  # Add the formatted session data to the list
		buffer += ',\n'.join(session_data)  # Add the session data to the buffer with the appropriate formatting
		buffer += f'\n    ],\n    "day_start": "{self.day_start_time}",\n    "start_date_timestamp": {self.start_timestamp}\n}}'  # Add the day and term start times to the buffer
		return buffer  # Return the result

	def update_button_states(self) -> None:
		"""
		Update the save state of the timetable and update the state of the save and saveas buttons
		"""

		if self.active_cell is not None and self.active_cell.current_event is not None:  # If a cell is selected with an event
			self.active_cell.current_event.text = self.event_entry.get(1.0, tk.END).strip('\n')  # Set the cell’s event’s text to the text currently in the event text entry

		if self.pause_text_event:  # If text events are paused, unpause them and skip the rest of the function
			self.pause_text_event = False
		else:  # Otherwise, update the save state of the timetable
			if self.event_entry.get(1.0, tk.END).strip('\n') != self.active_cell.current_event.text.strip('\n'):
				self.events_saved = False
			else:
				self.check_saved(self.get_json())

	def edit_class_names(self, idx: int) -> None:
		"""
		Update the values in the class name selection combobox and update the timetable’s save-state

		:param idx: The index of the combobox value to update
		"""

		values = [v.get() for v in self.classes]  # Get all the stored class names
		self.class_name_combobox.set(values[idx])  # Update the value of the combobox
		self.class_name_combobox.configure(values=values)  # Update the list of possible values in the combobox
		self.check_saved(self.get_json())  # Update the timetable’s save-state

	def new_class(self) -> None:
		"""
		Create a new class to map in the timetable
		"""

		## Todo: implement timetable_class class

		idx = len(self.classes)  # Get the index of the new class
		self.active_cell.class_data_idx = idx  # Update the class data mapping of the current cell
		self.classes.append(tk.StringVar(self.master, f'<Class-{idx}>'))  # Add a new string variable to the list of classes
		self.classes[-1].trace('w', lambda a, b, c, n=idx: self.edit_class_names(n))  # Add an edit trace to the class name stringvar

		self.class_name_combobox.current(idx)  # Set the value of the class selector combobox to the new class

		## Add string variables for the room and teacher
		self.teachers.append(tk.StringVar(self.master, ''))
		self.rooms.append(tk.StringVar(self.master, ''))

		self.active_cell.update_sessiondata()  # Update the selected cell’s session data

		self.check_saved(self.get_json())  # Update the timetable’s save-state

	def delete_class(self, confirm: bool = True) -> None:
		"""
		Delete the selected timetable class

		:param confirm: Weather to ask the user for confirmation before deleting
		"""

		## Ask the user to confirm the deletion
		if confirm and mb.askokcancel('Delete Class?', 'Do you really want to delete all instances of this class?') is not True:
			return

		idx = self.active_cell.class_data_idx  # Get the mapped class index of the current cell
		for row in self.tt_elements:  # Iterate through each cell in the timetable and reset its class and mapping if it is mapped to the deleted class
			for elem in row:
				if elem.class_data_idx == idx:
					elem.class_data_idx = None
					elem.update_sessiondata()
		self.class_name_combobox.set('')  # Delete the contents of the class name selection combobox
		self.check_saved(self.get_json())  # Update the save state of the timetable

	def edit_class(self) -> None:
		"""
		Update the values of the cells mapped to the edited class
		"""

		## Get the index of the edited class
		idx = self.class_name_combobox.current()
		if idx == -1:
			self.class_name_combobox.current(self.active_cell.class_data_idx)  # Set the value of the class selection combobox to the class mapping of the selected cell
		else:
			self.active_cell.class_data_idx = self.class_name_combobox.current()  # Set the mapping of the selected cell to the value of the class selection combobox
			self.active_cell.update_sessiondata()

		self.check_saved(self.get_json())  # Update the save state of the timetable

	def update_active_event(self) -> None:
		"""
		Configure the necessary active and displayed data associated with events to reflect the event of the selected timetable cell.
		"""

		if self.active_cell is None or self.active_cell.weekend:  # If no cell is selected or the cell is on a weekend
			## Disable the timetable class data entries
			self.name_entry.configure(textvariable=self.empty_text_variable, state='disabled')
			self.teacher_entry.configure(textvariable=self.empty_text_variable, state='disabled')
			self.room_entry.configure(textvariable=self.empty_text_variable, state='disabled')

			## Update the values and states of the UI elements
			self.delete_class_button.configure(state='disabled')
			self.class_name_combobox.configure(state='disabled')
			self.class_name_combobox.set('')
		else:
			## Set the variables of the class data entries to those of the selected cell
			self.name_entry.configure(textvariable=self.active_cell.name, state='normal')
			self.teacher_entry.configure(textvariable=self.active_cell.teacher, state='normal')
			self.room_entry.configure(textvariable=self.active_cell.room, state='normal')

			## Update the value of the class selection combobox
			self.class_name_combobox.configure(state='readonly')
			self.class_name_combobox.current(self.active_cell.class_data_idx)

			## Update the state of the delete class button
			if self.active_cell.class_data_idx is None:
				self.delete_class_button.configure(state='disabled')
			else:
				self.delete_class_button.configure(state='normal')

		if self.active_cell is None or self.active_cell.current_event is None:  # If no cell with an event is selected
			if not self.event_info_label.grid_info():  # Cover the event text entry with a label
				self.event_info_label.grid()

			if self.active_cell is not None:  # If a cell is selected, set the label’s text to prompt the user to create an event
				self.event_info_label.configure(text='No Events\n(click to create)')
			else:  # Otherwise, set the label’s text to prompt the user that there is no selection
				self.event_info_label.configure(text='No Selection')

			## Disable the 'delete' button and event type picker
			self.delete_button.configure(state='disabled')
			self.event_type_combobox.configure(state='disabled', textvariable=self.empty_text_variable)
			self.event_type_combobox.set('')
		else:  # If a cell with an event is selected
			if self.event_info_label.grid_info():  # Remove the label covering the event text entry
				self.event_info_label.grid_remove()

			self.event_info_label.configure(text='1 Event')  # Display the number of events in the selection (Note: under normal circumstances, there can only be one event in a cell)
			self.event_entry.replace(1.0, tk.END, self.active_cell.current_event.text)  # Add the selected event’s text to the event text entry

			## Enable the 'delete event' button and the event type picker. Update the current value of the event type picker.
			self.delete_button.configure(state='normal')
			self.event_type_combobox.configure(state='normal', textvariable=self.active_cell.current_event.event_type)

			self.pause_text_event = True  # Pause text events

	def __exit__(self, exc_type, exc_val, exc_tb) -> None:
		"""
		Define what happens when the class is deleted
		"""

		self.display_frame.destroy()  # Close the window
		del self  # Remove the class from memory

	def destroy(self) -> None:
		"""
		Destroy the window and delete the class from memory
		"""

		self.__exit__(None, None, None)


class Window(tk.Tk):
	"""
	The main window widget holding the timetable to display.
	Handles loading and exporting of timetables as well as calculations involving the week number.

	:param file_checks: The result of validating the necessary files for the program to run outputted by the `validate_local_files` function
	"""

	def __init__(self, file_checks, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)

		self.focus()  # Set the focus into the window
		self.title(f'Timetable V{VERSION}')  # Set the title of the window

		self.pixel = tk.PhotoImage(width=1, height=1)  # Create a transparent 1px by 1px image. When used as the image for a widget such as a button or label, it allows for the size of said widget to be adjusted in pixels rather than arbitrary units.

		## Load the SVG icons stored on disk to a dictionary
		self.icons = load_images(
			[
				('icons/dotpoints.svg', 'dotpoints', 18),
				('icons/numbering3.svg', 'numbering', 18),
				('icons/lettering.svg', 'lettering', 18),

				('icons/calendar.svg', 'calendar', 20),
				('icons/saveas.svg', 'saveas', 20),
				('icons/savecopy.svg', 'savecopy', 20),
				('icons/new_timetable.svg', 'new', 23),
				('icons/import.svg', 'import', 20),
				('icons/export.svg', 'export', 20),
				('icons/pdf_icon.svg', 'pdf', 20),
				('icons/xls_icon.svg', 'xls', 20),
				('icons/csv_icon.svg', 'csv', 20),
				('icons/help_icon.svg', 'help', 20),
				('icons/about_icon.svg', 'about', 20),
				('icons/win_icon2.svg', 'window_icon2', 64)
			]
		)

		## Add the other SVGs to the icon dictionary
		self.icons.update(
			{
				'Event': tksvg.SvgImage(data=b'<svg viewBox="0 0 512 512" fill="#e55"><path d="M504 256c0 136.997-111.043 248-248 248S8 392.997 8 256C8 119.083 119.043 8 256 8s248 111.083 248 248zm-248 50c-25.405 0-46 20.595-46 46s20.595 46 46 46 46-20.595 46-46-20.595-46-46-46zm-43.673-165.346l7.418 136c.347 6.364 5.609 11.346 11.982 11.346h48.546c6.373 0 11.635-4.982 11.982-11.346l7.418-136c.375-6.874-5.098-12.654-11.982-12.654h-63.383c-6.884 0-12.356 5.78-11.981 12.654z"/></svg>', scaletowidth=10),
				'Info': tksvg.SvgImage(data=b'<svg viewBox="0 0 512 512" fill="#55e"><path d="M256 8C119.043 8 8 119.083 8 256c0 136.997 111.043 248 248 248s248-111.003 248-248C504 119.083 392.957 8 256 8zm0 110c23.196 0 42 18.804 42 42s-18.804 42-42 42-42-18.804-42-42 18.804-42 42-42zm56 254c0 6.627-5.373 12-12 12h-88c-6.627 0-12-5.373-12-12v-24c0-6.627 5.373-12 12-12h12v-64h-12c-6.627 0-12-5.373-12-12v-24c0-6.627 5.373-12 12-12h64c6.627 0 12 5.373 12 12v100h12c6.627 0 12 5.373 12 12v24z"/></svg>', scaletowidth=12),
				'Reminder': tksvg.SvgImage(data=b'<svg viewBox="0 0 448 512" fill="#ee5"><path d="M224 512c35.32 0 63.97-28.65 63.97-64H160.03c0 35.35 28.65 64 63.97 64zm215.39-149.71c-19.32-20.76-55.47-51.99-55.47-154.29 0-77.7-54.48-139.9-127.94-155.16V32c0-17.67-14.32-32-31.98-32s-31.98 14.33-31.98 32v20.84C118.56 68.1 64.08 130.3 64.08 208c0 102.3-36.15 133.53-55.47 154.29-6 6.45-8.66 14.16-8.61 21.71.11 16.4 12.98 32 32.1 32h383.8c19.12 0 32-15.6 32.1-32 .05-7.55-2.61-15.27-8.61-21.71z"/></svg>', scaletowidth=12),
				'Bookmark': tksvg.SvgImage(data=b'<svg viewBox="0 0 384 512" fill="#5e5"><path d="M0 512V48C0 21.49 21.49 0 48 0h288c26.51 0 48 21.49 48 48v464L192 400 0 512z"/></svg>', scaletowidth=12),
				'Assignment': tksvg.SvgImage(data=b'<svg viewBox="0 0 576 512" fill="#e5e"><path d="M542.22 32.05c-54.8 3.11-163.72 14.43-230.96 55.59-4.64 2.84-7.27 7.89-7.27 13.17v363.87c0 11.55 12.63 18.85 23.28 13.49 69.18-34.82 169.23-44.32 218.7-46.92 16.89-.89 30.02-14.43 30.02-30.66V62.75c.01-17.71-15.35-31.74-33.77-30.7zM264.73 87.64C197.5 46.48 88.58 35.17 33.78 32.05 15.36 31.01 0 45.04 0 62.75V400.6c0 16.24 13.13 29.78 30.02 30.66 49.49 2.6 149.59 12.11 218.77 46.95 10.62 5.35 23.21-1.94 23.21-13.46V100.63c0-5.29-2.62-10.14-7.27-12.99z"/></svg>', scaletowidth=12),
				'Test': tksvg.SvgImage(data=b'<svg viewBox="0 0 512 512" fill="#eee"><path d="M79.18 282.94a32.005 32.005 0 0 0-20.24 20.24L0 480l4.69 4.69 92.89-92.89c-.66-2.56-1.57-5.03-1.57-7.8 0-17.67 14.33-32 32-32s32 14.33 32 32-14.33 32-32 32c-2.77 0-5.24-.91-7.8-1.57l-92.89 92.89L32 512l176.82-58.94a31.983 31.983 0 0 0 20.24-20.24l33.07-84.07-98.88-98.88-84.07 33.07zM369.25 28.32L186.14 227.81l97.85 97.85 199.49-183.11C568.4 67.48 443.73-55.94 369.25 28.32z"/></svg>', scaletowidth=12),

				'restore': None,
				'version': None,
				'new_event': None,
				'new_class': None,
				'delete_event': None,
				'delete_class': None,
				'bug': tksvg.SvgImage(data=b'<svg viewBox="0 0 512 512" fill="#D4D4D4"><path d="M256 0c53 0 96 43 96 96v3.6c0 15.7-12.7 28.4-28.4 28.4H188.4c-15.7 0-28.4-12.7-28.4-28.4V96c0-53 43-96 96-96zM41.4 105.4c12.5-12.5 32.8-12.5 45.3 0l64 64c.7 .7 1.3 1.4 1.9 2.1c14.2-7.3 30.4-11.4 47.5-11.4H312c17.1 0 33.2 4.1 47.5 11.4c.6-.7 1.2-1.4 1.9-2.1l64-64c12.5-12.5 32.8-12.5 45.3 0s12.5 32.8 0 45.3l-64 64c-.7 .7-1.4 1.3-2.1 1.9c6.2 12 10.1 25.3 11.1 39.5H480c17.7 0 32 14.3 32 32s-14.3 32-32 32H416c0 24.6-5.5 47.8-15.4 68.6c2.2 1.3 4.2 2.9 6 4.8l64 64c12.5 12.5 12.5 32.8 0 45.3s-32.8 12.5-45.3 0l-63.1-63.1c-24.5 21.8-55.8 36.2-90.3 39.6V240c0-8.8-7.2-16-16-16s-16 7.2-16 16V479.2c-34.5-3.4-65.8-17.8-90.3-39.6L86.6 502.6c-12.5 12.5-32.8 12.5-45.3 0s-12.5-32.8 0-45.3l64-64c1.9-1.9 3.9-3.4 6-4.8C101.5 367.8 96 344.6 96 320H32c-17.7 0-32-14.3-32-32s14.3-32 32-32H96.3c1.1-14.1 5-27.5 11.1-39.5c-.7-.6-1.4-1.2-2.1-1.9l-64-64c-12.5-12.5-12.5-32.8 0-45.3z"/></svg>', scaletowidth=20),
				'feature': None,

				'save': tksvg.SvgImage(data=b'<svg viewBox="0 0 448 512" fill="#D4D4D4"><path d="M48 96V416c0 8.8 7.2 16 16 16H384c8.8 0 16-7.2 16-16V170.5c0-4.2-1.7-8.3-4.7-11.3l33.9-33.9c12 12 18.7 28.3 18.7 45.3V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96C0 60.7 28.7 32 64 32H309.5c17 0 33.3 6.7 45.3 18.7l74.5 74.5-33.9 33.9L320.8 84.7c-.3-.3-.5-.5-.8-.8V184c0 13.3-10.7 24-24 24H104c-13.3 0-24-10.7-24-24V80H64c-8.8 0-16 7.2-16 16zm80-16v80H272V80H128zm32 240a64 64 0 1 1 128 0 64 64 0 1 1 -128 0z"/></svg>', scaletowidth=20),
				'load': tksvg.SvgImage(data=b'<svg viewBox="0 0 576 512" fill="#D4D4D4"><path d="M88.7 223.8L0 375.8V96C0 60.7 28.7 32 64 32H181.5c17 0 33.3 6.7 45.3 18.7l26.5 26.5c12 12 28.3 18.7 45.3 18.7H416c35.3 0 64 28.7 64 64v32H144c-22.8 0-43.8 12.1-55.3 31.8zm27.6 16.1C122.1 230 132.6 224 144 224H544c11.5 0 22 6.1 27.7 16.1s5.7 22.2-.1 32.1l-112 192C453.9 474 443.4 480 432 480H32c-11.5 0-22-6.1-27.7-16.1s-5.7-22.2 .1-32.1l112-192z"/></svg>', scaletowidth=20),

				'undo': tksvg.SvgImage(data=b'<svg viewBox="0 0 512 512" fill="#D4D4D4"><path d="M48.5 224H40c-13.3 0-24-10.7-24-24V72c0-9.7 5.8-18.5 14.8-22.2s19.3-1.7 26.2 5.2L98.6 96.6c87.6-86.5 228.7-86.2 315.8 1c87.5 87.5 87.5 229.3 0 316.8s-229.3 87.5-316.8 0c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0c62.5 62.5 163.8 62.5 226.3 0s62.5-163.8 0-226.3c-62.2-62.2-162.7-62.5-225.3-1L185 183c6.9 6.9 8.9 17.2 5.2 26.2s-12.5 14.8-22.2 14.8H48.5z"/></svg>', scaletowidth=20),
				'redo': tksvg.SvgImage(data=b'<svg viewBox="0 0 512 512" fill="#D4D4D4"><path d="M463.5 224H472c13.3 0 24-10.7 24-24V72c0-9.7-5.8-18.5-14.8-22.2s-19.3-1.7-26.2 5.2L413.4 96.6c-87.6-86.5-228.7-86.2-315.8 1c-87.5 87.5-87.5 229.3 0 316.8s229.3 87.5 316.8 0c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0c-62.5 62.5-163.8 62.5-226.3 0s-62.5-163.8 0-226.3c62.2-62.2 162.7-62.5 225.3-1L327 183c-6.9 6.9-8.9 17.2-5.2 26.2s12.5 14.8 22.2 14.8H463.5z"/></svg>', scaletowidth=20),
				'settings': tksvg.SvgImage(data=b'<svg viewBox="0 0 512 512" fill="#D4D4D4"><path d="M352 320c88.4 0 160-71.6 160-160c0-15.3-2.2-30.1-6.2-44.2c-3.1-10.8-16.4-13.2-24.3-5.3l-76.8 76.8c-3 3-7.1 4.7-11.3 4.7H336c-8.8 0-16-7.2-16-16V118.6c0-4.2 1.7-8.3 4.7-11.3l76.8-76.8c7.9-7.9 5.4-21.2-5.3-24.3C382.1 2.2 367.3 0 352 0C263.6 0 192 71.6 192 160c0 19.1 3.4 37.5 9.5 54.5L19.9 396.1C7.2 408.8 0 426.1 0 444.1C0 481.6 30.4 512 67.9 512c18 0 35.3-7.2 48-19.9L297.5 310.5c17 6.2 35.4 9.5 54.5 9.5zM80 408a24 24 0 1 1 0 48 24 24 0 1 1 0-48z"/></svg>', scaletowidth=20),
			}
		)

		self.filename: Optional[str] = None

		self.popup_elem = None
		self.popup_after = None
		self.enable_popup_animation = True

		## If the stored timetable file failed one or more validation checks, use a temporary file
		if any(file_checks[:3]) or any(file_checks[-3:]):  # Check if the timetable file failed validation
			self.filename = 'tempfile.json'  # Set the filename to a temporary file
			with open(self.filename, 'w', encoding='utf-8') as template_file:  # Write template timetable data to the temporary file
				template_file.write(TIMETABLE_JSON_TEMPLATE % int(datetime.datetime.now().timestamp()))

		## If the settings file failed validation, use a template settings file
		if any(file_checks[:3]):  # If the settings file failed validation
			self.settings = DEFAULT_SETTINGS  # Use the stored settings template
			self.settings.update({'default.path': self.filename})  # Update the stored filename (Note: If the settings file fails validation, the timetable filename cannot be read and therefore will also fail validation, so the filename will never be None)
		else:  # If the settings file passed validation
			with open('settings.json', encoding='utf-8') as settingsfile:  # Load the settings JSON file to a dictionary
				self.settings = json.load(settingsfile)
			if not any(file_checks[-3:]):  # If the timetable file passed validation, set the filename to the stored path TODO: could use `if filename is None`
				self.filename = self.settings['default.path']
			else:  # Otherwise, use the temporary filename
				self.settings.update({'default.path': self.filename})

		## If the window config file failed validation, use a template
		if any(file_checks[3:6]):  # If the window config file failed validation
			self.window_settings = DEFAULT_WINDOW_SETTINGS  # Used the stored template
		else:
			with open('window_settings.json', encoding='utf-8') as winsettingsfile:  # Otherwise, load the window config JSON file to a dictionary
				self.window_settings = json.load(winsettingsfile)

		self.call('wm', 'iconphoto', str(self), self.icons['window_icon2'])  # Set the icon of the window
		self.tk.call('tk', 'scaling', self.settings['ui_scaling'])  # Update the scaling of the window
		self.protocol('WM_DELETE_WINDOW', lambda: self.close_handler())  # Add a handler for when the window is closed

		self.geometry(self.window_settings['window.geometry'])  # Set the window’s size and position
		self.state(self.window_settings['window.state'])  # Set the window’s state (fullscreen, minimised, etc.)

		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, weight=1)

		timetable_data = read_timetable(self.filename)  # Read the timetable

		## Add the top 'action bar' to the window
		self.top_bar = WindowTopbar(self, background='#000')
		self.top_bar.grid(row=0, column=0, sticky='nswe')

		## Add the timetable to the window
		self.timetable = TimeTable(self, *timetable_data)
		self.timetable.grid(row=1, column=0, sticky='nswe')

		## ============================================= Style =============================================
		## Define the ttk style
		self.style = ttk.Style()
		self.style.theme_use('default')

		self.manager = ci.CIManager(self, self.style)  # Create a custom image mapping manager
		self.manager.load_dir('icons')  # Load the images in the `icons` dictionary

		## ------------------------------------------- Combobox --------------------------------------------
		## Define the formatting of the combobox listbox area (The list of options shown when the arrow is clicked)
		self.option_add('*TCombobox*Listbox.background', '#303841')
		self.option_add('*TCombobox*Listbox.foreground', '#D8DEE9')
		self.option_add('*TCombobox*Listbox.selectBackground', '#424D59')
		self.option_add('*TCombobox*Listbox.selectForeground', '#D8DEE9')

		## Configure the style of the vertical scrollbar used in the combobox listbox area
		self.style.configure('TCombobox.Vertical.TScrollbar', background='#696F75', troughcolor='#444B53', relief='flat', troughrelief='flat', arrowcolor='#B8BBBE')

		## Set the style of the combobox widget
		self.style.configure('TCombobox', background='#424D59', fieldbackground='#2E3238', highlightthickness=1, highlightbackground='#4F565E', insertwidth=2, insertcolor='#F9AE58', borderwidth=0, relief='flat', arrowcolor='#B8BBBE', foreground='#D8DEE9', font=('Calibri', 13), padding=(2, 5, 2, 5))
		self.style.map('TCombobox', background=[('pressed', '#5E6E7F'), ('active', '#46525C'), ('disabled', '#424D59')], foreground=[('!disabled', '#D8DEE9'), ('disabled', '#BFC5D0')], fieldbackground=[('!disabled', '#2E3238'), ('disabled', '#424D59')])

		self.style.configure('Custom.TCombobox', background='#424D59', fieldbackground='#303841', highlightthickness=1, highlightbackground='#4F565E', insertwidth=2, insertcolor='#F9AE58', borderwidth=0, relief='flat', arrowcolor='#B8BBBE', foreground='#D8DEE9', font=('Calibri', 12))
		self.style.map('Custom.TCombobox', background=[('active', '#46525C'), ('disabled', '#424D59')], foreground=[('!disabled', '#D8DEE9'), ('disabled', '#BFC5D0')], fieldbackground=[('!disabled', '#303841'), ('disabled', '#424D59')])

		## ------------------------------------------- Spinbox ---------------------------------------------
		self.style.configure('Custom.TSpinbox', background='#424D59', fieldbackground='#2E3238', highlightthickness=1, highlightbackground='#4F565E', insertwidth=2, insertcolor='#F9AE58', borderwidth=0, relief='flat', arrowcolor='#B8BBBE', foreground='#D8DEE9', font=('Calibri', 13), padding=(2, 5, 2, 5), arrowsize=12)
		self.style.map('Custom.TSpinbox', background=[('pressed', '#5E6E7F'), ('active', '#46525C'), ('disabled', '#424D59')], foreground=[('!disabled', '#D8DEE9'), ('disabled', '#BFC5D0')], fieldbackground=[('!disabled', '#2E3238'), ('disabled', '#424D59')])

		## -------------------------------------------- Button ---------------------------------------------
		self.style.configure('stipple.TButton', background='#303841', foreground='#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', bordercolor='#f00', borderwidth=0, relief='flat', activeforeground='#D4D6D7', activebackground='#303841', disabledforeground='#BFC5D0', padding=(0, 0, 0, 0), shiftrelief=1, anchor='center')
		self.style.map('stipple.TButton', background=[('pressed', '#5E6E7F'), ('active', '#3B434C')], foreground=[('pressed', '#C0C5CE'), ('active', '#C0C5CE'), ('!active', '#D8DEE9'), ('disabled', '#A8AEB7')])

		self.style.configure('symbol.stipple.TButton', font=('Segoe UI Symbol', 11), padding=(2, 4, 0, 0))
		self.style.configure('text.stipple.TButton', font=('Calibri', 12))

		## Create a custom layout for an image-mapped button
		buttonlayout = self.manager.create_layout('stipple.TButton', [('Button.border', {'sticky': 'nswe', 'border': '1', 'children': [('Button.padding', {'sticky': 'nswe', 'children': [('Button.label', {'sticky': 'nswe'})]})]})])

		buttonlayout.add('Button.button', 0, 'Button.border', sticky='nswe')  # Add the button properties to the image mapping manager

		## Add the custom image mapping for the button widget background
		self.manager.map('stipple.TButton', 'Button.button', {'default': 'blank', '!disabled': 'blank', 'disabled': 'stipple'}, inherit=False)

		## -------------------------------------------- Entry ----------------------------------------------
		## Add custom image mapping for the entry field
		self.manager.map('stipple.TEntry', 'Entry.field', {'default': 'blank', '!disabled': 'blank', 'disabled': 'stipple'}, inherit=False)

		## Specify the style of the entry widget
		self.style.configure('stipple.TEntry', font=('Calibri', 13), background='#2E3238', activebackground='#2E3238', selectrelief='flat', foreground='#D8DEE9', borderwidth=0, insertbackground='#F9AE58', insertcolor='#ff0', relief='flat', padding=(2, -1, 2, -1))
		self.style.map('stipple.TEntry', background=[('disabled', '#2E3238'), ('!disabled', '#2E3238')])

		## ------------------------------------------ Scrollbar --------------------------------------------
		self.style.configure('TScrollbar', width=7, arrowcolor='#B8BBBE', background='#696F75', troughcolor='#444B53', relief='flat', troughrelief='flat')
		self.style.map('TScrollbar', background=[('active', '#858C93')])

		self.style.layout('Custom.Vertical.TScrollbar', [('Vertical.Scrollbar.trough', {'sticky': 'ns', 'children': [('Vertical.Scrollbar.thumb', {'unit': '1', 'sticky': 'nswe', 'children': [('Vertical.Scrollbar.grip', {'sticky': ''})]})]})])

	def undo(self) -> None:
		""" Call the timetable event entry widget’s undo function """
		## Todo: add undo/redo for other actions (eg: adding, deleting, and editing classes and events)
		self.timetable.event_entry.edit_undo()

	def redo(self) -> None:
		""" Call the timetable event entry widget’s redo function """
		self.timetable.event_entry.edit_redo()

	def load_timetable(self, filename: Optional[str] = None) -> None:
		"""
		Load a timetable from a JSON file

		:param filename: The path to the JSON file to load. If left blank, the program will prompt the user for a file.
		"""

		## Todo: validate timetable file (use validate_local_files function)
		if filename is None:  # If no filename is specified, prompt the user to pick a file
			filename = fd.askopenfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.filename), initialfile=self.filename, parent=self)

		if not file_exists(filename):  # If the specified file does not exist, return.
			return

		## Update the stored filenames
		self.filename = filename  # Update the current filename
		self.top_bar.filename_display.configure(text=filename)  # Update the displayed filename
		self.settings.update({'default.path': filename})  # Update the stored filename

		## Todo: Update the existing timetable object instead of creating a new one
		## Todo: Warn the user if the file is not saved

		## Create a new timetable object
		self.timetable.destroy()  # Destroy the existing timetable object
		timetable_data = read_timetable(filename)  # Read the timetable from the input file
		self.timetable = TimeTable(self, *timetable_data)  # Create a new timetable object
		self.timetable.grid(row=1, column=0, sticky='nswe')  # Display the timetable object

		## Update the window size
		self.update_idletasks()  # Wait for the running tasks to complete (i.e.: until the new UI has loaded)
		## Update the minimum size of the window to fit the timetable
		self.wm_minsize(window.timetable.display_frame.winfo_width() - 47, window.timetable.display_frame.winfo_height() + window.top_bar.winfo_height() - 34)

	def export_timetable(self, mode: Literal['xls', 'csv', 'pdf']) -> None:
		"""
		Export the current timetable as a csv/xls/pdf file

		:param mode: The file type to export as
		"""

		match mode:
			case 'xls':
				## todo: implement xls and csv conversion
				mb.showinfo('Not Implemented', 'This feature has not been implemented yet.')
			case 'csv':
				mb.showinfo('Not Implemented', 'This feature has not been implemented yet.')
			case 'pdf':
				ExportAsPDFMenu(self)  # Show the 'export to pdf' UI

	def undo_all(self) -> None:
		""" Undo all unsaved changes to the current file """
		## Todo: implement (load the saved file)
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.')

	def show_about(self) -> None:
		""" Show information about the program """

		## Create a new window to show the about information
		tl = tk.Toplevel(self, background='#303841')
		tl.attributes('-topmost', True)  # Set the window as the topmost in the UI
		tl.resizable(False, False)  # Disable resizing
		tl.title('About')  # Set the window title
		self.call('wm', 'iconphoto', str(tl), self.icons['window_icon2'])  # Set the window icon

		## Configure the grid
		tl.columnconfigure(0, weight=1)
		tl.rowconfigure(0, weight=1)

		## Add a label displaying the about information
		tk.Label(tl, text=AboutInfo, background='#303841', foreground='#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Jetbrains Mono Light', 13), anchor='w', justify='left', image=self.pixel, compound='center').grid(sticky='nswe')

	def show_help(self) -> None:
		""" Not implemented. Show the help menu """
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.\n\n(No help is coming)')

	def report_bug(self) -> None:
		""" Not implemented. Show the 'report bug' UI """
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.\n\n(My code is perfect and any issues are 100% your own fault)')

	def report_feature(self) -> None:
		""" Not implemented. Show the 'request feature' UI """
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.')

	def show_settings(self) -> None:
		""" Show the settings UI """
		SettingsWindow(self, background='#303841')

	@staticmethod
	def get_start_week(week: Optional[int] = None, allow_cancel: bool = False) -> int | None:
		"""
		Get the timestamp of the starting week.
		The output of this function is used to calculate the current week number.

		:param week: The current week number. Leave unspecified to prompt the user to enter a week number.
		:param allow_cancel: Weather to allow the user to cancel updating the stating week timestamp.
		:return: The calculated timestamp for the starting week of the term
		"""

		## Get the week number
		if week is None:
			week = sd.askinteger('Setup', 'Enter the current week:', initialvalue=1, minvalue=1, maxvalue=11)  # Prompt the user for a week number
			if week is None:  # If the user pressed cancel
				if allow_cancel:  # Return if cancelling is allowed, otherwise set the week number to 0
					return
				week = 0
			else:  # Otherwise, remove 1 from the week. The week number is treated as an index starting from 0, but is displayed as a number starting at 1, so this is necessary.
				week -= 1

		current_time = datetime.datetime.now()  # Get the current time

		## Remove subtract the current seconds since midnight from the current time
		start_timestamp = int(current_time.timestamp()) - current_time.hour * 3600 - current_time.minute * 60 - current_time.second

		## Remove days since term began
		start_timestamp -= (week * 7 + current_time.weekday()) * 86400

		return start_timestamp  # Return the result

	def new_timetable(self) -> None:
		""" Create a new timetable """

		## Get the filename
		filename = fd.asksaveasfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.filename), confirmoverwrite=True, initialfile=self.filename, parent=self)
		if not filename:  # If the user pressed cancel, return.
			return

		## Get the timestamp of the starting week and save a copy of the template timetable JSON
		with open(filename, 'w', encoding='utf-8') as file:
			file.writelines(TIMETABLE_JSON_TEMPLATE % self.get_start_week())

		self.load_timetable(filename)  # Load the newly created timetable JSON

	def close_handler(self) -> None:
		""" Handler for closing the window. Called when the window is closed. """

		## Attempt to save the timetable
		try:
			if not self.timetable.check_saved(self.timetable.get_json()):  # If the timetable has unsaved changes, prompt the user to save
				ans = mb.askyesnocancel('Unsaved Data', 'Do you want to save your changes to this timetable?')
				if ans is None:  # If the user presses 'cancel', return.
					return
				elif ans:  # If the user presses 'yes', save the timetable and continue.
					self.timetable.save_timetable()

			## Get the current window state, position and size and save them to a JSON file
			json_object = json.dumps({'window.geometry': self.winfo_geometry(), 'window.state': self.state()}, indent=4, separators=(', ', ': '))
			with open('window_settings.json', 'w', encoding='utf-8') as file:
				file.write(json_object)

			## Save the current settings to the settings file
			json_object = json.dumps(self.settings, indent=4, separators=(', ', ': '))
			with open('settings.json', 'w', encoding='utf-8') as file:
				file.write(json_object)

		except Exception:  # Catch all exceptions with a broad exception clause, otherwise the program may get 'stuck open'
			## Prompt the user that the program failed to save
			mb.showerror('Failed to Save', f'An error occurred while attempting to close.\nAs a result, some data may be unsaved.\n\n{sys.exc_info()[1]}\n{sys.exc_info()[2]}\n\n{format_exc()}')

		self.destroy()  # Destroy the window

	def display_popup(self, text: str, ms: int = 2000) -> None:
		"""
		Display a popup at the bottom of the screen.

		:param text: The text to display in the popup
		:param ms: The duration that the popup is displayed for in milliseconds
		"""

		## Destroy any existing popups
		if self.popup_elem is not None:
			self.popup_elem.destroy()
			self.after_cancel(self.popup_after)

		## Create an animated frame element
		self.popup_elem = anim.AnimatedFrame(self, background='#3B434C')
		self.popup_elem.columnconfigure(0, weight=1)

		## Add a label and close button to the frame
		tk.Label(self.popup_elem, text=text, relief='flat', font=('Calibri', 11), background='#303841', foreground='#D8DEE9', image=self.pixel, compound='center', height=15, anchor='w').grid(row=0, column=0, sticky='nswe', padx=1, pady=1)
		tk.Button(self.popup_elem, text='', relief='flat', font=('Segoe UI Symbol', 9), background='#4F565E', foreground='#D8DEE9', image=self.pixel, compound='center', width=15, height=15, command=lambda: self.remove_popup(), activebackground='#303841', activeforeground='#D4D6D7', borderwidth=0).grid(row=0, column=1, sticky='nswe', padx=(0, 1), pady=1)

		if self.enable_popup_animation:  # If animation is enabled
			## Animate the popup moving up from the bottom of the window
			self.popup_elem.configure_animation(y_func=anim.ANIM_RECIPROCAL, delay=5, step=0.05, end_command=lambda: self.after(ms, lambda: self.remove_popup()))
			self.popup_elem.animate_place((self.winfo_width() // 2 - 100, self.winfo_height() + 5), (self.winfo_width() // 2 - 100, self.winfo_height() - 35), 0)
		else:  # Otherwise, place the popup in the window
			self.popup_elem.place(x=self.winfo_width() // 2 - 100, y=self.winfo_height() - 35, width=200)
			self.popup_after = self.after(ms, lambda: self.remove_popup())  # Set the popup to close after the specified time

	def remove_popup(self) -> None:
		""" Remove the current popup """

		if self.enable_popup_animation:  # If animation is enabled
			## Animate the popup moving off-screen
			self.popup_elem.configure_animation(end_command=None)
			self.popup_elem.animate_place((self.winfo_width() // 2 - 100, self.winfo_height() - 35), (self.winfo_width() // 2 - 100, self.winfo_height() + 5), 0)

		self.popup_elem.destroy()  # Destroy the popup frame
		self.popup_elem = None  # Reset the popup variable
		self.after_cancel(self.popup_after)  # Cancel the automatic call to close the popup
		self.popup_after = None  # Reset the after variable


## Define a template JSON file for a timetable
TIMETABLE_JSON_TEMPLATE = '''{
    "classes": ["Session0", "<class-1>", "<class-2>", "<class-3>", "<class-4>", "<class-5>", "<class-6>", "<class-7>", "<class-8>", "Homework"],
    "teachers": ["None", "", "", "", "", "", "", "", "", "None"],
    "rooms": ["None", "", "", "", "", "", "", "", "", "None"],
    "timetable": [
        [0, 1, 2, 3, 4, 5, 9],
        [0, 1, 2, 3, 4, 5, 9],
        [0, 1, 2, 3, 4, 5, 9],
        [0, 1, 2, 3, 4, 5, 9],
        [0, 1, 2, 3, 4, 5, 9]
    ],
    "events": [],
    "sessions": [
        ["0", true, "08:20"],
        ["Before School", false, "08:30"],
        ["1", true, "09:30"],
        ["2", true, "10:45"],
        ["Recess", false, "11:15"],
        ["3", true, "12:15"],
        ["4", true, "13:15"],
        ["Lunch", false, "13:45"],
        ["5", true, "14:45"],
        ["After School", false, "15:00"],
        ["6", true, "-1"]
    ],
    "day_start": "7:15",
    "start_date_timestamp": %s
}'''


def read_timetable(path: str, encoding: str = 'utf-8') -> tuple[list[str], list[str], list[str], Any, list[dict], str, list[list[str, bool, str]], int] | None:
	"""
	Read a timetable from a JSON file

	:param path: The path to read.
	:param encoding: The encoding of the target file.
	:return: The data read from the timetable file to be passed directly to a timetable object.
	"""

	## Add the JSON extension to the target path
	if not path.endswith('.json'):
		path += '.json'

	## If the target file does not exist, create a new file from the template timetable JSON
	if not file_exists(path):
		with open(path, 'w', encoding=encoding) as eventfile:
			eventfile.write(TIMETABLE_JSON_TEMPLATE % int(datetime.datetime.now().timestamp()))

	try:  # Try to read the target file
		with open(path, encoding=encoding) as readfile:
			data = json.load(readfile)
	except json.decoder.JSONDecodeError:  # If the target file has invalid JSON syntax, prompt the user that the file could not be read
		mb.showwarning('JSON Decode Error', f'Could not load "{path}".\nReason: JSON Decode Error\n\n{sys.exc_info()[1]}')
		return

	## Otherwise, return the data from the json file. Todo: return the dictionary rather than the value of each key
	return data['classes'], data['teachers'], data['rooms'], data['timetable'], data['events'], data['day_start'], data['sessions'], data['start_date_timestamp']


def increment_numbering(indent: str) -> str:
	"""
	Increment the numbering portion of the input indent string.

	:param indent: The indent string to increment.
	:return: The next indent string in the sequence.
	"""

	location = re.match('[^\t .):]*', indent).span()  # Get the location of the numbering in the input string
	numbering = indent.strip('\t .):')  # Remove non-numbering characters from the input string to get the value of the numbering

	if numbering:  # If there is numbering or lettering in the input indent
		if re.match('[0-9]*', numbering).span() == (0, len(numbering)):  # If the numbering in the indent string is numeric
			numbering = list(str(int(numbering) + 1))  # Add 1 to the numbering and convert the number into a list of characters
			indent = list(indent)  # Convert the indent to a list of characters
			indent[location[0]:location[1]] = numbering  # Insert the numbering string into the indent string at the position of the old numbering string
			indent = ''.join(indent)  # Join the characters of the indent into a string

		elif re.match('[a-zA-Z]*', numbering).span() == (0, len(numbering)):  # If the numbering in the indent string is alphabetic
			numbering = [ord(i.lower()) - ord('a') for i in numbering[::-1]]  # Convert the lettering string to a list of numbers in reverse order

			add = True  # Holds weather or not the number at the current index should be incremented
			idx = 0  # Stores the current index

			## todo: could do `for i in range(numbering.index(25))`

			while add:  # Repeat while a value remains to be incremented
				if idx >= len(numbering):  # If the current index is greater than the width of the lettering string
					numbering.append(0)  # Add an 'a' to the end of the list (start of the string)
					add = False  # Do not increment the next index
				else:  # If the current index is within the current lettering string
					if numbering[idx] == 25:  # If the letter to be incremented is 'z'
						numbering[idx] = 0  # Reset the value of the character
						idx += 1  # Increment the current index
					else:  # If the letter to be incremented is not 'z'
						numbering[idx] += 1  # Increment the letter at the current index
						add = False  # Do not increment the next number

			numbering = [chr(i + ord('a')) for i in numbering[::-1]]  # Convert the characters in the list back to alphabetic strings
			indent = list(indent)  # Convert the indent to a list of characters
			indent[location[0]:location[1]] = numbering  # Insert the lettering string into the indent string at the position of the old lettering string
			indent = ''.join(indent)  # Join the characters of the indent into a string

	return indent  # Return the result


def load_images(data: list[tuple[str, str, int]], linecolour: str = '#D4D4D4', highlightcolour: str = '#6FB0DB') -> dict:
	"""
	Load a list of SVG files, configure the line and highlight colour, scale to a specified size and add each image to a dictionary with a specified key.

	:param data: A list containing the images to load. This parameter should be in the format [path to image, image key, scale width].
	:param linecolour: The colour to format the linecolour field in the loaded SVG files.
	:param highlightcolour: The colour to format the highlightcolour field in the loaded SVG files.
	:return: A dictionary of tkinter svg images loaded from files with their specified keys.
	"""

	images = dict()  # Declare a dictionary to hold the images

	for file, name, width in data:  # Iterate through the data list
		if file_exists(file):  # If the target file exists
			with open(file) as svg_file:  # Open and read the target file
				svg_data = svg_file.readlines()
				## Format the colour fields in the SVG data and create a tkinter-compatible image using said data.
				images.update({name: tksvg.SvgImage(data=''.join(svg_data).format(linecolour=linecolour, highlightcolour=highlightcolour), scaletowidth=width)})
		else:  # If the target file does not exist, set the value for the specified key to be Null
			images.update({name: None})

	return images  # Return the dictionary of images


def find_data_file() -> str:
	"""
	Find the path of the application depending on weather the application is frozen (executable) or not.

	From: https://stackoverflow.com/a/56748839
	"""

	if getattr(sys, 'frozen', False):
		# The application is frozen
		return os.path.dirname(os.path.realpath(sys.executable))
	else:
		# The application is not frozen
		return os.path.dirname(os.path.realpath(__file__))


class SettingsWindow(tk.Toplevel):
	"""
	Displays, and allows editing of, the settings dictionary for the window and its associated JSON file.

	:param root: The root window widget
	"""

	def __init__(self, root, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		self.root: Window = root

		self.attributes('-topmost', True)  # Set the window to be the topmost
		self.grab_set()  # Direct all events to this window
		self.title('Settings')  # Set the window title
		self.root.call('wm', 'iconphoto', str(self), self.root.icons['window_icon2'])  # Set the window icon

		## Set the position of the settings window to be roughly in the centre of the main window.
		self.geometry(f'+{self.root.winfo_x() + int(self.root.winfo_width() // 3)}+{self.root.winfo_y() + int(self.root.winfo_height() // 3)}')

		self.columnconfigure(0, weight=1)

		## Create a string variable for each of the editable options in the settings dictionary
		self.default_path = tk.StringVar(self, root.settings['default.path'])
		self.editor_font = tk.StringVar(self, root.settings['editor.font'][0])
		self.editor_size = tk.IntVar(self, root.settings['editor.font'][1])
		self.editor_style = tk.StringVar(self, root.settings['editor.font'][2].title())
		self.dpi_awareness = tk.StringVar(self, ['DPI Unaware', 'System DPI Aware', 'Per Monitor DPI Aware'][root.settings['dpi_awareness']])
		self.ui_scaling = tk.StringVar(self, str(root.settings['ui_scaling']))

		## Define default formatting for UI elements
		buttonconfig = {'background': '#3B434C', 'foreground': '#D8DEE9', 'activebackground': '#303841', 'mouseoverbackground': '#303841', 'borderwidth': 0, 'font': ('Calibri', 12), 'image': self.root.pixel, 'compound': 'center', 'highlightthickness': 1, 'highlightbackground': '#4F565E'}
		labelconfig = {'background': '#303841', 'borderwidth': 0, 'anchor': 'w', 'justify': 'left', 'image': self.root.pixel, 'compound': 'center'}

		## ======================================== User Interface ========================================

		## ---------------------------------------- Filepath Input ----------------------------------------
		frame = tk.Frame(self, background='#303841', highlightthickness=1, highlightbackground='#4F565E')
		frame.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
		frame.columnconfigure(0, weight=1)

		tk.Label(frame, text='Default Path', foreground='#D8DEE9', font=('Calibri', 13, 'bold'), **labelconfig).grid(row=0, column=0, sticky='nswe', padx=1, pady=(1, 0), columns=2)
		tk.Label(frame, text='Specifies the path to load when the program is opened.', foreground='#777', font=('Calibri', 10, 'italic'), **labelconfig).grid(row=1, column=0, sticky='nswe', padx=1, pady=(0, 0), columns=2)
		self.path_entry = ttk.Entry(frame, style='stipple.TEntry', textvariable=self.default_path)
		self.path_entry.grid(row=2, column=0, sticky='nswe', padx=1, pady=(0, 1))

		MouseoverButton(frame, text='Browse', command=lambda: self.browse_timetables(), **buttonconfig).grid(row=2, column=1, sticky='nswe', padx=(0, 1), pady=(0, 1))

		## ----------------------------------------- Editor Font ------------------------------------------
		frame = tk.Frame(self, background='#303841', highlightthickness=1, highlightbackground='#4F565E')
		frame.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
		frame.columnconfigure((1, 3), weight=1)

		tk.Label(frame, text='Editor Font', foreground='#D8DEE9', font=('Calibri', 13, 'bold'), **labelconfig).grid(row=0, column=0, sticky='nswe', padx=1, pady=(1, 0), columns=2)
		tk.Label(frame, text='Specifies the font to use for the event text.', foreground='#777', font=('Calibri', 10, 'italic'), **labelconfig).grid(row=1, column=0, sticky='nswe', padx=1, pady=(0, 0), columns=2)
		tk.Label(frame, text='Family', background='#3B434C', width=50, foreground='#D8DEE9', borderwidth=0, font=('Calibri', 10, 'bold'), image=self.root.pixel, compound='center').grid(row=2, column=0, sticky='nswe', padx=(1, 1), pady=(0, 1))
		self.font_entry = CustomComboBox(frame, validatecommand=lambda v: self.validate_font(), validate='focusout', style='TCombobox', textvariable=self.editor_font, values=tkfont.families())
		self.font_entry.configure(invalidcommand=lambda: self.invalid_input(self.font_entry, 'Font not found.'))
		self.font_entry.grid(row=2, column=1, sticky='nswe', padx=(0, 1), pady=(0, 1), columns=3)

		tk.Label(frame, text='Size', background='#3B434C', width=50, foreground='#D8DEE9', borderwidth=0, font=('Calibri', 10, 'bold'), image=self.root.pixel, compound='center').grid(row=3, column=0, sticky='nswe', padx=(1, 1), pady=(0, 1))
		self.size_entry = ttk.Spinbox(frame, validatecommand=lambda v: self.validate_size(), validate='focusout', style='Custom.TSpinbox', textvariable=self.editor_size, from_=1, to=144)
		self.size_entry.configure(invalidcommand=lambda: self.invalid_input(self.size_entry, 'Size must be an integer between 1 and 144.'))
		self.size_entry.grid(row=3, column=1, sticky='nswe', padx=(0, 1), pady=(0, 1))

		tk.Label(frame, text='Style', background='#3B434C', width=50, foreground='#D8DEE9', borderwidth=0, font=('Calibri', 10, 'bold'), image=self.root.pixel, compound='center').grid(row=3, column=2, sticky='nswe', padx=(1, 1), pady=(0, 1))
		self.style_entry = CustomComboBox(frame, style='TCombobox', textvariable=self.editor_style, values=['Normal', 'Bold', 'Italic', 'Bold Italic'], state='readonly')
		self.style_entry.grid(row=3, column=3, sticky='nswe', padx=(0, 1), pady=(0, 1))

		## ------------------------------------------ DPI Scaling -----------------------------------------
		frame = tk.Frame(self, background='#303841', highlightthickness=1, highlightbackground='#4F565E')
		frame.grid(row=2, column=0, padx=5, pady=5, sticky='nswe')
		frame.columnconfigure(0, weight=1)

		tk.Label(frame, text='DPI Awareness', foreground='#D8DEE9', font=('Calibri', 13, 'bold'), **labelconfig).grid(row=0, column=0, sticky='nswe', padx=1, pady=(1, 0), columns=2)
		tk.Label(frame, text='DPI awareness for the application.', foreground='#777', font=('Calibri', 10, 'italic'), **labelconfig).grid(row=1, column=0, sticky='nswe', padx=1, pady=(0, 0), columns=2)
		self.resolution_entry = CustomComboBox(frame, style='TCombobox', textvariable=self.dpi_awareness, values=['DPI Unaware', 'System DPI Aware', 'Per Monitor DPI Aware'], state='readonly')
		self.resolution_entry.grid(row=2, column=0, sticky='nswe', padx=1, pady=(0, 1), columns=2)

		## ------------------------------------------ UI Scaling ------------------------------------------
		frame = tk.Frame(self, background='#303841', highlightthickness=1, highlightbackground='#4F565E')
		frame.grid(row=3, column=0, padx=5, pady=5, sticky='nswe')
		frame.columnconfigure(0, weight=1)

		tk.Label(frame, text='UI Scaling', foreground='#D8DEE9', font=('Calibri', 13, 'bold'), **labelconfig).grid(row=0, column=0, sticky='nswe', padx=1, pady=(1, 0), columns=2)
		tk.Label(frame, text='Scaling for the size of the application UI.', foreground='#777', font=('Calibri', 10, 'italic'), **labelconfig).grid(row=1, column=0, sticky='nswe', padx=1, pady=(0, 0), columns=2)
		self.scale_entry = ttk.Entry(frame, validatecommand=lambda v: self.validate_ui_scale(), validate='focusout', style='stipple.TEntry', textvariable=self.ui_scaling)
		self.scale_entry.configure(invalidcommand=lambda: self.invalid_input(self.scale_entry, 'UI scale must be a number between 0.2 and 10.0'))
		self.scale_entry.grid(row=2, column=0, sticky='nswe', padx=1, pady=(0, 1), columns=2)

		## ----------------------------------- Ok/Cancel/Apply Buttons ------------------------------------
		frame = tk.Frame(self, background='#303841', height=5)
		frame.grid(row=4, column=0, sticky='nse', padx=5, pady=5)

		MouseoverButton(frame, text='OK', command=lambda: self.ok_pressed(), width=60, **buttonconfig).grid(row=0, column=1, sticky='nswe', padx=(1, 1), pady=(1, 1))
		MouseoverButton(frame, text='Cancel', command=lambda: self.destroy(), width=60, **buttonconfig).grid(row=0, column=2, sticky='nswe', padx=(0, 1), pady=(1, 1))
		MouseoverButton(frame, text='Apply', command=lambda: self.apply(), width=60, **buttonconfig).grid(row=0, column=3, sticky='nswe', padx=(0, 0), pady=(1, 1))

	@staticmethod
	def invalid_input(element: ttk.Entry, text: str) -> None:
		"""
		This function is called when an input into an entry does not pass validation.
		It sets the cursor back into the entry and displays a message to the user.

		:param element: The entry to set the cursor into
		:param text: The message to display to the user
		"""

		cursor_pos = element.index(tk.INSERT)
		mb.showinfo('Invalid Input', text)
		element.focus()
		element.icursor(cursor_pos)

	def validate_font(self) -> bool:
		""" Check if the font in the editor font entry is in the list of detected font families """
		return self.editor_font.get().title() in tkfont.families()

	def validate_size(self) -> bool:
		""" Check that the font size is between 1 and 144 pts """
		return 1 <= int(self.editor_size.get()) <= 144

	def validate_ui_scale(self) -> bool:
		""" Check that the UI scale is an integer between 0.5 and 5 """

		if not self.ui_scaling.get().isnumeric():
			return False
		else:
			return 0.5 <= int(self.ui_scaling.get()) <= 5

	def browse_timetables(self) -> None:
		""" Prompt the user to select a timetable file and update the default path field with their response """
		filename = fd.askopenfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.root.filename), initialfile=self.root.filename, parent=self)
		if filename:
			self.default_path.set(filename)

	def get_settings(self) -> dict:
		""" Get the current settings as a dictionary """

		return {
			'default.path': self.default_path.get(),
			'editor.font': [self.editor_font.get().title(), int(self.editor_size.get()), self.editor_style.get().lower()],
			'dpi_awareness': ['DPI Unaware', 'System DPI Aware', 'Per Monitor DPI Aware'].index(self.ui_scaling.get()),
			'ui_scaling': float(self.ui_scaling.get())
		}

	def ok_pressed(self) -> None:
		""" When the 'OK' button is pressed, apply the changes and close the window """
		self.apply()
		self.destroy()

	def apply(self) -> None:
		""" Update the settings dictionary and settings file with the updated settings data. """
		settings_dict = self.get_settings()  # Get the updated settings data

		if settings_dict != self.root.settings:  # Check if the current settings data is different to the saved settings data
			if settings_dict['editor.font'] != self.root.settings['editor.font']:  # If the font has been changed, update the font of the timetable event text entry
				self.root.timetable.entry_font.configure(family=self.editor_font.get(), size=self.editor_size.get(), slant='italic' if 'italic' in self.editor_style.get().lower() else 'roman', weight='bold' if 'bold' in self.editor_style.get().lower() else 'normal')

			## Update the UI scaling if it has been changed
			if settings_dict['ui_scaling'] != self.root.settings['ui_scaling']:
				self.root.tk.call('tk', 'scaling', float(self.ui_scaling.get()))

			## Update the DPI awareness if it has been changed
			if settings_dict['dpi_awareness'] != self.root.settings['dpi_awareness']:
				ctypes.windll.shcore.SetProcessDpiAwareness(int(self.dpi_awareness.get()))

			self.root.settings.update(settings_dict)  # Update the settings dictionary with the new values

			## Write the updated settings dictionary to disk in JSON format
			with open('settings.json', 'w', encoding='utf-8') as file:
				json_object = json.dumps(settings_dict, indent=4, separators=(', ', ': '))
				file.write(json_object)


## Declare the default settings dictionary
DEFAULT_SETTINGS = {
	"default.path": find_data_file() + "/timetable.json",
	"editor.font": ["Calibri", 10, ""],
	"dpi_awareness": 2,
	"ui_scaling": 1.3
}

## Declare the default window config dictionary
DEFAULT_WINDOW_SETTINGS = {
	"window.geometry": "1198x744+341+69",
	"window.state": "normal"
}

## Declare a list of the required image files
ImageFiles = ['blank.png', 'stipple.png', 'slider-thumb-large-active.png', 'slider-thumb-large.png', 'dotpoints.svg', 'numbering3.svg', 'lettering.svg', 'calendar.svg', 'saveas.svg', 'savecopy.svg', 'new_timetable.svg', 'import.svg', 'export.svg', 'pdf_icon.svg', 'xls_icon.svg', 'csv_icon.svg', 'help_icon.svg', 'about_icon.svg']


def validate_local_files() -> list[bool | str]:
	"""
	Check the existence and validity of the program’s required files.

	:return:
		The state of the following reasons for failing validation:

		1. The settings file does not exist
		2. The settings file has invalid JSON syntax
		3. The settings file is missing a key field

		4. The window settings file does not exist
		5. The window settings file has invalid JSON syntax
		6. The window settings file is missing a key field

		7. The 'icons' dictionary does not exist
		8. The 'icons' dictionary is missing a file

		9. The timetable file does not exist
		10. The timetable file has invalid JSON syntax
		11. The timetable file is missing a key field
	"""

	checks = [not file_exists('settings.json')]  # Check if the settings file exists

	if not checks[-1]:  # If the settings file exists, try to read it
		try:
			with open('settings.json', encoding='utf-8') as file:
				settings = json.load(file)

			checks.extend([False, set(settings.keys()) != set(DEFAULT_SETTINGS.keys())])  # Add false to the validation check list, since the file did not fail to load. Additionally, add the result of checking if the keys of the read settings file are the same as the keys of the template settings file.
		except json.decoder.JSONDecodeError:  # If the file has invalid JSON syntax, add the exception information to the validation check list
			checks.extend([str(sys.exc_info()[1]), False])

	else:
		checks.extend([False, False])  # Mark the settings file JSON syntax and keys as valid

	checks.append(not file_exists('window_settings.json'))  # Check if the window settings file exists

	if not checks[-1]:  # If the window settings file exists, try to read it
		try:
			with open('window_settings.json', encoding='utf-8') as file:
				window_settings = json.load(file)

			checks.extend([False, set(window_settings.keys()) != set(DEFAULT_WINDOW_SETTINGS.keys())])  # Mark the window settings JSON syntax as valid and add the result of checking if the keys of the read window settings file are the same as the keys of the template window settings file.

		except json.decoder.JSONDecodeError:  # If the file has invalid JSON syntax, add the exception information to the validation check list
			checks.extend([str(sys.exc_info()[1]), False])
	else:
		checks.extend([False, False])  # Mark the window settings file JSON syntax and keys as valid

	checks.append(not os.path.exists('icons'))  # Check if the `icons` directory exists
	checks.append(bool(set(ImageFiles) - set(os.listdir('icons'))))  # Check that all of the necessary files are in the icons dictionary. Todo: this may cause performance issues when there are lots of files

	if all(checks[:3]):  # If the settings file if valid
		if file_exists(settings['default.path']):  # Check if the default timetable file exists
			try:  # Attempt to read the timetable file
				with open(settings['default.path'], encoding='utf-8') as file:
					tt_data = json.load(file)

				## Check if the timetable file’s keys are different than expected
				keys_invalid = set(tt_data.keys()) != {'classes', 'teachers', 'rooms', 'timetable', 'events', 'sessions', 'day_start', 'start_date_timestamp'}
				checks.extend([False, False, settings['default.path'] if keys_invalid else False])  # If the timetable file’s keys are different than expected, add the timetable’s filename to the path. Also, mark the previous two checks as valid.
			except json.decoder.JSONDecodeError:  # If the file has invalid JSON syntax, add the exception information and the timetable filename to the validation check list
				checks.extend([False, [settings['default.path'], str(sys.exc_info()[1])], False])
		else:  # If the timetable file does not exist, add the path to the validation check list
			checks.extend([settings['default.path'], False, False])
	else:
		checks.extend([False, False, False])

	return checks  # Return the result of all of the validation checks


file_val = validate_local_files()  # Validate the existence and contents of the local files.

## Todo: add runtime to about

## Create the 'About' string
AboutInfo = f'Timetable Version {VERSION}\n\n{{spacer}}\nProgram Name  : Timetable.py\nAuthor        : Connor Bateman\nVersion       : v2.21.1\nRevision Date : 23-05-2024 11:00\nDependencies  : null\n{{pyheading}}\nVersion        : {platform.python_version()}\nRevision       : {platform.python_revision()}\nCompiler       : {platform.python_compiler()}\nImplementation : {platform.python_implementation()}\n\n{{exheading}}\nBase         : '

## Add the system platform to the about string
if sys.platform == 'win32':
	AboutInfo += 'Win32GUI'
elif sys.platform == 'win64':
	AboutInfo += 'Win64GUI'
else:
	AboutInfo += 'None'

AboutInfo += f'\nPath         : {find_data_file()}\nProduct Code : {None}\nUpgrade Code : {None}\n'

## Get the maximum line length of the about string
about_width = max(map(len, AboutInfo.split('\n')))

## Add and headers justified using the width to the about string
AboutInfo = AboutInfo.format(spacer='=' * about_width, pyheading=' Python '.center(about_width, '-'), exheading=' Executable '.center(about_width, '-'))

AboutInfo += '=' * about_width

## End About String

## If the window settings file does not exist, create a new one using a template.
if file_val[3]:
	JsonObject = json.dumps(DEFAULT_WINDOW_SETTINGS, indent=4, separators=(', ', ': '))
	with open('window_settings.json', 'w', encoding='utf-8') as File:
		File.write(JsonObject)

window = Window(file_val)  # Create the main window

## Display a warning if using the wrong operating system, otherwise, set DPI awareness
if platform.system() == 'Windows':
	ctypes.windll.shcore.SetProcessDpiAwareness(window.settings['dpi_awareness'])

if file_exists('first_time_setup.txt') and getattr(sys, 'frozen', True):  # Check if this is the first time the program is being run as an executable
	os.remove('first_time_setup.txt')  # Remove the file marking the first time setup
	if platform.system() != 'Windows':  # Warn the user if the program is running on an unsupported operating system
		mb.showwarning('Unsupported Operating System', f'Your operating system is {platform.system()}, however this\nprogram was developed for Windows.\n\nRunning this program on another system may cause unintended behavior.')

else:  # Otherwise, show warnings related to file validation
	if file_val[0]:
		mb.showwarning('File not Found', f'Could not find "settings.json" in "{find_data_file()}"\nLoading default settings instead.')
	if file_val[1]:
		mb.showwarning('JSON Decode Error', f'Could not load "settings.json".\nReason: JSON Decode Error\n\nLoading default settings instead.\n\nException Info:\n{file_val[1]}')
	if file_val[2]:
		mb.showwarning('Index Error', 'One or more field(s) are missing from "settings.json".\n\nLoading default settings instead.')
	if file_val[3]:
		mb.showwarning('File not Found', f'Could not find "window_settings.json" in "{find_data_file()}"')
	if file_val[4]:
		mb.showwarning('JSON Decode Error', f'Could not load "window_settings.json".\nReason: JSON Decode Error\n\nException Info:\n{file_val[4]}')
	if file_val[5]:
		mb.showwarning('Index Error', 'One or more field(s) are missing from "window_settings.json".')
	if file_val[6]:
		mb.showwarning('Missing Directory', f'The directory "icons" could not be found in {find_data_file()}')
	if file_val[7]:
		mb.showwarning('File not Found', f'One or more file(s) are missing from "icons/"')
	if file_val[8]:
		mb.showwarning('File not Found', f'Could not find the file {file_val[8]}')
	if file_val[9]:
		mb.showwarning('JSON Decode Error', f'Could not load "{file_val[9][0]}".\nReason: JSON Decode Error\n\nException Info:\n{file_val[9][1]}')
	if file_val[10]:
		mb.showwarning('Index Error', f'One or more field(s) are missing from "{file_val[10]}".')

ProgramClosed = False

## If the existing timetable file is missing, invalid, or otherwise can't be read, create a new timetable file.
if any(file_val[:3]) or any(file_val[-3:]):  # Check the validation of the settings file and timetable file.
	## Prompt the user for a filename for the new timetable file
	Filename = fd.asksaveasfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=find_data_file(), initialfile='new_timetable.json', confirmoverwrite=True, parent=window, title='Create new timetable')

	if Filename == "":  # If the user does not pick a filename, end the program since a timetable file is required for the program to run. TODO: check behavior when the program is run without timetable
		ProgramClosed = True
	else:
		## Update the stored filename
		window.filename = Filename
		window.top_bar.filename_display.configure(text=Filename)

		## Get the timestamp for the starting week of the timetable, allowing the user to cancel, but closing the window if they do. This gives the user an option to go back if they previously picked a wrong file.
		start_time = window.get_start_week(allow_cancel=True)
		if start_time is None:
			ProgramClosed = True
		else:
			## Otherwise, update the settings file with the new start time and create a new timetable with the retrieved starting week
			window.settings.update({'default.path': window.filename})
			if not file_exists('settings.json'):
				JsonObject = json.dumps(window.settings, indent=4, separators=(', ', ': '))
				with open('settings.json', 'w', encoding='utf-8') as File:
					File.write(JsonObject)

			with open(Filename, 'w', encoding='utf-8') as File:
				File.writelines(TIMETABLE_JSON_TEMPLATE % start_time)

			TimetableData = read_timetable(Filename)  # Get the data from the newly created filename
			if TimetableData is not None:  # If the timetable file is read correctly
				if window.timetable is not None:  # Remove the existing timetable
					window.timetable.destroy()

				## Create a new timetable
				window.timetable = TimeTable(window, *TimetableData)
				window.timetable.grid(row=1, column=0, sticky='nswe')
			else:  # If, for whatever reason, there is an error reading the timetable file, show an error message and close the window.
				mb.showwarning('Failed to Load', f'Failed to read {Filename}')
				ProgramClosed = True

if not ProgramClosed:  # Check that the window hasn't been destroyed by the code above
	del ProgramClosed
	window.update_idletasks()  # Wait for the background tasks to complete
	## Update the minimum size of the window to fit the timetable
	Size = (window.timetable.display_frame.winfo_width() - 47, window.timetable.display_frame.winfo_height() + window.top_bar.winfo_height() - 34)
	window.wm_minsize(*Size)
else:  # Otherwise, close the window and exit the program.
	window.destroy()
	sys.exit(0)

window.mainloop()
