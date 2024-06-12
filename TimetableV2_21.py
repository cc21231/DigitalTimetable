"""
=========================================
Program Name  : Timetable.py
Author        : Connor Bateman
Version       : v2.21.4
Revision Date : 05-06-2024 13:20
Dependencies  : null
=========================================
"""
import webbrowser

VERSION = '2.21.4'
import re
import sys
from traceback import format_exc
import idlelib.colorizer as ic
import idlelib.percolator as ip
import configurable_image_widgets18 as ci
from tkinter import messagebox as mb
from tkinter import filedialog as fd
from typing import Literal, Optional, Any
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
from toolsV1 import *
from tkinter import font as tkfont


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

		if self.target is not None:
			if orient == 'vertical':
				self.bind('<MouseWheel>', lambda e: self.scroll_y)
			else:
				self.bind('<MouseWheel>', lambda e: self.scroll_x)

	def scroll_x(self, e: tk.Event) -> None:
		""" Scroll on the x-axis """
		self.target.xview_scroll(int(-1 * (e.delta / 120)), 'units')

	def scroll_y(self, e: tk.Event) -> None:
		""" Scroll on the y-axis """
		self.target.yview_scroll(int(-1 * (e.delta / 120)), 'units')

	def set(self, low: Any, high: Any) -> None:
		""" Set the value of the scrollbar """
		if not self.enabled:
			return

		if float(low) <= 0.0 and float(high) >= 1.0:
			self.grid_remove()
		else:
			self.grid()
			ttk.Scrollbar.set(self, low, high)


class CustomComboBox(ttk.Combobox):
	""" Creates a ttk combobox with a custom themed scrollbar """

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		## Referenced from: https://stackoverflow.com/a/63135420
		window.eval(f'set popdown [ttk::combobox::PopdownWindow {self}]')
		window.eval(f'$popdown.f.sb configure -style {kwargs["style"]}.Vertical.TScrollbar')


class CustomRadiobutton(tk.Radiobutton):
	"""
	A custom radiobutton widget that allows the user to set a custom foreground colour to use when the radiobutton's value is selected
	"""

	def __init__(self, *args, **kwargs) -> None:
		self.selectforeground = kwargs.pop('selectforeground') if 'selectforeground' in kwargs else None
		super().__init__(*args, **kwargs)
		self.variable = self.cget('variable')
		self.normalforeground = self.cget('foreground')

		kwargs['variable'].trace_add('write', lambda name, index, mode: self.change_val())  # Add a trace to the radiobutton's variable to call the `change_val` function whenever the variable's value is changed

		self.change_val()

	def change_val(self) -> None:
		"""
		Called whenever the value of the radiobutton variable changes. Updates the foreground and background colour of the widget
		"""

		if self.variable.get() == self.cget('value'):
			self.configure(foreground=self.selectforeground, background='#2E3274')
		else:
			self.configure(foreground=self.normalforeground, background='#272E35')


class MouseoverButton(tk.Button):
	"""
	A Button subclass that changes the foreground and background colour when moused-over
	"""

	def __init__(self, *args, **kwargs) -> None:
		self.mouseover_bg = kwargs.pop('mouseoverbackground') if 'mouseoverbackground' in kwargs else None
		self.mouseover_fg = kwargs.pop('mouseoverforeground') if 'mouseoverforeground' in kwargs else None
		super().__init__(*args, **kwargs)
		self.default_bg = self.cget('background')
		self.default_fg = self.cget('foreground')
		self.bind('<Enter>', lambda v: self.enter(), add='+')
		self.bind('<Leave>', lambda v: self.leave(), add='+')

	def enter(self) -> None:
		"""
		Called when the mouse cursor enters the widget. Changes the foreground and/or background colour.
		"""

		if self.mouseover_bg is not None:
			self.configure(background=self.mouseover_bg)
		if self.mouseover_fg is not None:
			self.configure(foreground=self.mouseover_fg)

	def leave(self) -> None:
		"""
		Called when the mouse cursor leaves the widget. Changes the foreground and/or background colour.
		"""

		if self.mouseover_bg is not None:
			self.configure(background=self.default_bg)
		if self.mouseover_fg is not None:
			self.configure(foreground=self.default_fg)


class WindowTopbar(tk.Frame):
	def __init__(self, root, *args, **kwargs) -> None:
		super().__init__(root, *args, **kwargs)
		self.root: Window = root
		icons = root.icons

		self.columnconfigure(10, weight=1)
		self.rowconfigure(0, weight=1)

		buttonconfig = {'background': self.cget('background'), 'width': 27, 'height': 27, 'activebackground': '#303841', 'mouseoverbackground': '#303841', 'borderwidth': 0}

		MouseoverButton(self, image=icons['save'], command=lambda: self.root.save_timetable(), **buttonconfig).grid(row=0, column=2, sticky='nswe', padx=(0, 1))
		MouseoverButton(self, image=icons['saveas'], command=lambda: self.root.save_timetable_as(), **buttonconfig).grid(row=0, column=3, sticky='nswe', padx=(0, 10))

		MouseoverButton(self, image=icons['undo'], command=lambda: self.root.undo(), **buttonconfig).grid(row=0, column=4, sticky='nswe', padx=(0, 1))
		MouseoverButton(self, image=icons['redo'], command=lambda: self.root.redo(), **buttonconfig).grid(row=0, column=5, sticky='nswe', padx=(0, 10))

		MouseoverButton(self, image=icons['settings'], command=lambda: self.root.show_settings(), **buttonconfig).grid(row=0, column=6, sticky='nswe', padx=(0, 10))

		file_menubutton = tk.Menubutton(self, text='File', relief='flat', borderwidth=0, activebackground='#323232', image=self.root.pixel, compound='center', height=13, width=50, background=self.cget('background'), foreground='#D8DEE9', activeforeground='#D8DEE9', font=('Calibri', 13))
		file_menubutton.grid(row=0, column=7, sticky='nswe', padx=(0, 1))

		export_menu = tk.Menu(file_menubutton, tearoff=0, background='#323232', relief='flat', foreground='#fff', borderwidth=0, activeborderwidth=0, type='normal')
		export_menu.add_command(label='CSV', image=icons['csv'], compound='left', command=lambda: self.root.export_timetable('csv'))
		export_menu.add_command(label='Excel Spreadsheet', image=icons['xls'], compound='left', command=lambda: self.root.export_timetable('xls'))
		export_menu.add_command(label='PDF', image=icons['pdf'], compound='left', command=lambda: self.root.export_timetable('pdf'))

		file_menu = tk.Menu(file_menubutton, tearoff=0, background='#323232', relief='flat', foreground='#fff', borderwidth=0, activeborderwidth=0, type='normal')
		file_menu.add_command(label='Save', image=icons['save'], compound='left', hidemargin=True, command=lambda: self.root.save_timetable())
		file_menu.add_command(label='Save As', image=icons['saveas'], compound='left', hidemargin=True, command=lambda: self.root.save_timetable_as())
		file_menu.add_command(label='Save a Copy', image=icons['savecopy'], compound='left', hidemargin=True, command=lambda: self.root.save_timetable_copy())
		file_menu.add_separator(background='#D4D4D4')
		file_menu.add_command(label='New', image=icons['new'], compound='left', hidemargin=True, command=lambda: self.root.new_timetable())
		file_menu.add_command(label='Load', image=icons['load'], compound='left', hidemargin=True, command=lambda: self.root.load_timetable())
		file_menu.add_separator(background='#D4D4D4')
		file_menu.add_cascade(label='Export', image=icons['export'], compound='left', hidemargin=True, menu=export_menu)
		file_menu.add_separator(background='#D4D4D4')
		file_menu.add_command(label='Settings', image=icons['settings'], compound='left', hidemargin=True, command=lambda: self.root.show_settings())
		file_menubutton.configure(menu=file_menu)

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
	def __init__(self, root, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.root: ExportAsPDFMenu = root
		self.style_option = tk.StringVar(self)

		# self.rowconfigure(0, weight=1)
		# self.columnconfigure(12, weight=1)

		self.class_dropdown = CustomComboBox(self, style='TCombobox', textvariable=self.style_option, values=['GRID', 'ALIGN', 'VALIGN', 'FONT', 'TOPPADDING', 'FONTSIZE', 'TEXTCOLOR', 'BACKGROUND', 'SPAN', 'BOTTOMPADDING'])
		self.class_dropdown.pack(side='left', fill='y', padx=1, pady=1)#.grid(row=0, column=0, sticky='NSWE', padx=(1, 1), pady=1)

		tk.Frame(self, background='#000', width=12).pack(side='left', fill='y')#.grid(row=0, column=1, sticky='NSWE', pady=0)

		tk.Label(self, background='#303841', foreground='#D8DEE9', text='X₁', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)#.grid(row=0, column=2, sticky='NSWE', padx=(1, 0), pady=1)

		self.x1_entry = ttk.Entry(self, style='stipple.TEntry', width=2, validate='focusout')
		self.x1_entry.configure(invalidcommand=lambda: self.invalid_input(self.x1_entry, 'Must be an integer within the bounds of the table.'), validatecommand=lambda v: self.validate_pos(self.x1_entry, 'x'))
		self.x1_entry.pack(side='left', fill='y', padx=(1, 0), pady=1)#.grid(row=0, column=3, sticky='NSWE', padx=(1, 0), pady=1)

		tk.Label(self, background='#303841', foreground='#D8DEE9', text='Y₁', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)#.grid(row=0, column=4, sticky='NSWE', padx=(1, 0), pady=1)

		self.y1_entry = ttk.Entry(self, style='stipple.TEntry', width=2, validate='focusout')
		self.y1_entry.configure(invalidcommand=lambda: self.invalid_input(self.y1_entry, 'Must be an integer within the bounds of the table.'), validatecommand=lambda v: self.validate_pos(self.y1_entry, 'y'))
		self.y1_entry.pack(side='left', fill='y', padx=(1, 1), pady=1)#.grid(row=0, column=5, sticky='NSWE', padx=(1, 0), pady=1)

		tk.Frame(self, background='#000', width=12).pack(side='left', fill='y')#.grid(row=0, column=6, sticky='NSWE', pady=0)


		tk.Label(self, background='#303841', foreground='#D8DEE9', text='X₂', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)#.grid(row=0, column=7, sticky='NSWE', padx=(1, 0), pady=1)

		self.x2_entry = ttk.Entry(self, style='stipple.TEntry', width=2, validate='focusout')
		self.x2_entry.configure(invalidcommand=lambda: self.invalid_input(self.x2_entry, 'Must be an integer within the bounds of the table.'), validatecommand=lambda v: self.validate_pos(self.x2_entry, 'x'))
		self.x2_entry.pack(side='left', fill='y', padx=(1, 0), pady=1)#.grid(row=0, column=7, sticky='NSWE', padx=(1, 0), pady=1)

		tk.Label(self, background='#303841', foreground='#D8DEE9', text='Y₂', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)#.grid(row=0, column=8, sticky='NSWE', padx=(1, 0), pady=1)

		self.y2_entry = ttk.Entry(self, style='stipple.TEntry', width=2, validate='focusout')
		self.y2_entry.configure(invalidcommand=lambda: self.invalid_input(self.y2_entry, 'Must be an integer within the bounds of the table.'), validatecommand=lambda v: self.validate_pos(self.y2_entry, 'y'))
		self.y2_entry.pack(side='left', fill='y', padx=(1, 1), pady=1)#.grid(row=0, column=9, sticky='NSWE', padx=(1, 1), pady=1)

		tk.Frame(self, background='#000', width=12).pack(side='left', fill='y')#.grid(row=0, column=10, sticky='NSWE', pady=0)

		tk.Label(self, background='#303841', foreground='#D8DEE9', text='Value ', font=('Calibri', 12)).pack(side='left', fill='y', padx=(1, 0), pady=1)#.grid(row=0, column=11, sticky='NSWE', padx=(1, 0), pady=1)

		self.value_entry = ttk.Entry(self, style='stipple.TEntry', validate='focusout')
		self.value_entry.configure(invalidcommand=lambda: self.invalid_input(self.value_entry, 'Invalid Value'), validatecommand=lambda: self.validate_value())
		self.value_entry.pack(side='left', expand=True, fill='both', padx=(1, 1), pady=1)#.grid(row=0, column=12, sticky='NSWE', padx=(0, 1), pady=1)

		self.bind_class(f'click:{id(self)}', '<Button-1>', lambda v: self.clicked())
		self.bindtags((f'click:{id(self)}', *self.bindtags()))
		for i in self.winfo_children():
			i.bindtags((f'click:{id(self)}', *i.bindtags()))

	def clicked(self):
		if self.root.selected_format_option == self:
			self.deselect()
			self.root.selected_format_option = None
		else:
			if self.root.selected_format_option is not None:
				self.root.selected_format_option.deselect()
			self.root.selected_format_option = self
			self.select()

	def select(self):
		self.configure(background='#F9AE58')

	def deselect(self):
		self.configure(background='#3B434C')

	def select_style_class(self):
		pass

	def validate_pos(self, elem, mode):
		val = elem.get()
		if not val.removeprefix('-').isnumeric():
			return False

		if mode == 'x':
			return -7 <= int(val) <= 6
		else:
			return -(len(self.root.timetable_data['sessions'])) <= int(val) <= (len(self.root.timetable_data['sessions']) - 1)

	def invalid_input(self, elem, text):
		cursor_pos = elem.index(tk.INSERT)
		mb.showinfo('Invalid Input', text)
		elem.focus()
		elem.icursor(cursor_pos)

	def validate_class(self):
		pass

	def validate_value(self):
		val = self.value_entry.get()
		# print(eval(f'[{val}]'))

		try:
			eval(f'[{val}]')
			return True
		except:
			return False


from reportlab.lib.colors import HexColor
from reportlab.lib.colors import Color
from reportlab.lib import units
from reportlab.platypus import Table
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.ttfonts import TTFont

## todo: add font, colours, margin, to export PDF

class verticalText(Flowable):
	'''
	Rotates a text in a table cell.
	From: https://stackoverflow.com/a/40349017
	'''

	def __init__(self, text, bottompadding=0):
		Flowable.__init__(self)
		self.text = text
		self.bottompadding = bottompadding

	def draw(self):
		canvas = self.canv
		canvas.rotate(90)
		fs = canvas._fontsize
		canvas.translate(1, -fs/1.2)  # canvas._leading?
		canvas.drawString(0, self.bottompadding, self.text)

	def wrap(self, aW, aH):
		canv = self.canv
		fn, fs = canv._fontname, canv._fontsize
		return canv._leading, 1 + canv.stringWidth(self.text, fn, fs)





class ExportAsPDFMenu(tk.Toplevel):
	def __init__(self, root, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.root = root
		# self.page_preset = tk.StringVar(self)
		self.configure(background='#222', padx=1, pady=1)
		self.columnconfigure(2, weight=1)
		self.rowconfigure(10, weight=1)

		frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		frame.grid(row=0, column=0, columns=3, sticky='NSWE', padx=0, pady=(0, 0))
		# frame.rowconfigure(0, weight=1)
		frame.columnconfigure(1, weight=1)

		labelconfig = dict(background='#303841', foreground='#D8DEE9', image=self.root.pixel, font=('Calibri', 11), compound='center', height=14)

		tk.Label(frame, text='Output File', width=60, **labelconfig).grid(row=0, column=0, sticky='NSWE', padx=(0, 1), pady=0)

		self.filename_entry = ttk.Entry(frame, style='stipple.TEntry')
		self.filename_entry.grid(row=0, column=1, sticky='NSWE', padx=(0, 1), pady=0)
		self.filename_entry.insert(0, self.root.filename.removesuffix('.json').removesuffix('.txt') + '.pdf')

		MouseoverButton(frame, command=lambda: self.browse_filename(), background='#303841', activebackground='#303841', mouseoverbackground='#3B434C', borderwidth=0, image=self.root.icons['load'], compound='center', highlightthickness=1, highlightbackground='#4F565E', width=25, anchor='center', height=20).grid(row=0, column=2, sticky='nswe', padx=(0, 0), pady=0)

		format_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		format_options_frame.grid(row=1, column=0, columns=2, sticky='nswe', padx=0, pady=(7, 0))


		# frame = tk.Frame(self, background='#3B434C')
		# frame.grid(row=2, column=0, columns=2, sticky='NSWE', padx=(1, 0), pady=(0, 1))
		# frame.rowconfigure(0, weight=1)
		# frame.columnconfigure((0, 2), weight=1)
		# tk.Frame(format_options_frame, background='#222', height=7).pack(side='top', fill='both', expand=True)
		tk.Label(format_options_frame, text='Page Size', **labelconfig).pack(side='top', padx=(0, 0), pady=(0, 1), fill='x')
		tk.Frame(format_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		self.presets_selector = CustomComboBox(format_options_frame, style='TCombobox', values=['A4 (Portrait)', 'A5 (Portrait)', 'A4 (Landscape)', 'A5 (Landscape)'], width=5)
		self.presets_selector.pack(side='top', padx=(0, 0), pady=(0, 1), fill='x')
		self.presets_selector.set('A4 (Portrait)')

		self.width_entry = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.width_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')
		self.width_entry.insert(0, '29.7')

		tk.Label(format_options_frame, text='x', width=10, **labelconfig).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.height_entry = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.height_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')
		self.height_entry.insert(0, '40')

		self.page_units = CustomComboBox(format_options_frame, style='TCombobox', values=['px', 'pt', 'cm', 'mm', 'in'], width=3)
		self.page_units.pack(side='left', padx=0, pady=0, fill='both')
		self.page_units.set('cm')

		# tk.Frame(frame, background='#303841').grid(row=3, column=0, columns=2, sticky='nswe')
		#
		format_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		format_options_frame.grid(row=2, column=0, columns=2, sticky='nswe', padx=0, pady=(7, 0))

		# tk.Frame(format_options_frame, background='#222', height=7).pack(side='top', fill='both', expand=True)
		tk.Label(format_options_frame, text='Table Size', **labelconfig).pack(side='top', anchor='w', padx=0, pady=0, fill='x')
		tk.Frame(format_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		self.table_width_entry = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.table_width_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')
		self.table_width_entry.insert(0, 'Auto')

		tk.Label(format_options_frame, text='x', width=10, **labelconfig).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.table_height_entry = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.table_height_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')
		self.table_height_entry.insert(0, 'Auto')

		self.table_units = CustomComboBox(format_options_frame, style='TCombobox', values=['px', 'pt', 'cm', 'mm', 'in', '%'], width=3)
		self.table_units.pack(side='left', padx=0, pady=0, fill='both')
		self.table_units.set('cm')

		format_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		format_options_frame.grid(row=3, column=0, columns=2, sticky='nswe', padx=0, pady=(7, 0))

		# tk.Frame(format_options_frame, background='#222', height=7).pack(side='top', fill='both', expand=True)
		tk.Label(format_options_frame, text='Margins', **labelconfig).pack(side='top', padx=0, pady=(0, 0), fill='x')
		tk.Frame(format_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		tk.Label(format_options_frame, text='↔', width=15, **labelconfig).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.h_margin_entry = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.h_margin_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')
		self.h_margin_entry.insert(0, 'Auto')

		tk.Label(format_options_frame, text='↕', width=15, **labelconfig).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.v_margin_entry = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.v_margin_entry.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')
		self.v_margin_entry.insert(0, 'Auto')

		self.margin_units = CustomComboBox(format_options_frame, style='TCombobox', values=['px', 'pt', 'cm', 'mm', 'in', '%'], width=3)
		self.margin_units.pack(side='left', padx=0, pady=0, fill='both')
		self.margin_units.set('cm')

		format_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		format_options_frame.grid(row=4, column=0, columns=2, sticky='nswe', padx=0, pady=(7, 0))

		# tk.Frame(format_options_frame, background='#222', height=7).pack(side='top', fill='both', expand=True)
		tk.Label(format_options_frame, text='Bottom Padding', **labelconfig).pack(side='top', padx=0, pady=(0, 0), fill='x')
		tk.Frame(format_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		self.bottom_padding_0 = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.bottom_padding_0.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')
		self.bottom_padding_0.insert(0, '5')

		self.bottom_padding_1 = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.bottom_padding_1.pack(side='left', padx=(0, 1), pady=0, expand=True, fill='both')
		self.bottom_padding_1.insert(0, '15')

		self.bottom_padding_2 = ttk.Entry(format_options_frame, style='stipple.TEntry', width=5)
		self.bottom_padding_2.pack(side='left', padx=(0, 0), pady=0, expand=True, fill='both')
		self.bottom_padding_2.insert(0, '25')
		# self.bottom_padding_1.configure(state='disabled')

		# tk.Frame(format_options_frame, background='#222', height=7).pack(side='bottom', fill='both', expand=True)

		format_options_frame = tk.Frame(self, background='#3B434C', highlightthickness=1, highlightbackground='#3B434C')
		format_options_frame.grid(row=5, column=0, columns=2, sticky='nswe', padx=0, pady=(7, 0))

		# tk.Frame(format_options_frame, background='#222', height=7).pack(side='top', fill='both', expand=True)
		tk.Label(format_options_frame, text='Round Corners', **labelconfig).pack(side='top', padx=0, pady=(0, 0), fill='x')
		tk.Frame(format_options_frame, background='#222', height=1).pack(side='top', fill='both', pady=(0, 1))

		self.margin_units = CustomComboBox(format_options_frame, style='TCombobox', values=['px', 'pt', 'cm', 'mm', 'in', '%'], width=3)
		self.margin_units.pack(side='top', padx=0, pady=(0, 1), fill='both')
		self.margin_units.set('cm')

		frame = tk.Frame(format_options_frame, background='#3B434C')
		frame.pack(side='top', expand=True, fill='both')

		tk.Label(frame, text='◴', **labelconfig, width=10).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.nw_corner_radius = ttk.Entry(frame, style='stipple.TEntry', width=5)
		self.nw_corner_radius.pack(side='left', padx=(0, 1), expand=True, fill='both')
		self.nw_corner_radius.insert(0, '5.0')

		tk.Label(frame, text='◷', **labelconfig, width=10).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.ne_corner_radius = ttk.Entry(frame, style='stipple.TEntry', width=5)
		self.ne_corner_radius.pack(side='left', padx=(0, 0), expand=True, fill='both')
		self.ne_corner_radius.insert(0, '5.0')

		frame = tk.Frame(format_options_frame, background='#3B434C')
		frame.pack(side='top', expand=True, fill='both')

		tk.Label(frame, text='◵', **labelconfig, width=10).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.sw_corner_radius = ttk.Entry(frame, style='stipple.TEntry', width=5)
		self.sw_corner_radius.pack(side='left', padx=(0, 1), expand=True, fill='both')
		self.sw_corner_radius.insert(0, '5.0')

		tk.Label(frame, text='◶', **labelconfig, width=10).pack(side='left', padx=(0, 1), pady=0, fill='y')

		self.se_corner_radius = ttk.Entry(frame, style='stipple.TEntry', width=5)
		self.se_corner_radius.pack(side='left', padx=(0, 0), expand=True, fill='both')
		self.se_corner_radius.insert(0, '5.0')

		self.match_corner_radius = tk.BooleanVar(self, True)
		ttk.Checkbutton(format_options_frame, style='Custom.TCheckbutton', text='Match Radius', variable=self.match_corner_radius).pack(side='top', fill='both', pady=(0, 1))


		# tk.Frame(self, background='#222', height=7).grid(row=5, column=0, columns=2, sticky='NSWE', pady=(1, 0))


		# self.expand_x = tk.BooleanVar(self)
		# self.expand_y = tk.BooleanVar(self)

		# frame = tk.Frame(self, background='#3B434C')
		# frame.grid(row=4, column=0, columns=2, sticky='NSWE', padx=1, pady=(0, 0))
		# frame.rowconfigure(0, weight=1)
		# frame.columnconfigure((0, 1), weight=1)

		# self.expand_x_toggle = ttk.Checkbutton(frame, style='Custom.TCheckbutton', text='Expand X', variable=self.expand_x)
		# self.expand_x_toggle.grid(row=4, column=0, sticky='NSWE', padx=(0, 1), pady=(1, 0))
		#
		# self.expand_y_toggle = ttk.Checkbutton(frame, style='Custom.TCheckbutton', text='Expand Y', variable=self.expand_y)
		# self.expand_y_toggle.grid(row=4, column=1, sticky='NSWE', padx=(0, 0), pady=(1, 0))

		# tk.Label(self, text='Bottom Padding', width=100, **labelconfig).grid(row=5, column=0, sticky='NSWE', padx=1, pady=(1, 0))
		#
		# self.bottom_padding = ttk.Entry(self, style='stipple.TEntry', width=5)
		# self.bottom_padding.grid(row=5, column=1, sticky='NSWE', padx=(0, 0), pady=(1, 0))
		# self.bottom_padding.insert(0, '5, 15, 25')
		# self.bottom_padding.configure(state='disabled')

		# tk.Label(self, background='#303841', foreground='#D8DEE9', text='Round Corners', font=('Calibri', 12)).grid(row=6, column=0, columns=2, sticky='NSWE', padx=(1, 0), pady=(1, 0))
		#
		# frame = tk.Frame(self, background='#3B434C')
		# frame.grid(row=7, column=0, columns=2, sticky='NSWE', padx=(1, 0), pady=(1, 0))
		# # frame.rowconfigure(0, weight=1)
		# frame.columnconfigure((0, 1), weight=1)
		#
		# self.nw_corner_radius = ttk.Entry(frame, style='stipple.TEntry', width=5)
		# self.nw_corner_radius.grid(row=7, column=0, sticky='NSWE', padx=0, pady=0)
		# self.nw_corner_radius.insert(0, '5')
		#
		# self.ne_corner_radius = ttk.Entry(frame, style='stipple.TEntry', width=5)
		# self.ne_corner_radius.grid(row=7, column=1, sticky='NSWE', padx=(1, 0), pady=0)
		# self.ne_corner_radius.insert(0, '5')
		#
		# self.sw_corner_radius = ttk.Entry(frame, style='stipple.TEntry', width=5)
		# self.sw_corner_radius.grid(row=8, column=0, sticky='NSWE', padx=0, pady=(1, 1))
		# self.sw_corner_radius.insert(0, '5')
		#
		# self.se_corner_radius = ttk.Entry(frame, style='stipple.TEntry', width=5)
		# self.se_corner_radius.grid(row=8, column=1, sticky='NSWE', padx=(1, 0), pady=(1, 1))
		# self.se_corner_radius.insert(0, '5')

		frame = tk.Frame(self, background='#222')
		frame.grid(row=1, column=2, columns=1, rows=7, sticky='NSWE', padx=(10, 0), pady=(7, 0))
		frame.rowconfigure(1, weight=1)
		frame.columnconfigure(1, weight=1, minsize=500)

		tk.Label(frame, text='Formatting', **labelconfig, highlightthickness=1, highlightbackground='#3B434C').grid(row=0, column=0, columns=3, sticky='NSWE', pady=(0, 1))

		self.vscrollbar = ttk.Scrollbar(frame, orient='vertical', style='Custom.Vertical.TScrollbar')
		self.vscrollbar.grid(row=1, column=2, sticky='ns', padx=(0, 0), pady=0)

		self.canvas = tk.Canvas(frame, highlightthickness=1, background='#000', yscrollcommand=self.vscrollbar.set, highlightbackground='#3B434C')
		self.canvas.grid(row=1, column=0, columns=2, sticky='NSWE', padx=(0, 1), pady=0)

		self.vscrollbar.configure(command=self.canvas.yview)

		self.canvas.xview_moveto(0)
		self.canvas.yview_moveto(0)

		self.formatting_frame = tk.Frame(self.canvas, background='#000')

		self.scrollable_frame = self.canvas.create_window(0, 0, window=self.formatting_frame, anchor='nw')

		frame1 = tk.Frame(frame, background='#3B434C')
		frame1.grid(row=2, column=0, sticky='nsw', padx=(0, 1), pady=(1, 0))
		MouseoverButton(frame1, text='+', command=lambda: self.add_formatting(), background='#303841', foreground='#D8DEE9', activebackground='#303841', mouseoverbackground='#3B434C', borderwidth=0, font=('Calibri', 12), image=self.root.pixel, compound='center', highlightthickness=1, highlightbackground='#4F565E', width=18, height=18).pack(side='left', padx=(1, 1), pady=(1, 1))

		frame1 = tk.Frame(frame, background='#3B434C')
		frame1.grid(row=2, column=1, sticky='nsw', padx=(0, 0), pady=(1, 0))
		# frame = tk.Frame(frame, background='#3B434C')
		# frame.pack(side='left', padx=1, pady=(1, 0))
		# tk.Frame(frame, background='#222').grid(row=1, column=3, columns=2, sticky='nswe', padx=(0, 0), pady=(0, 0))
		## todo: rm ah
		MouseoverButton(frame1, text='-', command=lambda: self.remove_formatting(), background='#303841', foreground='#D8DEE9', activebackground='#303841', mouseoverbackground='#3B434C', borderwidth=0, font=('Calibri', 12), image=self.root.pixel, compound='center', highlightthickness=1, highlightbackground='#4F565E', width=18, height=18).pack(side='left', padx=(1, 1), pady=(1, 1))


		frame = tk.Frame(self, background='#3B434C')
		frame.grid(row=9, column=0, columns=3, sticky='NSWE', padx=1, pady=(0, 0))
		frame.rowconfigure(0, weight=1)
		frame.columnconfigure(0, weight=1)

		tk.Frame(frame, background='#222').pack(side='left', fill='both', expand=True)

		MouseoverButton(frame, text='Cancel', command=lambda: self.destroy(), background='#303841', foreground='#D8DEE9', activebackground='#303841', mouseoverbackground='#3B434C', borderwidth=0, font=('Calibri', 12), image=self.root.pixel, compound='center', highlightthickness=1, highlightbackground='#4F565E', width=50, height=20).pack(side='left', padx=(1, 0), fill='y', pady=1)  # .grid(row=1, column=1, sticky='nswe', padx=(0, 1), pady=(0, 0))
		MouseoverButton(frame, text='Export', command=lambda: self.convert(), background='#303841', foreground='#D8DEE9', activebackground='#303841', mouseoverbackground='#3B434C', borderwidth=0, font=('Calibri', 12), image=self.root.pixel, compound='center', highlightthickness=1, highlightbackground='#4F565E', width=50, height=20).pack(side='left', padx=(1, 1), fill='y', pady=1)  # .grid(row=1, column=0, sticky='nswe', padx=(0, 1), pady=(0, 0))


		self.selected_format_option: Optional[FormattingOption] = None
		self.formatting_elems = []
		self.timetable_data = None
		# self.cw = None
		# self.rh = None
		self.tablestyle = None
		self.read(self.root.filename)

		for i in self.tablestyle:
			elem = FormattingOption(self, self.formatting_frame, background='#3B434C')
			elem.pack(side='top', fill='x', padx=1, pady=(1, 0))
			elem.style_option.set(i[0])
			elem.x1_entry.insert(0, str(i[1][0]))
			elem.x2_entry.insert(0, str(i[2][0]))
			elem.y1_entry.insert(0, str(i[1][1]))
			elem.y2_entry.insert(0, str(i[2][1]))
			print(list(i[2:]))
			elem.value_entry.insert(0, str(list(i[3:]))[1:-1])

			self.formatting_elems.append(elem)

		## From: https://stackoverflow.com/a/16198198
		def _configure_interior(event):
			# Update the scrollbars to match the size of the inner frame.
			size = (self.formatting_frame.winfo_reqwidth(), self.formatting_frame.winfo_reqheight())
			self.canvas.config(scrollregion="0 0 %s %s" % size)
			if self.formatting_frame.winfo_reqwidth() != self.canvas.winfo_width():
				# Update the canvas's width to fit the inner frame.
				self.canvas.config(width=self.formatting_frame.winfo_reqwidth())

		self.formatting_frame.bind('<Configure>', _configure_interior)

		def _configure_canvas(event):
			if self.formatting_frame.winfo_reqwidth() != self.canvas.winfo_width():
				# Update the inner frame's width to fill the canvas.
				self.canvas.itemconfigure(self.scrollable_frame, width=self.canvas.winfo_width())

		self.canvas.bind('<Configure>', _configure_canvas)

	def read(self, input_filename):
		with open(input_filename, 'r', encoding='utf-8') as input_file:
			timetable = json.load(input_file)

		self.timetable_data = timetable
		# document = BaseDocTemplate(output_filename)

		# elems = []

		# title_frame_1 = Frame(0 * cm, 0 * cm, 17.5 * cm, 22.5 * cm, id='col1', showBoundary=0)
		# title_template_1 = PageTemplate(id='OneCol', frames=title_frame_1)
		# canvas.addPageTemplates([title_template_1])

		self.tablestyle = [
			('GRID', (0, 0), (-1, -1), 0.5, HexColor(0x000000)),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('FONT', (0, 0), (0, -1), 'Calibri-Bold', 7, 7),
			('FONT', (0, 0), (-1, 0), 'Calibri-Bold', 7, 7),
			('FONT', (1, 1), (-1, -1), 'Calibri', 7, 7),
			('BACKGROUND', (0, 0), (-1, 0), HexColor(0xD3D3D3)),
			('BACKGROUND', (0, 0), (0, -1), HexColor(0xD3D3D3)),
			('SPAN', (-2, 2), (-2, -1)),
			('SPAN', (-1, 2), (-1, -1)),
		]

	## todo: add margins
		# if bottompadding[2]:
		# 	ts.append(('BOTTOMPADDING', (0, 0), (-1, 0), bottompadding[2]))
		# if bottompadding[1]:
		# 	ts.append(('BOTTOMPADDING', (1, 1), (-1, -1), bottompadding[1]))

	# def validate_units(self):
	# 	return self.units_selector.get() in ['cm', 'mm', 'in', 'px', 'pt']


	def convert(self):
		# if append:
		# 	canvas = Canvas(dir_name + '/img2pdf_tmp.pdf', (doc_w, doc_h))
		# else:
		output_filename = self.filename_entry.get()
		if not output_filename.endswith('.pdf'):
			output_filename += '.pdf'

		self.tablestyle = []
		for i in self.formatting_elems:
			# print(f'[{i.value_entry.get()}]')
			line = [i.style_option.get(), (int(i.x1_entry.get()), int(i.y1_entry.get())), (int(i.x2_entry.get()), int(i.y2_entry.get())), *eval(f'[{i.value_entry.get()}]')]
			self.tablestyle.append(line)

		unit = {'cm': units.cm, 'mm': units.mm, 'pt': units.pica, 'px': 1, 'in': units.inch}[self.units_selector.get()]
		doc_w = float(self.width_entry.get()) * unit
		doc_h = float(self.height_entry.get()) * unit

		margin = [1.5 * units.cm, 1.5 * units.cm]

		if self.table_width_entry.get().lower() == 'auto':
			tablewidth = doc_w - margin[0] * 2
		else:
			tablewidth = float(self.table_width_entry.get()) * unit

		if self.table_height_entry.get().lower() == 'auto':
			tableheight = doc_h - margin[1] * 2
		else:
			tableheight = float(self.table_height_entry.get()) * unit

		session_types = [v[1] for v in self.timetable_data['sessions']]

		## Get relative column widths and row heights
		cw = [0.6] + [2] * 7
		rh = [0.6] + [0.5] * (3 * sum(session_types) + session_types.count(False))
		print(tableheight, tablewidth, sum(rh) * unit, sum(cw) * unit)

		h_scale = tablewidth / (sum(cw) * unit)
		v_scale = tableheight / (sum(rh) * unit)

		cw = [v * h_scale * unit for v in cw]
		rh = [v * v_scale * unit for v in rh]
		print('cw', cw, 'rh', rh)

		canvas = Canvas(output_filename, (doc_w, doc_h))

		data = [
			['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
		]

		bottompadding = eval(f'[{self.bottom_padding.get()}]')

		# if not self.expand_x.get():
		# 	bottompadding = [0, *bottompadding[1:]]
		# if not self.expand_y.get():
		# 	bottompadding = [bottompadding[0], 0, 0]

		break_count = 0

		for n, i in enumerate(self.timetable_data['sessions']):
			if i[1]:
				line_data = [[verticalText(i[0], bottompadding[0])], [''], ['']]
				self.tablestyle.extend([('SPAN', (0, len(data)), (0, len(data) + 2)), ('FONT', (1, len(data)), (-1, len(data)), 'Calibri-Bold', 7, 7)])
				for day_num, day in enumerate(self.timetable_data['timetable']):
					# print(day, n)
					class_index = day[n - break_count]
					line_data[0].append(self.timetable_data['classes'][class_index])
					line_data[1].append(self.timetable_data['teachers'][class_index])
					line_data[2].append(self.timetable_data['rooms'][class_index])
				line_data[0].extend(['', ''])
				line_data[1].extend(['', ''])
				line_data[2].extend(['', ''])

				data.extend(line_data)
			else:
				break_count += 1
				line_data = [i[0]] + [''] * 5
				self.tablestyle.extend([('SPAN', (0, len(data)), (-3, len(data))), ('FONT', (1, len(data)), (-1, len(data)), 'Calibri-Bold'), ('BACKGROUND', (1, len(data)), (-3, len(data)), HexColor(0xD3D3D3))])
				if bottompadding[2]:
					self.tablestyle.append(('BOTTOMPADDING', (0, len(data)), (-3, len(data)), bottompadding[2]))
				data.append(line_data)
		data[1][-1] = 'Homework'
		data[1][-2] = 'Homework'

		pdfmetrics.registerFont(TTFont(f'Calibri-Bold', 'calibrib.ttf'))
		pdfmetrics.registerFont(TTFont(f'Calibri', 'calibri.ttf'))
		# for i in data:
		# 	print(i)

		# if expand[0]:
		# 	total_w = doc_w - offset[0] * 2
		# 	size_scale = total_w/sum(cw)#*len(cw)
		# 	cw = [(i * size_scale) for i in cw]
		# 	print(size_scale, 'sc')
		# if expand[1]:
		# 	total_h = doc_h - offset[1] * 2
		# 	size_scale = total_h/sum(rh)#*len(rh)
		# 	rh = [(i * size_scale) for i in rh]
		# 	print(size_scale, 'sc')

		# if self.expand_x.get():
		header_size = 1
		face = pdfmetrics.getFont('Calibri-Bold').face
		h_height = (face.ascent - face.descent) / 1000 * (header_size + 0.5)
		while h_height < rh[0]/2:
			header_size += 0.5
			h_height = (face.ascent - face.descent) / 1000 * (header_size + 0.5)

		# print(face.descent, 'hh', rh[0] - (face.ascent - face.descent) / 1000 * header_size)

		body_size = 1
		face = pdfmetrics.getFont('Calibri').face
		b_height = (face.ascent - face.descent) / 1000 * (body_size + 0.5)
		while b_height < rh[1]/2:
			body_size += 0.5
			b_height = (face.ascent - face.descent) / 1000 * (body_size + 0.5)
		print(0.625 * units.cm, (face.ascent - face.descent) / 1000 * 6)
			# print(face.descent, 'fd', b_height)

		self.tablestyle.extend([
			('FONTSIZE', (0, 0), (0, -1), header_size),
			('FONTSIZE', (0, 0), (-1, 0), header_size),
			('FONTSIZE', (1, 1), (-1, -1), body_size),
		])

		table = Table(
			data, style=self.tablestyle,
			colWidths=cw, rowHeights=rh,
			cornerRadii=(int(self.nw_corner_radius.get()) if self.nw_corner_radius.get() else 0, int(self.ne_corner_radius.get()) if self.ne_corner_radius.get() else 0, int(self.sw_corner_radius.get()) if self.sw_corner_radius.get() else 0, int(self.se_corner_radius.get()) if self.se_corner_radius.get() else 0)
		)
		table.wrapOn(canvas, doc_w, doc_h)
		table.drawOn(canvas, margin[0], doc_h - margin[1] - tableheight)
		canvas.save()

		mb.showinfo('Success', f'Successfully converted {self.root.filename} to PDF.')

		webbrowser.open('file://' + self.filename_entry.get())

		self.destroy()

	def add_formatting(self):
		elem = FormattingOption(self, self.formatting_frame, background='#3B434C')
		elem.pack(side='top', fill='x', padx=1, pady=(1, 0))
		self.formatting_elems.append(elem)
		self.canvas.yview_moveto(10)

	def remove_formatting(self):
		if self.selected_format_option is not None:
			idx = self.formatting_elems.index(self.selected_format_option)
			self.formatting_elems.pop(idx).destroy()
			if len(self.formatting_elems):
				self.selected_format_option = self.formatting_elems[max(0, idx - 1)]
				self.selected_format_option.select()
# self.page_preview

		# self.format_preview_frame = tk.Frame(self)
		# self.format_preview_frame.grid(row=8, column=0, sticky='NSWE', padx=1, pady=1)
		#
		# self.h_header_preview = tk.Label(self.format_preview_frame, background='#ccc', foreground='#000', text='Monday')
		# self.h_header_preview.grid(row=0, column=0, sticky='nswe', padx=1, pady=1)
		#
		# self.v_header_preview
		# self.session_break_preview
		# self.room_preview
		# self.teacher_preview
		# self.day_preview
		#
		# self.header_font_family
		# self.header_font_style
		# self.header_font_size
		# self.header_font_colour
		# self.header_background
		#
		# self.session_font_family
		# self.session_font_style
		# self.session_font_size
		# self.session_font_colour
		# self.session_background
		#
		# self.cell_font_family
		# self.cell_font_style
		# self.cell_font_size
		# self.cell_font_colour
		# self.cell_background
		#
		# self.table_border_width
		# self.table_border_colour


## todo: loading bar: ⡿⢿⣻⣽⣾⣷⣯⣟

class IndentText(tk.Text):
	def __init__(self, parent, *args, **kwargs) -> None:
		self.parent: TimeTable = parent
		self.tab_spaces = kwargs.pop('tab_spaces') if 'tab_spaces' in kwargs else 4

		if 'font' in kwargs:
			if isinstance(kwargs['font'], tkfont.Font):
				self.font = kwargs['font']
			else:
				self.font = tkfont.Font(font=kwargs['font'])
		else:
			self.font = tkfont.Font(font=('Consolas', 10))

		kwargs.update({'font': self.font, 'tabs': self.font.measure(' ' * self.tab_spaces)})

		super().__init__(*args, **kwargs)

		self.cdg = ic.ColorDelegator()
		self.cdg.tagdefs = dict()

		dashpoint = r'(?P<DASHPOINT>[>\-])'
		dotpoints = r'(?P<DOTPOINT>[•o])'
		lettering = r'(?P<LETTERING>(([A-Z]{1,2})|([a-z]{1,2}))[\):])'
		numbering = r'(?P<NUMBERING>[0-9]{1,2}[\.\):])'
		pattern = rf'(\n|\A)[ \t]*({dotpoints}|{numbering}|{lettering}|{dashpoint})[ \t]+'
		self.cdg.prog = re.compile(pattern, re.S)
		self.cdg.idprog = re.compile(r'\s+(\w+)', re.S)

		self.cdg.tagdefs['DASHPOINT'] = {'foreground': '#F9AE57'}
		self.cdg.tagdefs['DOTPOINT'] = {'foreground': '#B8BBBE'}
		self.cdg.tagdefs['NUMBERING'] = {'foreground': '#60B4B4'}
		self.cdg.tagdefs['LETTERING'] = {'foreground': '#99C794'}
		self.percolator = ip.Percolator(self)
		self.percolator.insertfilter(self.cdg)

		self.bind('<KeyPress>', lambda v: self.key_press(v))

	def custom_update_callback(self) -> None:
		self.see(self.index(tk.INSERT))
		self.parent.on_edit()
		self.parent.update_button_states()

	def key_press(self, event: tk.Event) -> Optional[str]:
		self.parent.pause_text_event = False
		cursor_pos = self.index(tk.INSERT)
		linenum = cursor_pos.split('.')[0]
		match event.keysym:
			case 'Return':
				indent = self.check_indent(linenum)
				if indent is not None:
					self.insert(cursor_pos, '\n' + increment_numbering(indent))
					if event.state == 4:
						self.mark_set(tk.INSERT, cursor_pos)
					self.custom_update_callback()
					return 'break'
			case 'BackSpace':
				match event.state:
					case 1:  # Shift
						line = self.get(f'{linenum}.0', f'{linenum}.end')
						indent = self.check_indent(line=line)
						if indent == line:
							self.delete(f'{linenum}.0', f'{linenum}.end')
							self.custom_update_callback()
							return 'break'
					case 4:  # Control
						line = self.get(f'{linenum}.0', cursor_pos)
						re_match = re.match(r'\w+', line[::-1])
						if re_match is not None:
							if re_match.start() == 0:
								self.delete(f'{cursor_pos}-{re_match.end()}c', cursor_pos)
								self.custom_update_callback()
								return 'break'
						else:
							if line and line[-1] == ' ':
								re_match = re.match(r' +', line[::-1])
								if re_match.start() == 0:
									self.delete(f'{cursor_pos}-{min(4, re_match.end())}c', cursor_pos)
									self.custom_update_callback()
									return 'break'

					case 5:  # Control + Shift
						pass
					case _:
						line = self.get(f'{linenum}.0', f'{linenum}.end')
						indent = self.check_indent(line=line)
						if indent is not None and cursor_pos == f'{linenum}.{len(indent)}':
							location = re.match('[^\t ]+', indent)
							if location is None:
								if indent[-1] != '\t':
									self.delete(cursor_pos + f'-{min(4, len(indent))}c', cursor_pos)
									self.custom_update_callback()
									return 'break'

							else:
								location = location.span()
								if indent[location[1]] == '\t' or indent[0] == '\t':
									self.delete(f'{linenum}.{location[0]}', f'{linenum}.{len(indent)}')
									self.insert(f'{linenum}.{location[0]}', '\t')
								else:
									self.delete(f'{linenum}.{0}', f'{linenum}.{len(indent)}')
									print('numbering')
									self.insert(f'{linenum}.{location[0]}', ' ' * len(indent))
								self.custom_update_callback()
								return 'break'
			case 'Tab':
				if self.tag_ranges('sel'):
					lines = []
					for i in self.tag_ranges('sel')[::2]:
						lines.append(str(i).split('.')[0])
					lines = list(set(lines))
					for linenum in lines:
						line = self.get(f'{linenum}.0', f'{linenum}.end')
						indent = self.check_indent(line=line)
						if event.state == 1:
							if indent[0] == '\t':
								self.delete(f'{linenum}.0', f'{linenum}.1')
							elif indent[0] == ' ':
								self.delete(f'{linenum}.0', f'{linenum}.{min(4, re.match(r' *', indent).end())}')
							else:
								self.delete(f'{linenum}.0', f'{linenum}.{len(indent)}')
							self.custom_update_callback()
							return 'break'

						else:
							if indent is None or indent[0] == '\t':
								new_line = '\t'
							else:
								new_line = '    '
							if indent is not None and ('•' in indent or 'o' in indent or '' in indent):
								new_line += indent
								new_line = new_line.replace('•', 'o').replace('o', '').replace('', '•')
								self.delete(f'{linenum}.0', f'{linenum}.{len(indent)}')

							self.insert(f'{linenum}.0', new_line)
					self.custom_update_callback()
					return 'break'

				else:
					line = self.get(f'{linenum}.0', f'{linenum}.end')
					indent = self.check_indent(line=line)
					if indent is not None:
						if event.state == 1:
							if indent[0] == '\t':
								self.delete(f'{linenum}.0', f'{linenum}.1')
							elif indent[0] == ' ':
								self.delete(f'{linenum}.0', f'{linenum}.{min(4, re.match(r' *', indent).end())}')
							else:
								self.delete(f'{linenum}.0', f'{linenum}.{len(indent)}')
							self.custom_update_callback()
							return 'break'
						else:
							if int(cursor_pos.split('.')[1]) == len(indent):
								if self.get(cursor_pos + '-1c', cursor_pos) == ' ':
									self.insert(cursor_pos, '    ')
									self.custom_update_callback()
									return 'break'
		print(event)
		self.custom_update_callback()

	def check_indent(self, linenum: Optional[int | str] = None, line: Optional[str] = None) -> Optional[str]:
		if line is None:
			line = self.get(f'{linenum}.0', f'{linenum}.end')
		re_match = re.match(r'[ \t]*(([A-Z]{1,2}[):])|([a-z]{1,2}[):])|([0-9]{1,2}[.):])|[>•o-])?[ \t]+', line)
		if re_match is not None and re_match.start() == 0:
			return line[slice(*re_match.span())]


class WeekFrame(tk.Frame):
	def __init__(self, parent, week, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.week = week
		self.parent: TimeTable = parent

		self.indicator_elems: list[Optional[tk.Label]] = [None] * len(self.parent.event_types)

		self.event_data = {(v.day, v.session): v.event_type.get() for v in filter(lambda v: v.week == week, parent.events)}
		types = list(self.event_data.values())
		event_type_counts = [(n, i, types.count(i)) for n, i in enumerate(self.parent.event_types)]
		self.event_num_texts = [tk.StringVar(self, str(i[2])) for i in event_type_counts]

		self.bind_class(f'click:wk{self.week}', '<Button-1>', lambda v: self.set_week())
		self.bindtags((f'click:wk{self.week}', *self.bindtags()))
		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, weight=1, minsize=8)

		self.numlabel = tk.Label(self, text=f'Week {week + 1}{" (Current)" if week == self.parent.week else ""}', background='#303841', foreground='#D8DEE9', height=15, image=self.parent.master.pixel, compound='center', font=('Arial', 11, 'bold' if week == self.parent.week else ''), anchor='nw')
		self.numlabel.bindtags((f'click:wk{self.week}', *self.numlabel.bindtags()))
		self.numlabel.grid(row=0, column=0, sticky='nswe')

		self.indicator_frame = tk.Frame(self, background='#303841', height=8)
		self.indicator_frame.bindtags((f'click:wk{self.week}', *self.indicator_frame.bindtags()))
		self.indicator_frame.grid(row=1, column=0, sticky='nswe')

		## Add a blank image for formatting purposes
		self.formatting_image = tk.Label(self.indicator_frame, image=parent.master.pixel, compound='center', width=8, height=8, background='#303841')
		self.formatting_image.bindtags((f'click:wk{self.week}', *self.formatting_image.bindtags()))
		self.formatting_image.grid(row=0, column=len(self.parent.event_types), padx=(0, 1), pady=(1, 0), sticky='NW')

		for idx, e_type, count in filter(lambda v: v[2] > 0, event_type_counts):
			indicator = tk.Label(self.indicator_frame, textvariable=self.event_num_texts[idx], image=parent.master.icons[e_type], compound='left', width=15, height=8, background='#303841', foreground='#D8DEE9', font=('Calibri', 12))
			indicator.grid(row=0, column=idx, padx=(0, 1), pady=(1, 0), sticky='W')
			indicator.bindtags((f'click:wk{self.week}', *indicator.bindtags()))

			self.indicator_elems[idx] = indicator

	def set_week(self) -> None:
		self.parent.week_slider.set(self.week)

	def edit_event_type(self, event) -> None:
		if self.event_data[(event.day, event.session)] == event.event_type.get():
			return
		else:
			self.remove_event(event, event_type=self.event_data[(event.day, event.session)])
			self.add_event(event)

	def add_event(self, event) -> None:
		idx = self.parent.event_types.index(event.event_type.get())

		text = self.event_num_texts[idx]
		val = int(text.get())
		if val == 0:
			indicator = tk.Label(self.indicator_frame, textvariable=text, image=self.parent.master.icons[event.event_type.get()], compound='left', width=15, height=8, background='#303841', foreground='#D8DEE9', font=('Calibri', 12))
			indicator.grid(row=0, column=idx, padx=(0, 1), pady=(1, 0), sticky='W')
			self.indicator_elems[idx] = indicator
			indicator.bindtags((f'click:wk{self.week}', *indicator.bindtags()))
		text.set(str(val + 1))
		self.event_data.update({(event.day, event.session): event.event_type.get()})

	def remove_event(self, event, event_type: Optional[str] = None) -> None:
		if event_type is None:
			event_type = event.event_type.get()
		idx = self.parent.event_types.index(event_type)

		text = self.event_num_texts[idx]
		val = int(text.get())
		if val == 1:
			self.indicator_elems[idx].destroy()
			self.indicator_elems[idx] = None
		text.set(str(val - 1))
		self.event_data.pop((event.day, event.session))


class Event:
	def __init__(self, week: int, day: int, session: int, text: str, tags: Optional[list], event_type: str) -> None:
		self.week = week
		self.day = day
		self.session = session
		self.text = text
		self.tags = tags
		self.event_type = tk.StringVar(value=event_type)

	def match(self, week: int, day: int, session: int) -> bool:
		return week == self.week and day == self.day and session == self.session

	def get_data(self) -> dict:
		data = {
			'week': self.week,
			'day': self.day,
			'session': self.session,
			'data': enclose(multireplace(self.text, {'"': '\\"', '\n': '\\n', '\t': '\\t'}), '"'),
			'tags': enclose(self.tags, '"') if self.tags is not None else 'null',
			'type': enclose(self.event_type.get(), '"')
		}
		return data

	def __gt__(self, other) -> bool:
		return self.day > other.day or (self.day == other.day and self.session > other.session)

	def __lt__(self, other) -> bool:
		return self.day < other.day or (self.day == other.day and self.session < other.session)

	def __ge__(self, other) -> bool:
		return self.day > other.day or (self.day == other.day and self.session >= other.session)

	def __le__(self, other) -> bool:
		return self.day < other.day or (self.day == other.day and self.session <= other.session)


class TimetableCell:
	def __init__(self, root, master, day: int, session: int, class_data_idx: Optional[int], weekend: bool = False) -> None:
		self.root: TimeTable = root  # The root timetable object
		self.master = master  # The parent element
		self.day = day
		self.session = session
		self.class_data_idx = class_data_idx

		self.weekend = weekend

		self.state = 'normal'
		self.current_event = None

		self.frame = tk.Frame(master, background='#3B434C')
		self.frame.columnconfigure(0, weight=1)
		self.frame.rowconfigure(0, weight=1)

		self.events_indicator = None

		self.frame.bind('<Enter>', lambda v: self.enter())
		self.frame.bind('<Leave>', lambda v: self.leave())
		self.frame.bind_class(f'click:{id(self)}', '<Button-1>', lambda v: self.toggle_selected())

	def add_event_indicator(self) -> None:
		self.events_indicator = tk.Label(self.frame, image=self.root.master.pixel, compound='center', width=8, height=8, background='#303841')
		self.events_indicator.grid(row=0, column=0, padx=(0, 1), pady=(1, 0), sticky='NE')

	def set_event(self, event) -> None:
		self.current_event = event
		if event is None:
			self.events_indicator.configure(image=self.root.master.pixel)
		else:
			self.events_indicator.configure(image=self.root.master.icons[event.event_type.get()])

	def update_event(self) -> None:
		print('update event')
		events = list(filter(lambda v: v.match(self.root.week, self.day, self.session), self.root.events))
		if not events:
			self.events_indicator.configure(image=self.root.master.pixel)
			self.current_event = None

		elif events:
			self.current_event = events[0]
			self.events_indicator.configure(image=self.root.master.icons[self.current_event.event_type.get()])

		if self.state == 'active':
			self.root.update_active_event()

	def grid(self) -> None:
		print('len', len(self.root.sessions))
		self.frame.grid(column=self.day + 1, row=self.session + sum(map(lambda v: self.session > v, self.root.session_break_idxs[1])) + 1, sticky='nswe', padx=(int(self.day == 0), 1), pady=(int(self.session == 0), 1), rows=len(self.root.sessions) if self.weekend else 1)

	def enter(self) -> None:
		if self.state == 'normal':
			self.state = 'highlighted'
			self.update_elems()

	def leave(self) -> None:
		if self.state == 'highlighted':
			self.state = 'normal'
			self.update_elems()

	def toggle_selected(self) -> None:
		if self.state == 'active':
			self.state = 'highlighted'
			self.root.active_cell = None
		else:
			if self.root.active_cell is not None:
				self.root.active_cell.state = 'normal'
				self.root.active_cell.update_elems()
			self.root.active_cell = self
			self.state = 'active'
		self.update_elems()
		self.root.update_active_event()

	def update_elems(self) -> None:
		formatting = self.root.cell_state_config[self.state]
		self.frame.configure(background=formatting[1])
		for elem in self.frame.winfo_children():
			elem.configure(**formatting[0])


class WeekendCell(TimetableCell):
	def __init__(self, root, master, weekend_day: int) -> None:
		self.name = ['Saturday', 'Sunday'][weekend_day]

		super().__init__(root, master, weekend_day + 5, 0, None, True)

		self.name_display = tk.Label(self.frame, text='Homework', relief='flat', wraplength=75, font=('Calibri', 12, 'bold'), background='#303841', foreground='#D8DEE9', anchor='n')
		self.name_display.grid(row=0, column=0, padx=1, pady=1, sticky='NSWE')
		self.name_display.bindtags((f'click:{id(self)}', *self.name_display.bindtags()))
		self.add_event_indicator()


class SessionCell(TimetableCell):
	def __init__(self, root, master, day: int, session: int, class_data_idx: int) -> None:
		self.name = root.classes[class_data_idx]
		self.room = root.rooms[class_data_idx]
		self.teacher = root.teachers[class_data_idx]

		super().__init__(root, master, day, session, class_data_idx)

		self.name_display = tk.Label(self.frame, textvariable=self.name, relief='flat', wraplength=100, font=('Calibri', 12, 'bold'), background='#303841', foreground='#D8DEE9')
		self.name_display.grid(row=0, column=0, padx=1, pady=1, sticky='NSWE')
		self.name_display.bindtags((f'click:{id(self)}', *self.name_display.bindtags()))

		self.room_display = tk.Label(self.frame, textvariable=self.room, relief='flat', font=('Calibri', 12), background='#303841', foreground='#D8DEE9')
		self.room_display.grid(row=1, column=0, padx=1, pady=(0, 1), sticky='NSWE')
		self.room_display.bindtags((f'click:{id(self)}', *self.room_display.bindtags()))

		self.teacher_display = tk.Label(self.frame, textvariable=self.teacher, relief='flat', font=('Calibri', 12), background='#303841', foreground='#D8DEE9')
		self.teacher_display.grid(row=2, column=0, padx=1, pady=(0, 1), sticky='NSWE')
		self.teacher_display.bindtags((f'click:{id(self)}', *self.teacher_display.bindtags()))

		self.add_event_indicator()

	def update_sessiondata(self) -> None:
		if self.class_data_idx is None:
			self.name = None
			self.room = None
			self.teacher = None

			self.name_display.configure(textvariable=self.root.null_text_variable)
			self.teacher_display.configure(textvariable=self.root.null_text_variable)
			self.room_display.configure(textvariable=self.root.null_text_variable)
		else:
			self.name = self.root.classes[self.class_data_idx]
			self.room = self.root.rooms[self.class_data_idx]
			self.teacher = self.root.teachers[self.class_data_idx]

			self.name_display.configure(textvariable=self.name)
			self.teacher_display.configure(textvariable=self.teacher)
			self.room_display.configure(textvariable=self.room)


class TimeTable:
	def __init__(self, master, classes: list[str], teachers: list[str], rooms: list[str], timetable_data: Any, event_data: list[dict], day_start_time, sessions, start_date) -> None:
		self.master: Window = master
		self.classname_str = classes

		self.data = timetable_data
		self.events = list(map(lambda v: Event(*list(v.values())), event_data))

		self.active_cell: Optional[WeekendCell | SessionCell] = None

		self.start_timestamp = start_date

		self.week = self.get_week(datetime.datetime.now().timestamp())
		self.day_start_time = day_start_time

		self.sessions, self.sessiontimes = self.get_sessiontimes(sessions)

		self.session = 0
		self.day = 0

		self.cell_state_config = {
			'normal': ({'background': '#303841', 'foreground': '#D8DEE9'}, '#3B434C'),
			'active': ({'background': '#4F565E', 'foreground': '#D4D6D7'}, '#62686F'),
			'highlighted': ({'background': '#343C44', 'foreground': '#D4D6D7'}, '#3B434C')
		}
		self.active_header_config = {'background': '#8C3841', 'foreground': '#D4D6D7', 'font': ('Calibri', 13, 'bold'), 'highlightbackground': '#963D49'}
		self.inactive_header_config = {'background': '#424D59', 'foreground': '#D4D6D7', 'font': ('Calibri', 13), 'highlightbackground': '#4F565E'}

		self.event_types = ['Event', 'Info', 'Reminder', 'Bookmark', 'Assignment', 'Test']

		self.display_frame = tk.Frame(master, background='#222')
		self.display_frame.columnconfigure(1, weight=1)
		self.display_frame.rowconfigure(0, weight=1)

		self.classes = list(map(lambda v: tk.StringVar(self.display_frame, v), classes))
		self.teachers = list(map(lambda v: tk.StringVar(self.display_frame, v), teachers))
		self.rooms = list(map(lambda v: tk.StringVar(self.display_frame, v), rooms))

		for n, i in enumerate(zip(self.classes, self.teachers, self.rooms)):
			i[0].trace('w', lambda a, b, c, idx=n: self.edit_class_names(idx))
			i[1].trace('w', lambda a, b, c: self.check_saved(self.get_json()))
			i[2].trace('w', lambda a, b, c: self.check_saved(self.get_json()))

		frame = tk.Frame(self.display_frame, background='#222')
		frame.grid(row=0, column=0, sticky='NSWE', padx=(1, 2))
		frame.columnconfigure(0, weight=1)
		frame.rowconfigure(1, weight=1)

		tk.Label(frame, background='#303841', borderwidth=0, relief='flat', foreground='#D8DEE9', font=('Calibri', 12, 'bold'), text='Week', highlightthickness=1, highlightbackground='#3B434C').grid(row=0, columnspan=2, column=0, sticky='nswe', pady=(1, 0))

		self.week_slider = tk.Scale(frame, orient='vertical', resolution=1, command=self.update_week, from_=0, to=11, borderwidth=0, relief='flat', border=0, showvalue=False, sliderlength=50, sliderrelief='flat', width=10, troughcolor='#444B53', highlightthickness=0, background='#696F75', activebackground='#858C93')
		self.week_slider.grid(row=1, column=0, sticky='ns', padx=(0, 1), pady=(1, 1), rowspan=12)

		self.weekframe = tk.Frame(frame, background='#222')
		self.weekframe.grid(row=1, column=1, sticky='NSWE', pady=(0, 0))
		self.weekframe.rowconfigure(list(range(12)), weight=1)
		self.weekframe.columnconfigure(1, weight=1, minsize=133)
		self.week_elems = []

		for i in range(12):
			frame = WeekFrame(self, i, self.weekframe, background='#303841', highlightbackground='#3B434C', highlightthickness=1)
			frame.grid(row=i, column=1, sticky='nswe', padx=(0, 0), pady=(int(i == 0), 1))
			self.week_elems.append(frame)

		## ==================================

		self.display_frame.columnconfigure(2, minsize=352)

		self.sidebar = tk.Frame(self.display_frame, background='#222', width=352)
		self.sidebar.grid(column=2, row=0, sticky='NSWE')
		self.sidebar.rowconfigure(11, weight=1)
		self.sidebar.columnconfigure(0, weight=1)

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

		self.save_button = ttk.Button(self.buttonframe, text='', style='symbol.stipple.TButton', command=lambda: self.save_events(), width=1, state='disabled')
		self.save_button.grid(row=0, column=1, padx=(0, 1), pady=(0, 1), sticky='nswe')

		tk.Frame(self.buttonframe, background='#222', width=10).grid(row=0, column=2, sticky='nswe')

		self.delete_button = ttk.Button(self.buttonframe, text='', style='symbol.stipple.TButton', state='disabled', command=lambda: self.delete_event(False), width=1)
		self.delete_button.grid(row=0, column=3, padx=(1, 1), pady=(0, 1), sticky='nswe')

		self.pause_text_event = False

		tk.Frame(self.buttonframe, background='#222').grid(row=0, column=4, sticky='nswe')

		tk.Label(self.buttonframe, background='#424D59', foreground='#D8DEE9', font=('Calibri', 12), text='Type', width=5).grid(row=0, column=5, padx=(1, 1), pady=(0, 1), sticky='nswe')

		self.event_type_combobox = ttk.Combobox(self.buttonframe, style='Custom.TCombobox', background='#303841', foreground='#D8DEE9', values=self.event_types, state='disabled')
		self.event_type_combobox.grid(row=0, column=6, sticky='nswe', padx=(0, 1), pady=(0, 1))
		self.event_type_combobox.bind('<<ComboboxSelected>>', lambda v: self.edit_event_type())
		self.tt_elements: list[list[SessionCell | WeekendCell]] = []

		## Spacer
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

		self.table_frame = tk.Frame(self.display_frame, background='#222')
		self.table_frame.grid(column=1, row=0, sticky='NSWE')
		self.table_frame.columnconfigure(list(range(1, 8)), weight=1)
		self.table_frame.rowconfigure(list(range(1, len(self.sessions))), weight=1)

		self.dotw_headers = []
		self.active_dotw_header = None

		for n, dotw in enumerate(['Mon', 'Tue', 'Wed', 'Thr', 'Fri', 'Sat', 'Sun']):
			header = tk.Label(self.table_frame, text=dotw, background='#424D59', foreground='#D4D6D7', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Calibri', 13), image=master.pixel, compound='center', height=19)
			header.grid(row=0, column=n + 1, sticky='NSWE', padx=(int(n == 0), 1), pady=(1, 0))
			self.dotw_headers.append(header)

		self.session_headers = []
		self.active_session_header = None

		self.session_break_idxs = [[], []]

		for n, session_data in enumerate(self.sessions):
			name, is_normal = session_data

			header = tk.Label(self.table_frame, text=name, background='#424D59' if is_normal else '#303841', foreground='#D4D6D7' if is_normal else '#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Calibri', 13), image=master.pixel, compound='center', width=15, height=19)
			header.grid(row=n + 1, column=0, columns=1 if is_normal else 6, sticky='NSWE', padx=(1, int(not is_normal)), pady=(int(n == 0), 1))
			if is_normal:
				self.session_headers.append(header)
			else:
				self.session_break_idxs[0].append(n)
				self.session_break_idxs[1].append(n - len(self.session_break_idxs[0]))
				self.table_frame.rowconfigure(n + 1, weight=0)

		for daynum, sessions in enumerate(self.data):
			self.tt_elements.append([])
			for sessionnum, ttclass in enumerate(sessions):
				cell = SessionCell(self, self.table_frame, daynum, sessionnum, ttclass)
				self.tt_elements[-1].append(cell)
				cell.grid()

		for i in range(2):
			cell = WeekendCell(self, self.table_frame, i)
			self.tt_elements.append([cell])
			cell.grid()

		self.current_session_marker = tk.Frame(self.table_frame, background='#8C3841', highlightthickness=1, highlightbackground='#969CA3')
		self.current_session_marker.bind('<Button-1>', lambda v: self.select(self.day, self.session))
		pywinstyles.set_opacity(self.current_session_marker.winfo_id(), 0.2)
		self.update_current_session()

		self.week_slider.set(self.week)

		self.empty_text_variable = tk.StringVar(self.display_frame, '')
		self.null_text_variable = tk.StringVar(self.display_frame, '<Null>')

		self.current_savefile_contents = None
		self.events_saved = True

		self.formatting_update_after = None

	def change_week(self) -> None:
		self.start_timestamp = self.master.get_start_week(allow_cancel=True)
		self.week = self.get_week(datetime.datetime.now().timestamp())
		self.update_week(self.week)

	def get_sessiontimes(self, data: list[list[str, str, str]]) -> tuple[list[list[str, str]], list[list[int]]]:
		session_times = [list(map(int, self.day_start_time.split(':')))]
		for idx, time in enumerate(swapaxes(data)[2]):
			if time == '-1':
				session_times.append([-1, -1])
			else:
				t = list(map(int, time.split(':')))
				session_times.append(t)

		return swapaxes(swapaxes(data)[:2]), session_times

	def get_week(self, now: float) -> int:
		print(datetime.datetime.fromtimestamp(self.start_timestamp), 'start')
		return int((now - self.start_timestamp) // (86400 * 7))

	def validate_session(self, now: datetime.datetime, h1: int, m1: int, h2: int, m2: int) -> int:
		if h2 == -1 and m2 == -1:
			return now.hour > h1 or now.hour == h1 and now.minute > m2
		elif h1 == h2:
			return now.hour == h1 and m1 <= now.minute <= m2
		else:
			return (now.hour == h1 and now.minute >= m1) or (now.hour == h2 and now.minute < m2)

	def get_session(self, now: datetime.datetime) -> Optional[int]:
		session_index = list(map(lambda v, n=now: self.validate_session(n, *v), zip(*swapaxes(self.sessiontimes[:-1]), *swapaxes(self.sessiontimes[1:]))))

		if True not in session_index:
			if now.hour > 14 or (now.hour == 45 and now.minute > 45):
				return 10
			else:
				return None

		else:
			return session_index.index(True)

	def update_list_format(self) -> None:
		tags = self.event_entry.tag_ranges('sel')
		print(tags)

		if not tags:
			positions = [[int(self.event_entry.index(tk.INSERT).split('.')[0])] * 2]
		else:
			positions = [[int(str(a).split('.')[0]), int(str(b).split('.')[0])] for a, b in zip(tags[:-1:2], tags[1::2])]

		for pos in positions:
			lines = self.event_entry.get(f'{pos[0]}.0', f'{pos[1]}.end').split('\n')
			indent = self.event_entry.check_indent(line=lines[0])
			if indent is None:
				numbering_loc = [0, 1]
				indent = ' \t'
			else:
				numbering_loc = re.match(rf'[^ \t]+', indent)
				if numbering_loc is None:
					numbering_loc = [len(indent) - 1] * 2
				else:
					numbering_loc = numbering_loc.span()

			new_lines = []
			maxlen = None

			for ln, line in list(enumerate(lines))[::-1]:
				numbering = ''
				line_indent = self.event_entry.check_indent(line=line)
				if line_indent is None:
					line_indent = ''

				match self.numbering_format.get():
					case 0:
						numbering = ''
					case 1:
						numbering = '•'
					case 2:
						numbering = str(ln + 1) + '.'
					case 3:
						numbering = []
						val = ln + 1
						while val > 0:
							print(val % 26, val // 26)
							numbering.append(chr(ord('a') + (val % 26) - 1))
							val //= 26
						numbering = ''.join(numbering[::-1]) + ')'

				if maxlen is None:
					maxlen = len(numbering)
				new_line = list(indent)
				new_line[slice(*numbering_loc)] = list(numbering.rjust(maxlen))
				new_lines.append(''.join(new_line) + line.removeprefix(line_indent))
				print(line)

			print(new_lines)
			self.event_entry.replace(f'{pos[0]}.0', f'{pos[1]}.end', '\n'.join(new_lines[::-1]))
			self.event_entry.tag_add('sel', f'{pos[0]}.0', f'{pos[1]}.end')

	def on_edit(self, skip_after: bool = False) -> None:
		cursor_position = self.event_entry.index(tk.INSERT).split('.')[0]
		tags = self.event_entry.tag_names(cursor_position + '.0')
		print(tags)
		list_mode = ['DOTPOINT' in tags, 'NUMBERING' in tags, 'LETTERING' in tags]
		if any(list_mode):
			self.numbering_format.set(list_mode.index(True) + 1)
		else:
			self.numbering_format.set(0)
			## The colouriser in the IndentText widget creates a 'TO​DO' tag, for updating colouration data on the next frame when the contents of the text widget are changed.
			## This code detects that tag and updates the formatting.
			if 'TODO' in tags and not skip_after:
				if self.formatting_update_after is not None:
					self.event_entry.after_cancel(self.formatting_update_after)
				self.formatting_update_after = self.event_entry.after(2, lambda: self.on_edit(True))

	def select(self, day: int, session: int) -> None:
		if day is not None and session is not None:
			self.tt_elements[day][session].toggle_selected()

	def update_current_session(self) -> None:
		now = datetime.datetime.now()
		d = now.weekday()
		self.day = d
		if d > 4:
			self.session = 0
			s = 0
		else:
			s = self.get_session(now)

			if s in self.session_break_idxs[0]:
				self.session = None
			else:
				self.session = s - sum(map(lambda v: s > v, self.session_break_idxs[0]))

		if self.active_dotw_header is not None:
			self.dotw_headers[self.active_dotw_header].configure(**self.inactive_header_config)

		if self.week == self.get_week(now.timestamp()):
			self.active_dotw_header = self.session
			self.dotw_headers[self.day].configure(**self.active_header_config)
		else:
			self.active_dotw_header = None

		if self.active_session_header is not None:
			self.session_headers[self.active_session_header].configure(**self.inactive_header_config)

		if self.session is not None and self.week == self.get_week(now.timestamp()):
			self.active_session_header = self.session
			self.session_headers[self.session].configure(**self.active_header_config)
		else:
			self.active_session_header = None

		if s is not None:
			self.current_session_marker.grid_configure(row=s + 1, column=self.day + 1, sticky='NSWE', padx=(int(self.day == 0), 1), pady=(int(s == 0), 1), rows=len(self.sessions) if self.day > 4 else 1)
		else:
			self.current_session_marker.grid_remove()

	def save_as(self) -> None:
		name = fd.asksaveasfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.master.filename), confirmoverwrite=True, initialfile=self.master.filename, parent=self.master)
		if name:
			self.master.filename = name
			self.master.top_bar.filename_display.configure(text=name)
			self.master.settings.update({'default.path': name})
			self.save_events()

	def save_copy(self) -> None:
		name = fd.asksaveasfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.master.filename), confirmoverwrite=True, initialfile=self.master.filename, parent=self.master)
		if name:
			self.save_events(name)

	def save_events(self, filename: Optional[str] = None, encoding: str = 'utf-8') -> None:
		if filename is None:
			filename = self.master.filename
		json_data = self.get_json()
		try:
			with open(filename, 'w', encoding=encoding) as writefile:
				writefile.write(json_data)
			self.master.display_popup('Saved Successfully')
			self.current_savefile_contents = multireplace(json_data, {'\n': '', '    ': '', '\t': ''})
			self.events_saved = True
			self.update_save_buttons()
		except PermissionError:
			self.master.display_popup('Could not save: Permission Denied')

	def update_save_buttons(self) -> None:
		state = 'disabled' if self.events_saved else 'normal'
		self.saveas_button.configure(state=state)
		self.save_button.configure(state=state)

	def check_saved(self, json_data: str) -> bool:
		if self.current_savefile_contents is None:
			with open(self.master.filename, encoding='utf-8') as file:
				self.current_savefile_contents = multireplace(''.join(file.readlines()), {'\n': '', '    ': '', '\t': ''})

		print(multireplace(json_data, {'\n': '', '    ': '', '\t': ''}))
		print(self.current_savefile_contents)
		self.events_saved = multireplace(json_data, {'\n': '', '    ': '', '\t': ''}) == self.current_savefile_contents
		self.update_save_buttons()
		return self.events_saved

	def edit_event_type(self) -> None:
		self.check_saved(self.get_json())
		self.week_elems[self.week].edit_event_type(self.active_cell.current_event)

		if self.active_cell is not None and self.active_cell.current_event is not None:
			self.active_cell.events_indicator.configure(image=self.master.icons[self.active_cell.current_event.event_type.get()])

	def update_week(self, value: str | int) -> None:
		events = list(filter(lambda v: v.week in [int(value), self.week], self.events))
		self.week_elems[self.week].numlabel.configure(font=('Arial', 11))
		self.week_elems[int(value)].numlabel.configure(font=('Arial', 11, 'bold'))
		self.week = int(value)
		for event in events:
			cell = self.tt_elements[event.day][event.session]
			cell.update_event()

		if self.week != self.get_week(datetime.datetime.now().timestamp()):
			if self.current_session_marker.grid_info():
				self.current_session_marker.grid_remove()
				if self.session is not None:
					self.session_headers[self.session].configure(**self.inactive_header_config)
				if self.day is not None:
					self.dotw_headers[self.day].configure(**self.inactive_header_config)

		else:
			if not self.current_session_marker.grid_info():
				self.current_session_marker.grid()
				if self.session is not None:
					self.session_headers[self.session].configure(**self.active_header_config)
				if self.day is not None:
					self.dotw_headers[self.day].configure(**self.active_header_config)

	def create_event(self) -> None:
		if self.active_cell is not None:
			event = Event(self.week, self.active_cell.day, self.active_cell.session, '', None, 'Event')
			self.events.append(event)
			self.active_cell.set_event(event)
			self.update_active_event()
			self.event_entry.focus_set()
			self.check_saved(self.get_json())
			self.week_elems[self.week].add_event(event)

	def grid(self, *args: tuple[Any], **kwargs: Any) -> None:
		self.display_frame.grid(*args, **kwargs)

	def _proxy(self, *args: tuple[Any]) -> Any:
		""" Called whenever an event occurs in the element. Raises an '<<Edit>>' event when the text is edited. """
		cmd = (self.event_entry._orig,) + args
		try:
			result = self.event_entry.tk.call(cmd)
		except tk.TclError:
			result = None

		if args[0] in ('insert', 'replace', 'delete'):
			self.event_entry.event_generate('<<Edit>>', when='tail')

		if args[0:3] == ('mark', 'set', 'insert'):
			self.event_entry.event_generate('<<Change>>', when='tail')

		return result

	def delete_event(self, confirm: bool = True) -> None:
		if confirm and mb.askokcancel('Delete Event?', 'Do you really want to delete all events on the selected session?') is not True:
			return

		if self.active_cell is not None and self.active_cell.current_event is not None:
			event = self.active_cell.current_event
			self.events.remove(event)
			self.week_elems[self.week].remove_event(event)
			self.active_cell.set_event(None)
			self.update_active_event()
			self.check_saved(self.get_json())

	def get_json(self) -> str:
		classes = list(map(lambda v: v.get(), self.classes))
		rooms = list(map(lambda v: v.get(), self.rooms))
		teachers = list(map(lambda v: v.get(), self.teachers))

		buffer = (
			'{\n'
			f'    "classes": {classes},\n'
			f'    "teachers": {teachers},\n'
			f'    "rooms": {rooms},\n'
			'    "timetable": [\n'
		)

		for i in self.data:
			buffer += f'        {i},\n'
		buffer = buffer[:-2] + '\n    ],\n    "events": ['
		for num, event in enumerate(self.events):
			buffer += ',' if buffer[-1] == '}' else ''
			event_data = []
			for k, v in event.get_data().items():
				event_data.append(f'"{k}": {v}')
			buffer += f'\n        {{\n            ' + ',\n            '.join(event_data) + '\n        }'
		buffer = buffer.replace("'", '"') + '\n    ],\n    "sessions": [\n'
		session_data = []
		for session, time in zip(self.sessions, self.sessiontimes[1:]):
			session_data.append(f'        ["{session[0]}", {"true" if session[1] else "false"}, "' + (f'{time[0]:>02n}:{time[1]:<02n}' if time[0] != -1 else '-1') + '"]')
		buffer += ',\n'.join(session_data)
		buffer += f'\n    ],\n    "day_start": "{self.day_start_time}",\n    "start_date_timestamp": {self.start_timestamp}\n}}'
		return buffer

	def save_event(self) -> None:
		if self.active_cell is not None and self.active_cell.current_event is not None:
			self.active_cell.current_event.text = self.event_entry.get(1.0, tk.END).strip('\n')

			self.active_cell.update_event()

	def update_button_states(self) -> None:
		if self.active_cell is not None and self.active_cell.current_event is not None:
			self.active_cell.current_event.text = self.event_entry.get(1.0, tk.END).strip('\n')
		if self.pause_text_event:
			self.pause_text_event = False
		else:
			if self.event_entry.get(1.0, tk.END).strip('\n') != self.active_cell.current_event.text.strip('\n'):
				self.events_saved = False
			else:
				self.check_saved(self.get_json())

	def edit_class_names(self, idx: int) -> None:
		values = [v.get() for v in self.classes]
		self.class_name_combobox.set(values[idx])
		self.class_name_combobox.configure(values=values)
		self.check_saved(self.get_json())

	def new_class(self) -> None:
		idx = len(self.classname_str)
		self.active_cell.class_data_idx = idx
		self.classname_str.append(f'<Class-{idx}>')
		self.classes.append(tk.StringVar(self.master, f'<Class-{idx}>'))
		self.classes[-1].trace('w', lambda a, b, c, n=idx: self.edit_class_names(n))

		self.class_name_combobox.current(idx)
		self.teachers.append(tk.StringVar(self.master, ''))
		self.rooms.append(tk.StringVar(self.master, ''))
		self.active_cell.update_sessiondata()

		self.check_saved(self.get_json())

	def delete_class(self, confirm: bool = True) -> None:
		if confirm and mb.askokcancel('Delete Class?', 'Do you really want to delete all instances of this class?') is not True:
			return
		idx = self.active_cell.class_data_idx
		for row in self.tt_elements:
			for elem in row:
				if elem.class_data_idx == idx:
					elem.class_data_idx = None
					elem.update_sessiondata()
		self.class_name_combobox.set('')
		self.check_saved(self.get_json())

	def edit_class(self) -> None:
		idx = self.class_name_combobox.current()
		if idx == -1:
			self.class_name_combobox.current(self.active_cell.class_data_idx)
		else:
			self.active_cell.class_data_idx = self.class_name_combobox.current()
			self.active_cell.update_sessiondata()
		self.check_saved(self.get_json())

	def update_active_event(self) -> None:
		print('update event', self.active_cell)
		if self.active_cell is None or self.active_cell.weekend:
			self.name_entry.configure(textvariable=self.empty_text_variable, state='disabled')
			self.teacher_entry.configure(textvariable=self.empty_text_variable, state='disabled')
			self.room_entry.configure(textvariable=self.empty_text_variable, state='disabled')
			self.delete_class_button.configure(state='disabled')
			self.class_name_combobox.configure(state='disabled')
			self.class_name_combobox.set('')
		else:
			self.name_entry.configure(textvariable=self.active_cell.name, state='normal')
			self.teacher_entry.configure(textvariable=self.active_cell.teacher, state='normal')
			self.room_entry.configure(textvariable=self.active_cell.room, state='normal')
			self.class_name_combobox.configure(state='readonly')
			self.class_name_combobox.current(self.active_cell.class_data_idx)

			if self.active_cell.class_data_idx is None:
				self.delete_class_button.configure(state='disabled')
			else:
				self.delete_class_button.configure(state='normal')

		if self.active_cell is None or self.active_cell.current_event is None:
			if not self.event_info_label.grid_info():
				self.event_info_label.grid()

			if self.active_cell is not None:
				self.event_info_label.configure(text='No Events\n(click to create)')
			else:
				self.event_info_label.configure(text='No Selection')

			self.delete_button.configure(state='disabled')
			self.event_type_combobox.configure(state='disabled', textvariable=self.empty_text_variable)
			self.event_type_combobox.set('')
		else:
			if self.event_info_label.grid_info():
				self.event_info_label.grid_remove()
			self.event_info_label.configure(text='1 Event')
			self.event_entry.configure()
			self.event_entry.delete(1.0, tk.END)
			self.event_entry.insert(1.0, self.active_cell.current_event.text)
			self.delete_button.configure(state='normal')
			self.event_type_combobox.configure(state='normal', textvariable=self.active_cell.current_event.event_type)

			self.pause_text_event = True

	def __exit__(self, exc_type, exc_val, exc_tb) -> None:
		self.display_frame.destroy()
		del self

	def destroy(self) -> None:
		self.__exit__(None, None, None)


class Window(tk.Tk):
	def __init__(self, file_checks, *args: Any, **kwargs: Any):
		super().__init__(*args, **kwargs)

		self.focus()
		self.title(f'Timetable V{VERSION}')

		self.pixel = tk.PhotoImage(width=1, height=1)

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

		if any(file_checks[:3]) or any(file_checks[-3:]):
			self.filename = 'tempfile.json'
			with open(self.filename, 'w', encoding='utf-8') as template_file:
				template_file.write(TIMETABLE_JSON_TEMPLATE % int(datetime.datetime.now().timestamp()))

		if any(file_checks[:3]):
			self.settings = DEFAULT_SETTINGS
			self.settings.update({'default.path': self.filename})
		else:
			with open('settings.json', encoding='utf-8') as settingsfile:
				self.settings = json.load(settingsfile)
			if not any(file_checks[-3:]):
				self.filename = self.settings['default.path']
			else:
				self.settings.update({'default.path': self.filename})

		if any(file_checks[3:6]):
			self.window_settings = DEFAULT_WINDOW_SETTINGS
		else:
			with open('window_settings.json', encoding='utf-8') as winsettingsfile:
				self.window_settings = json.load(winsettingsfile)

		self.call('wm', 'iconphoto', str(self), self.icons['window_icon2'])
		self.tk.call('tk', 'scaling', self.settings['ui_scaling'])

		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, weight=1)

		timetable_data = read_timetable(self.filename)
		if timetable_data is None:  # This shouldn't be able to happen any more thanks to the file validation
			pass

		self.top_bar = WindowTopbar(self, background='#000')
		self.top_bar.grid(row=0, column=0, sticky='nswe')

		# self.timetable = TimeTable(self, *timetable_data)
		# self.timetable.grid(row=1, column=0, sticky='nswe')

		self.protocol('WM_DELETE_WINDOW', lambda: self.close_handler())

		self.style = ttk.Style()
		self.style.theme_use('default')

		self.geometry(self.window_settings['window.geometry'])
		self.state(self.window_settings['window.state'])

		self.manager = ci.CIManager(self, self.style)
		self.manager.load_dir('icons')

		self.option_add('*TCombobox*Listbox.background', '#303841')
		self.option_add('*TCombobox*Listbox.foreground', '#D8DEE9')
		self.option_add('*TCombobox*Listbox.selectBackground', '#424D59')
		self.option_add('*TCombobox*Listbox.selectForeground', '#D8DEE9')

		self.style.configure('TCombobox.Vertical.TScrollbar', background='#696F75', troughcolor='#444B53', relief='flat', troughrelief='flat', arrowcolor='#B8BBBE')
		self.style.configure('TCombobox', background='#424D59', fieldbackground='#2E3238', highlightthickness=1, highlightbackground='#4F565E', insertwidth=2, insertcolor='#F9AE58', borderwidth=0, relief='flat', arrowcolor='#B8BBBE', foreground='#D8DEE9', font=('Calibri', 13), padding=(2, 5, 2, 5))
		self.style.map('TCombobox', background=[('pressed', '#5E6E7F'), ('active', '#46525C'), ('disabled', '#424D59')], foreground=[('!disabled', '#D8DEE9'), ('disabled', '#BFC5D0')], fieldbackground=[('!disabled', '#2E3238'), ('disabled', '#424D59')])

		print(self.style.layout('Custom.TSpinbox'))

		self.style.configure('Custom.TSpinbox', background='#424D59', fieldbackground='#2E3238', highlightthickness=1, highlightbackground='#4F565E', insertwidth=2, insertcolor='#F9AE58', borderwidth=0, relief='flat', arrowcolor='#B8BBBE', foreground='#D8DEE9', font=('Calibri', 13), padding=(2, 5, 2, 5), arrowsize=12)
		self.style.map('Custom.TSpinbox', background=[('pressed', '#5E6E7F'), ('active', '#46525C'), ('disabled', '#424D59')], foreground=[('!disabled', '#D8DEE9'), ('disabled', '#BFC5D0')], fieldbackground=[('!disabled', '#2E3238'), ('disabled', '#424D59')])

		self.style.configure('stipple.TButton', background='#303841', foreground='#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', bordercolor='#f00', borderwidth=0, relief='flat', activeforeground='#D4D6D7', activebackground='#303841', disabledforeground='#BFC5D0', padding=(0, 0, 0, 0), shiftrelief=1, anchor='center')
		self.style.map('stipple.TButton', background=[('pressed', '#5E6E7F'), ('active', '#3B434C')], foreground=[('pressed', '#C0C5CE'), ('active', '#C0C5CE'), ('!active', '#D8DEE9'), ('disabled', '#A8AEB7')])

		self.style.configure('symbol.stipple.TButton', font=('Segoe UI Symbol', 11), padding=(2, 4, 0, 0))
		self.style.configure('text.stipple.TButton', font=('Calibri', 12))

		buttonlayout = self.manager.create_layout('stipple.TButton', [('Button.border', {'sticky': 'nswe', 'border': '1', 'children': [('Button.padding', {'sticky': 'nswe', 'children': [('Button.label', {'sticky': 'nswe'})]})]})])

		buttonlayout.add('Button.button', 0, 'Button.border', sticky='nswe')
		self.manager.map('stipple.TButton', 'Button.button', {'default': 'blank', '!disabled': 'blank', 'disabled': 'stipple'}, inherit=False)

		self.manager.map('stipple.TEntry', 'Entry.field', {'default': 'blank', '!disabled': 'blank', 'disabled': 'stipple'}, inherit=False)
		self.style.configure('stipple.TEntry', font=('Calibri', 13), background='#2E3238', activebackground='#2E3238', selectrelief='flat', foreground='#D8DEE9', borderwidth=0, insertbackground='#F9AE58', insertcolor='#ff0', relief='flat', padding=(2, -1, 2, -1))
		self.style.map('stipple.TEntry', background=[('disabled', '#2E3238'), ('!disabled', '#2E3238')])

		self.style.configure('TScrollbar', width=7, arrowcolor='#B8BBBE', background='#696F75', troughcolor='#444B53', relief='flat', troughrelief='flat')
		self.style.map('TScrollbar', background=[('active', '#858C93')])
		self.style.layout('Custom.Vertical.TScrollbar', [('Vertical.Scrollbar.trough', {'sticky': 'ns', 'children': [('Vertical.Scrollbar.thumb', {'unit': '1', 'sticky': 'nswe', 'children': [('Vertical.Scrollbar.grip', {'sticky': ''})]})]})])

		self.style.configure('Custom.TCombobox', background='#424D59', fieldbackground='#303841', highlightthickness=1, highlightbackground='#4F565E', insertwidth=2, insertcolor='#F9AE58', borderwidth=0, relief='flat', arrowcolor='#B8BBBE', foreground='#D8DEE9', font=('Calibri', 12))
		self.style.map('Custom.TCombobox', background=[('active', '#46525C'), ('disabled', '#424D59')], foreground=[('!disabled', '#D8DEE9'), ('disabled', '#BFC5D0')], fieldbackground=[('!disabled', '#303841'), ('disabled', '#424D59')])
		self.popup_elem = None
		self.popup_after = None
		self.x = None
		self.y = None

	def undo(self) -> None:
		self.timetable.event_entry.edit_undo()

	def redo(self) -> None:
		self.timetable.event_entry.edit_redo()

	def save_timetable_as(self) -> None:
		self.timetable.save_as()

	def save_timetable_copy(self) -> None:
		self.timetable.save_copy()

	def save_timetable(self) -> None:
		self.timetable.save_events()

	def load_timetable(self, filename: Optional[str] = None) -> None:
		if filename is None:
			filename = fd.askopenfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.filename), initialfile=self.filename, parent=self)
		if not file_exists(filename):
			return

		self.filename = filename
		self.top_bar.filename_display.configure(text=filename)
		self.settings.update({'default.path': filename})
		self.timetable.destroy()
		timetable_data = read_timetable(filename)
		self.timetable = TimeTable(self, *timetable_data)
		self.timetable.grid(row=1, column=0, sticky='nswe')
		self.update_idletasks()
		self.wm_minsize(window.timetable.display_frame.winfo_width() - 47, window.timetable.display_frame.winfo_height() + window.top_bar.winfo_height() - 34)

	def export_timetable(self, mode: Literal['xls', 'csv', 'pdf']) -> None:
		"""
		Export the current timetable as a csv/xls/pdf file
		"""
		## todo: implement
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.')

	def undo_all(self) -> None:
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.')

	def show_about(self) -> None:
		tl = tk.Toplevel(self, background='#303841')
		tl.attributes('-topmost', True)
		tl.resizable(False, False)
		tl.title('About')
		self.call('wm', 'iconphoto', str(tl), self.icons['window_icon2'])
		tl.columnconfigure(0, weight=1)
		tl.rowconfigure(0, weight=1)

		tk.Label(tl, text=about_info, background='#303841', foreground='#D8DEE9', highlightthickness=1, highlightbackground='#4F565E', borderwidth=0, font=('Jetbrains Mono Light', 13), anchor='w', justify='left', image=self.pixel, compound='center').grid(sticky='nswe')

	def show_help(self) -> None:
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.\n\n(No help is coming)')

	def report_bug(self) -> None:
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.\n\n(My code is perfect and any issues are 100% your own fault)')

	def report_feature(self) -> None:
		mb.showinfo('Not Implemented', 'This feature has not been implemented yet.')

	def show_settings(self) -> None:
		SettingsWindow(self, background='#303841')

	def get_start_week(self, week: Optional[int] = None, allow_cancel: bool = False) -> int | None:
		if week is None:
			week = sd.askinteger('Setup', 'Enter the current week:', initialvalue=1, minvalue=1, maxvalue=11)
			print(week)
			if week is None:
				if allow_cancel:
					return
				week = 0
			else:
				week -= 1
		current_time = datetime.datetime.now()

		## Remove HH:MM:SS:ms
		start_timestamp = int(current_time.timestamp()) - current_time.hour * 3600 - current_time.minute * 60 - current_time.second
		## Remove days since term began
		start_timestamp -= (week * 7 + current_time.weekday()) * 86400
		return start_timestamp

	def new_timetable(self) -> None:
		## Todo: add delete to indent text keypress manager

		filename = fd.asksaveasfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.filename), confirmoverwrite=True, initialfile=self.filename, parent=self)
		if not filename:
			return
		self.filename = filename
		self.top_bar.filename_display.configure(text=filename)
		self.settings.update({'default.path': filename})
		week = sd.askinteger('Setup', 'Enter the current week:', initialvalue=1, minvalue=1, maxvalue=11)
		if week is None:
			return
		else:
			week -= 1

		with open(filename, 'w', encoding='utf-8') as file:
			file.writelines(TIMETABLE_JSON_TEMPLATE % self.get_start_week(week))
		timetable_data = read_timetable(filename)
		if timetable_data is None:
			return
		self.timetable.destroy()
		self.timetable = TimeTable(self, *timetable_data)
		self.timetable.grid(row=1, column=0, sticky='nswe')
		self.update_idletasks()
		size = (window.timetable.display_frame.winfo_width() - 47, window.timetable.display_frame.winfo_height() + window.top_bar.winfo_height() - 34)
		self.wm_minsize(*size)

	def close_handler(self) -> None:
		try:
			if not self.timetable.check_saved(self.timetable.get_json()):
				ans = mb.askyesnocancel('Unsaved Data', 'Do you want to save your changes to this timetable?')
				if ans is None:
					return
				elif ans:
					self.timetable.save_events()

			json_object = json.dumps({'window.geometry': self.winfo_geometry(), 'window.state': self.state()}, indent=4, separators=(', ', ': '))
			with open('window_settings.json', 'w', encoding='utf-8') as file:
				file.write(json_object)

			json_object = json.dumps(self.settings, indent=4, separators=(', ', ': '))
			with open('settings.json', 'w', encoding='utf-8') as file:
				file.write(json_object)
		except Exception:  # Catch all exceptions with a broad exception clause, otherwise the program may get 'stuck open'
			mb.showerror('Failed to Save', f'An error occurred while attempting to close.\nAs a result, some data may be unsaved.\n\n{sys.exc_info()[1]}\n{sys.exc_info()[2]}\n\n{format_exc()}')

		self.destroy()

	def display_popup(self, text: str, ms: int = 2000) -> None:
		if self.popup_elem is not None:
			self.popup_elem.destroy()
			self.after_cancel(self.popup_after)

		self.popup_elem = tk.Frame(self, background='#3B434C')
		self.popup_elem.columnconfigure(0, weight=1)
		self.popup_elem.place(x=self.winfo_width() // 2 - 100, y=self.winfo_height() - 35, width=200)

		tk.Label(self.popup_elem, text=text, relief='flat', font=('Calibri', 11), background='#303841', foreground='#D8DEE9', image=self.pixel, compound='center', height=15, anchor='w').grid(row=0, column=0, sticky='nswe', padx=1, pady=1)
		tk.Button(self.popup_elem, text='', relief='flat', font=('Segoe UI Symbol', 9), background='#4F565E', foreground='#D8DEE9', image=self.pixel, compound='center', width=15, height=15, command=lambda: self.remove_popup(), activebackground='#303841', activeforeground='#D4D6D7', borderwidth=0).grid(row=0, column=1, sticky='nswe', padx=(0, 1), pady=1)

		self.popup_after = self.after(ms, lambda: self.remove_popup())

	def remove_popup(self) -> None:
		self.popup_elem.destroy()
		self.popup_elem = None
		self.after_cancel(self.popup_after)
		self.popup_after = None


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


def create_timetable(path: str, encoding: str = 'utf-8') -> None:
	if not path.endswith('.json'):
		path += '.json'

	with open(path, 'w', encoding=encoding) as eventfile:
		eventfile.write(TIMETABLE_JSON_TEMPLATE % int(datetime.datetime.now().timestamp()))


def read_timetable(path: str, encoding: str = 'utf-8') -> tuple[list[str], list[str], list[str], Any, list[dict], str, list[list[str, bool, str]], int] | None:
	if not path.endswith('.json'):
		path += '.json'
	print(path)

	if not file_exists(path):
		create_timetable(path, encoding)

	try:
		with open(path, encoding=encoding) as readfile:
			print(readfile.readlines())
		with open(path, encoding=encoding) as readfile:
			data = json.load(readfile)
	except json.decoder.JSONDecodeError:
		mb.showwarning('JSON Decode Error', f'Could not load "{path}".\nReason: JSON Decode Error\n\n{sys.exc_info()[1]}')
		return

	return data['classes'], data['teachers'], data['rooms'], data['timetable'], data['events'], data['day_start'], data['sessions'], data['start_date_timestamp']


def increment_numbering(indent: str) -> str:
	location = re.match('[^\t .):]*', indent).span()
	numbering = indent.strip('\t .):')
	if numbering:
		if re.match('[0-9]*', numbering).span() == (0, len(numbering)):
			numbering = list(str(int(numbering) + 1))
			indent = list(indent)
			indent[location[0]:location[1]] = numbering
			indent = ''.join(indent)
		elif re.match('[a-zA-Z]*', numbering).span() == (0, len(numbering)):
			numbering = [ord(i.lower()) - ord('a') for i in numbering[::-1]]
			add = True
			idx = 0
			while add:
				if idx >= len(numbering):
					numbering.append(0)
					add = False
				else:
					if numbering[idx] == 25:
						numbering[idx] = 0
						idx += 1
					else:
						numbering[idx] += 1
						add = False

			numbering = [chr(i + ord('a')) for i in numbering[::-1]]
			indent = list(indent)
			indent[location[0]:location[1]] = numbering
			indent = ''.join(indent)
	return indent


def load_images(data: list[tuple[str, str, int]], linecolour: str = '#D4D4D4', highlightcolour: str = '#6FB0DB') -> dict:
	images = {}
	for file, name, width in data:
		if file_exists(file):
			with open(file) as svg_file:
				svg_data = svg_file.readlines()
				images.update({name: tksvg.SvgImage(data=''.join(svg_data).format(linecolour=linecolour, highlightcolour=highlightcolour), scaletowidth=width)})
		else:
			images.update({name: None})
	return images


def find_data_file() -> str:
	"""From: https://stackoverflow.com/a/56748839"""
	if getattr(sys, 'frozen', False):
		# The application is frozen
		return os.path.dirname(os.path.realpath(sys.executable))
	else:
		# The application is not frozen
		return os.path.dirname(os.path.realpath(__file__))


class SettingsWindow(tk.Toplevel):
	def __init__(self, root, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.root: Window = root
		self.attributes('-topmost', True)
		self.default_path = tk.StringVar(self, root.settings['default.path'])
		self.editor_font = tk.StringVar(self, root.settings['editor.font'][0])
		self.editor_size = tk.IntVar(self, root.settings['editor.font'][1])
		self.editor_style = tk.StringVar(self, root.settings['editor.font'][2].title())

		self.resolution_scaling = tk.StringVar(self, str(root.settings['resolution_scaling']))
		self.ui_scaling = tk.StringVar(self, str(root.settings['ui_scaling']))

		self.title('Settings')
		self.geometry(f'+{self.root.winfo_x() + int(self.root.winfo_width() // 3)}+{self.root.winfo_y() + int(self.root.winfo_height() // 3)}')
		self.root.call('wm', 'iconphoto', str(self), self.root.icons['window_icon2'])
		self.columnconfigure(0, weight=1)

		buttonconfig = {'background': '#3B434C', 'foreground': '#D8DEE9', 'activebackground': '#303841', 'mouseoverbackground': '#303841', 'borderwidth': 0, 'font': ('Calibri', 12), 'image': self.root.pixel, 'compound': 'center', 'highlightthickness': 1, 'highlightbackground': '#4F565E'}
		labelconfig = {'background': '#303841', 'borderwidth': 0, 'anchor': 'w', 'justify': 'left', 'image': self.root.pixel, 'compound': 'center'}

		#

		frame = tk.Frame(self, background='#303841', highlightthickness=1, highlightbackground='#4F565E')
		frame.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
		frame.columnconfigure(0, weight=1)

		tk.Label(frame, text='Default Path', foreground='#D8DEE9', font=('Calibri', 13, 'bold'), **labelconfig).grid(row=0, column=0, sticky='nswe', padx=1, pady=(1, 0), columns=2)
		tk.Label(frame, text='Specifies the path to load when the program is opened.', foreground='#777', font=('Calibri', 10, 'italic'), **labelconfig).grid(row=1, column=0, sticky='nswe', padx=1, pady=(0, 0), columns=2)
		self.path_entry = ttk.Entry(frame, style='stipple.TEntry', textvariable=self.default_path)
		self.path_entry.grid(row=2, column=0, sticky='nswe', padx=1, pady=(0, 1))

		MouseoverButton(frame, text='Browse', command=lambda: self.browse_timetables(), **buttonconfig).grid(row=2, column=1, sticky='nswe', padx=(0, 1), pady=(0, 1))

		## =====

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
		self.style_entry = CustomComboBox(frame, validatecommand=lambda v: self.validate_style(), validate='focusout', style='TCombobox', textvariable=self.editor_style, values=['Normal', 'Bold', 'Italic', 'Bold Italic'])
		self.style_entry.configure(invalidcommand=lambda: self.invalid_input(self.style_entry, 'Style must be "normal", or "bold" and/or "italic"'))
		self.style_entry.grid(row=3, column=3, sticky='nswe', padx=(0, 1), pady=(0, 1))

		## =====

		frame = tk.Frame(self, background='#303841', highlightthickness=1, highlightbackground='#4F565E')
		frame.grid(row=2, column=0, padx=5, pady=5, sticky='nswe')
		frame.columnconfigure(0, weight=1)

		tk.Label(frame, text='Resolution Scaling', foreground='#D8DEE9', font=('Calibri', 13, 'bold'), **labelconfig).grid(row=0, column=0, sticky='nswe', padx=1, pady=(1, 0), columns=2)
		tk.Label(frame, text='DPI scaling for the application. Must be an intager.', foreground='#777', font=('Calibri', 10, 'italic'), **labelconfig).grid(row=1, column=0, sticky='nswe', padx=1, pady=(0, 0), columns=2)
		self.resolution_entry = ttk.Entry(frame, validatecommand=lambda v: self.validate_dpi_scale(), validate='focusout', style='stipple.TEntry', textvariable=self.resolution_scaling)
		self.resolution_entry.configure(invalidcommand=lambda: self.invalid_input(self.resolution_entry, 'Resolution scaling must be an integer between 0 and 3.'))
		self.resolution_entry.grid(row=2, column=0, sticky='nswe', padx=1, pady=(0, 1), columns=2)

		## =====

		frame = tk.Frame(self, background='#303841', highlightthickness=1, highlightbackground='#4F565E')
		frame.grid(row=3, column=0, padx=5, pady=5, sticky='nswe')
		frame.columnconfigure(0, weight=1)

		tk.Label(frame, text='UI Scaling', foreground='#D8DEE9', font=('Calibri', 13, 'bold'), **labelconfig).grid(row=0, column=0, sticky='nswe', padx=1, pady=(1, 0), columns=2)
		tk.Label(frame, text='Scaling for the size of the application UI.', foreground='#777', font=('Calibri', 10, 'italic'), **labelconfig).grid(row=1, column=0, sticky='nswe', padx=1, pady=(0, 0), columns=2)
		self.scale_entry = ttk.Entry(frame, validatecommand=lambda v: self.validate_ui_scale(), validate='focusout', style='stipple.TEntry', textvariable=self.ui_scaling)
		self.scale_entry.configure(invalidcommand=lambda: self.invalid_input(self.scale_entry, 'UI scale must be a number between 0.2 and 10.0'))
		self.scale_entry.grid(row=2, column=0, sticky='nswe', padx=1, pady=(0, 1), columns=2)

		frame = tk.Frame(self, background='#4F565E', height=5)
		frame.grid(row=4, column=0, sticky='nse', padx=5, pady=5)

		MouseoverButton(frame, text='Ok', command=lambda: self.ok_pressed(), width=60, **buttonconfig).grid(row=0, column=1, sticky='nswe', padx=(1, 1), pady=(1, 1))
		MouseoverButton(frame, text='Cancel', command=lambda: self.destroy(), width=60, **buttonconfig).grid(row=0, column=2, sticky='nswe', padx=(0, 1), pady=(1, 1))
		MouseoverButton(frame, text='Apply', command=lambda: self.apply(), width=60, **buttonconfig).grid(row=0, column=3, sticky='nswe', padx=(0, 1), pady=(1, 1))

	def invalid_input(self, element: ttk.Entry, text: str) -> None:
		cursor_pos = element.index(tk.INSERT)
		mb.showinfo('Invalid Input', text)
		element.focus()
		element.icursor(cursor_pos)

	def validate_font(self) -> bool:
		return self.editor_font.get() in tkfont.families()

	def validate_style(self) -> bool:
		style = self.editor_style.get().lower()
		styles = [v.strip() for v in style.split(' ') if v.strip() in ['normal', 'bold', 'italic']]
		valid = (0 <= len(styles) <= 1 or styles in [['bold', 'italic'], ['italic', 'bold']]) and style.replace('italic', '').replace('bold', '').replace('normal', '').strip(' \n\t') == ''
		if valid:
			self.editor_style.set(' '.join(styles).title())
		return valid

	def validate_size(self) -> bool:
		return 1 <= int(self.editor_size.get()) <= 144

	def validate_dpi_scale(self) -> bool:
		print('dpi')
		if not self.resolution_scaling.get().isnumeric():
			return False
		else:
			return 0 <= int(self.resolution_scaling.get()) <= 3

	def validate_ui_scale(self) -> bool:
		if not self.ui_scaling.get().replace('.', '', 1).isnumeric():
			return False
		else:
			return 0.2 <= float(self.ui_scaling.get()) <= 10

	def browse_timetables(self) -> None:
		filename = fd.askopenfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=os.path.dirname(self.root.filename), initialfile=self.root.filename, parent=self)
		if filename:
			self.default_path.set(filename)

	def get_settings(self) -> dict:
		return {
			'default.path': self.default_path.get(),
			'editor.font': [self.editor_font.get().title(), int(self.editor_size.get()), self.editor_style.get().lower()],
			'resolution_scaling': int(self.resolution_scaling.get()),
			'ui_scaling': float(self.ui_scaling.get())
		}

	def ok_pressed(self) -> None:
		self.apply()
		self.destroy()

	def apply(self) -> None:
		print('apply', self.ui_scaling.get())
		settings_dict = self.get_settings()
		if settings_dict != self.root.settings:
			self.root.settings.update(settings_dict)
			if settings_dict['editor.font'] != self.root.settings['editor.font']:
				self.root.timetable.entry_font.configure(family=self.editor_font.get(), size=self.editor_size.get(), slant='italic' if 'italic' in self.editor_style.get().lower() else 'roman', weight='bold' if 'bold' in self.editor_style.get().lower() else 'normal')
			if settings_dict['resolution_scaling'] != self.root.settings['resolution_scaling'] or settings_dict['ui_scaling'] != self.root.settings['ui_scaling']:
				mb.showinfo('Restart Required', 'The program must be restarted for these changes to take effect.')
				if settings_dict['ui_scaling'] != self.root.settings['ui_scaling']:
					self.root.tk.call('tk', 'scaling', float(self.ui_scaling.get()))
				if settings_dict['resolution_scaling'] != self.root.settings['resolution_scaling']:
					ctypes.windll.shcore.SetProcessDpiAwareness(int(self.resolution_scaling.get()))
			with open('settings.json', 'w', encoding='utf-8') as file:
				json_object = json.dumps(settings_dict, indent=4, separators=(', ', ': '))
				file.write(json_object)


## Load Settings
DEFAULT_SETTINGS = {
	"default.path": find_data_file() + "/timetable.json",
	"editor.font": ["Calibri", 10, ""],
	"resolution_scaling": 2,
	"ui_scaling": 1.3
}

DEFAULT_WINDOW_SETTINGS = {
	"window.geometry": "1198x744+341+69",
	"window.state": "normal"
}

ImageFiles = ['blank.png', 'stipple.png', 'slider-thumb-large-active.png', 'slider-thumb-large.png', 'dotpoints.svg', 'numbering3.svg', 'lettering.svg', 'calendar.svg', 'saveas.svg', 'savecopy.svg', 'new_timetable.svg', 'import.svg', 'export.svg', 'pdf_icon.svg', 'xls_icon.svg', 'csv_icon.svg', 'help_icon.svg', 'about_icon.svg']


def validate_local_files() -> list[bool | str]:
	checks = [not file_exists('settings.json')]

	if not checks[-1]:
		try:
			with open('settings.json', encoding='utf-8') as file:
				settings = json.load(file)
			keys = list(settings.keys())
			keys_invalid = False
			for i in ['default.path', 'editor.font', 'resolution_scaling', 'ui_scaling']:
				if i not in keys:
					keys_invalid = True
			checks.extend([False, keys_invalid])
		except json.decoder.JSONDecodeError:
			checks.extend([str(sys.exc_info()[1]), False])

	else:
		checks.extend([False, False])

	checks.append(not file_exists('window_settings.json'))

	if not checks[-1]:
		try:
			with open('window_settings.json', encoding='utf-8') as file:
				window_settings = json.load(file)
			keys = list(window_settings.keys())
			keys_invalid = False
			for i in ['window.geometry', 'window.state']:
				if i not in keys:
					keys_invalid = True
			checks.extend([False, keys_invalid])
		except json.decoder.JSONDecodeError:
			checks.extend([str(sys.exc_info()[1]), False])
	else:
		checks.extend([False, False])

	checks.append(not os.path.exists('icons'))

	missing_icons = False
	if not checks[-1]:
		counter = 0
		icon_files = os.listdir('icons')
		while not missing_icons and counter < len(ImageFiles):
			if ImageFiles[counter] in icon_files:
				counter += 1
			else:
				missing_icons = True
	checks.append(missing_icons)

	if all(checks[:3]):
		if file_exists(settings['default.path']):
			try:
				with open(settings['default.path'], encoding='utf-8') as file:
					tt_data = json.load(file)
				keys = list(tt_data.keys())
				keys_invalid = False
				for i in ['classes', 'teachers', 'rooms', 'timetable', 'events', 'sessions', 'day_start', 'start_date_timestamp']:
					if i not in keys:
						keys_invalid = True
				checks.extend([False, False, settings['default.path'] if keys_invalid else False])
			except json.decoder.JSONDecodeError:
				checks.extend([False, [settings['default.path'], str(sys.exc_info()[1])], False])
		else:
			checks.extend([settings['default.path'], False, False])
	else:
		checks.extend([False, False, False])

	return checks


file_val = validate_local_files()

about_info = f'Timetable Version {VERSION}\n\n{{spacer}}\nProgram Name  : Timetable.py\nAuthor        : Connor Bateman\nVersion       : v2.21.1\nRevision Date : 23-05-2024 11:00\nDependencies  : null\n\n{{pyheading}}\nVersion        : {platform.python_version()}\nRevision       : {platform.python_revision()}\nCompiler       : {platform.python_compiler()}\nImplementation : {platform.python_implementation()}\n\n{{exheading}}\nBase         : '
if sys.platform == 'win32':
	about_info += 'Win32GUI'
elif sys.platform == 'win64':
	about_info += 'Win64GUI'
else:
	about_info += 'None'
about_info += f'\nPath         : {find_data_file()}\nProduct Code : {None}\nUpgrade Code : {None}\n'

about_width = max(map(len, about_info.split('\n')))

about_info = about_info.format(spacer='=' * about_width, pyheading=' Python '.center(about_width, '-'), exheading=' Executable '.center(about_width, '-'))

about_info += '=' * about_width


if file_val[3]:
	json_object = json.dumps(DEFAULT_WINDOW_SETTINGS, indent=4, separators=(', ', ': '))
	with open('window_settings.json', 'w', encoding='utf-8') as File:
		File.write(json_object)

window = Window(file_val)

## Display a warning if using the wrong operating system, otherwise, set DPI awareness
if platform.system() == 'Windows':
	ctypes.windll.shcore.SetProcessDpiAwareness(window.settings['resolution_scaling'])


m = ExportAsPDFMenu(window)

window.mainloop()

first_time_setup = False
if file_exists('first_time_setup.txt') and getattr(sys, 'frozen', True):
	first_time_setup = True
	os.remove('first_time_setup.txt')
	if platform.system() != 'Windows':
		mb.showwarning('Unsupported Operating System', f'Your operating system is {platform.system()}, however this\nprogram was developed for Windows.\n\nRunning this program on another system may cause unintended behavior.')

else:
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

if any(file_val[:3]) or any(file_val[-3:]):  # Check the validation of the settings file and window_settings file.
	Filename = fd.asksaveasfilename(defaultextension='.json', filetypes=(('JSON', '.json'), ('Plain Text', '.txt'), ('All', '*')), initialdir=find_data_file(), initialfile='new_timetable.json', confirmoverwrite=True, parent=window, title='Create new timetable')
	if Filename == "":
		window.destroy()
	else:
		window.filename = Filename
		window.top_bar.filename_display.configure(text=Filename)

		start_time = window.get_start_week(allow_cancel=True)
		if start_time is None:
			window.destroy()
		else:
			window.settings.update({'default.path': window.filename})
			if not file_exists('settings.json'):
				json_object = json.dumps(window.settings, indent=4, separators=(', ', ': '))
				with open('settings.json', 'w', encoding='utf-8') as File:
					File.write(json_object)

			with open(Filename, 'w', encoding='utf-8') as File:
				File.writelines(TIMETABLE_JSON_TEMPLATE % start_time)

			TimetableData = read_timetable(Filename)
			if TimetableData is not None:
				window.timetable.destroy()
				window.timetable = TimeTable(window, *TimetableData)
				window.timetable.grid(row=1, column=0, sticky='nswe')

## Check that the window hasn't been destroyed by the code above
if 'window' in globals():
	window.update_idletasks()
	size = (window.timetable.display_frame.winfo_width() - 47, window.timetable.display_frame.winfo_height() + window.top_bar.winfo_height() - 34)
	window.wm_minsize(*size)

window.mainloop()
