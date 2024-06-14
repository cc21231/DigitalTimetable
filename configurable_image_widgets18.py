import sys
from tkinter import ttk
import tkinter as tk
import ctypes
from typing import Optional, Union, Self, Any
import tksvg


class CIManager:
	def __init__(self, parent: tk.Tk, style: ttk.Style):
		"""
		Creates a manager for image mapping, widget layouts, and layout elements

		:param parent: Parent widget
		:param style: ttk Style object
		"""

		self.master: tk.Tk = parent
		self.style: ttk.Style = style
		self.master.evalfile('widget_image_config.tcl')

		self.layout_dict: dict[str: Layout] = {}

		self.default_mapping = {
			'Button.button': ('button', {'pressed': 'button-focus', '{active focus}': 'button-active', 'active': 'button-hover', 'focus': 'button-hover', 'disabled': 'button-insensitive'}, {'border': 3, 'sticky': 'ewns'}),
			'Toolbutton.button': ('button-empty', {'{active selected !disabled}': 'button-active', 'selected': 'button-toggled', 'pressed': 'button-active', '{active !disabled}': 'button-hover'}, {'border': 3, 'sticky': 'news'}),
			'Checkbutton.indicator': ('checkbox-unchecked', {'disabled': 'checkbox-unchecked-insensitive', '{pressed selected}': 'checkbox-checked-pressed', '{active selected}': 'checkbox-checked-active', '{pressed !selected}': 'checkbox-unchecked-pressed', 'active': 'checkbox-unchecked-active', 'selected': 'checkbox-checked', '{disabled selected}': 'checkbox-checked-insensitive'}, {'width': 22, 'sticky': 'w'}),
			'Radiobutton.indicator': ('radio-unchecked', {'disabled': 'radio-unchecked-insensitive', '{pressed selected}': 'radio-checked-pressed', '{active selected}': 'radio-checked-active', '{pressed !selected}': 'radio-unchecked-pressed', 'active': 'radio-unchecked-active', 'selected': 'radio-checked', '{disabled selected}': 'radio-checked-insensitive'}, {'width': 22, 'sticky': 'w'}),
			'Horizontal.Scrollbar.trough': ('scrollbar-trough-horiz-active', {}, {'border': '{6 0 6 0}', 'sticky': 'ew'}),
			'Horizontal.Scrollbar.thumb': ('scrollbar-slider-horiz', {'{active !disabled}': 'scrollbar-slider-horiz-active', 'disabled': 'scrollbar-slider-insens'}, {'border': '{6 0 6 0}', 'sticky': 'ew'}),
			'Vertical.Scrollbar.trough': ('scrollbar-trough-vert-active', {}, {'border': '{0 6 0 6}', 'sticky': 'ns'}),
			'Vertical.Scrollbar.thumb': ('scrollbar-slider-vert', {'{active !disabled}': 'scrollbar-slider-vert-active', 'disabled': 'scrollbar-slider-insens'}, {'border': '{0 6 0 6}', 'sticky': 'ns'}),
			'Horizontal.Scale.trough': ('scrollbar-slider-horiz', {'disabled': 'scale-trough-horizontal'}, {'border': '{8 5 8 5}', 'padding': 0}),
			'Horizontal.Scale.slider': ('scale-slider', {'disabled': 'scale-slider-insensitive', 'pressed': 'scale-slider-pressed', 'active': 'scale-slider-active'}, {'sticky': '{}'}),
			'Vertical.Scale.trough': ('scrollbar-slider-vert', {'disabled': 'scale-trough-vertical'}, {'border': '{8 5 8 5}', 'padding': 0}),
			'Vertical.Scale.slider': ('scale-slider', {'disabled': 'scale-slider-insensitive', 'pressed': 'scale-slider-pressed', 'active': 'scale-slider-active'}, {'sticky': '{}'}),
			'Entry.field': ('entry', {'{focus !disabled}': 'entry-focus', '{hover !disabled}': 'entry-active', 'disabled': 'entry-insensitive'}, {'border': 3, 'padding': '{6 8}', 'sticky': 'news'}),
			'Labelframe.border': ('labelframe', {}, {'border': 4, 'padding': 4, 'sticky': 'news'}),
			'Menubutton.button': ('button', {'pressed': 'button-active', 'active': 'button-hover', 'disabled': 'button-insensitive'}, {'sticky': 'news', 'border': 3, 'padding': '{3 2}'}),
			'Menubutton.indicator': ('arrow-down', {'active': 'arrow-down-prelight', 'pressed': 'arrow-down-prelight', 'disabled': 'arrow-down-insens'}, {'sticky': 'e', 'width': 20}),
			'Combobox.field': ('entry', {'{readonly disabled}': 'button-insensitive', '{readonly pressed}': 'button-hover', '{readonly focus hover}': 'button-active', '{readonly focus}': 'button-focus', '{readonly hover}': 'button-hover', 'readonly': 'button', '{disabled}': 'entry-insensitive', '{focus}': 'entry-focus', '{focus hover}': 'entry-focus', '{hover}': 'entry-active'}, {'border': 4, 'padding': '{6 8}'}),
			'Combobox.downarrow': ('arrow-down', {'active': 'arrow-down-prelight', 'pressed': 'arrow-down-prelight', 'disabled': 'arrow-down-insens'}, {'border': 4, 'sticky': '{}'}),
			'Spinbox.field': ('entry', {'focus': 'entry-focus', 'disabled': 'entry-insensitive', 'hover': 'entry-active'}, {'border': 4, 'padding': '{6 8}', 'sticky': 'news'}),
			'Spinbox.uparrow': ('arrow-up-small', {'active': 'arrow-up-small-prelight', 'pressed': 'arrow-up-small-prelight', 'disabled': 'arrow-up-small-insens'}, {'border': 4, 'sticky': '{}'}),
			'Spinbox.downarrow': ('arrow-down-small', {'active': 'arrow-down-small-prelight', 'pressed': 'arrow-down-small-prelight', 'disabled': 'arrow-down-small-insens'}, {'border': 4, 'sticky': '{}'}),
			'Notebook.client': ('notebook-client', {}, {'border': 1}),
			'Notebook.tab': ('notebook-tab-top', {'selected': 'notebook-tab-top-active', 'active': 'notebook-tab-top-hover'}, {'padding': '{12 4 12 4}', 'border': 2}),
			'Horizontal.Progressbar.trough': ('scrollbar-trough-horiz-active', {}, {'border': '{6 0 6 0}', 'sticky': 'ew'}),
			'Horizontal.Progressbar.pbar': ('scrollbar-slider-horiz', {}, {'border': '{6 0 6 0}', 'sticky': 'ew'}),
			'Vertical.Progressbar.trough': ('scrollbar-trough-vert-active', {}, {'border': '{0 6 0 6}', 'sticky': 'ns'}),
			'Vertical.Progressbar.pbar': ('scrollbar-slider-vert', {}, {'border': '{0 6 0 6}', 'sticky': 'ns'}),
			'Treeview.field': ('treeview', {}, {'border': 1}),
			'Treeheading.cell': ('notebook-client', {'active': 'treeheading-prelight'}, {'border': 1, 'padding': 4, 'sticky': 'ewns'}),
			'Treeheading.row': ('notebook-client', {}, {'border': 1, 'padding': 4, 'sticky': 'ewns'}),
			'Treeitem.indicator': ('arrow-right', {'user2': 'empty', 'user1': 'arrow-down'}, {'width': 15, 'sticky': 'w'}),
			'Treeitem.row': ('empty', {}, {'border': 1, 'padding': 4, 'sticky': 'ewns'}),
			'vsash': ('transparent', {}, {'sticky': 'e', 'padding': 1, 'width': 1}),
			'hsash': ('transparent', {}, {'sticky': 'n', 'padding': 1, 'width': 1}),
			'Panedwindow.background': ('empty', {}, {'border': '1'}),
			'Separator.separator': ('horizontal-separator', {}, {'sticky': 'we', 'height': 2}),
			'Sizegrip.sizegrip': ('sizegrip', {'active': 'sizegrip-active'}, {'sticky': 'se'}),
		}

	def layout(self, name: Optional[str] = None):
		"""
		Retrieve a layout object from the stored layout dictionary

		:param name: (str) Style name of the layout
		:return: (Layout) Layout object
		"""

		if name is None:
			return self.layout_dict
		else:
			return self.layout_dict[name]

	def load_image(self, filename: str, name: str = None, format: str = None) -> None:
		"""
		Loads an image from a file using tcl

		:param filename: (str) The path to the image to load
		:param name: (Optional[str]) The key to use for the loaded image. If <name> is None, the filename (minus the extension) will be used as the key
		:param format: (Optional[str]) The image format of the file (e.g., PNG)
		"""

		self.master.eval(f'load_image {filename} {name if name is not None else ""} {format if format is not None else ""}')

	def load_local_dir(self, extension: str = '*.png') -> None:
		self.master.eval(f'load_local_dir {extension}')

	def load_dir(self, dirname: str, path: str = None, extension: str = None) -> None:
		self.master.eval(f'load_dir {dirname} {path if path is not None else ""} {extension if extension is not None else ""}')

	def get_images(self) -> str:
		""" Get the names of the loaded images """
		return self.master.eval('get_images')

	def check_array(self, key: str) -> str:
		"""
		Check the tcl image array for the existence of the key, and format the key appropriately

		:param key: (str) The key to check
		:return: (str) The formatted key
		"""

		if int(self.master.eval(f'info exists I({key})')):
			return f'$I({key})'
		else:
			return key

	def create_layout(self, style: str, data: Optional[list] = None, stylename: Optional[str] = None):
		"""
		Creates a layout object

		:param style: (str) The ttk style name for the layout. This is also used as the key for the layout.
		:param data: (dict) The dictionary containing the element layout for the style. The default value of this can be retrieved using <Style object>.layout(<style name>)
		:param stylename: (Optional[str]) The prefix for the style name used before layout element names. If this is not specified, it is calculated automatically. This only needs to be specified for specific cases where the style is not in a standard format.
		"""

		layout = Layout(self.style, style, data, stylename)

		self.layout_dict.update({style: layout})

		return layout

	def map(self, style: str, element_name: str, mapping: dict, **kwargs) -> tuple[dict, dict]:
		"""
		States:
			General:
			- default

			- pressed
			- active
			- focus
			- disabled
			- selected
			- hover

			Entry:
			- readonly

			Treeview:
			- user1
			- user2

			Modifiers:
			- use '!' for NOT (e.g., !active)
			- use '{' and '}' for multiple states (e.g., {active !disabled})

		:param style: (str) The name of the ttk style to modify (E.g., "Custom.TButton”).
		:param element_name: (str) The name of the layout element to modify (E.g.,
		“Radiobutton.indicator”). A list of layout elements can be retrieved by calling the <elements> method on a Layout object. These can also be found in the standard ttk layout for each element.
		:param mapping: (dict) The dictionary containing mapping information. In the form of {<state>: <image name or tkinter PhotoImage object>}


		General keywords:
			:keyword border: (int) The width of the border
			:keyword padding: (list(int, ...)) The padding of the button. Use curly brackets for list and use spaces instead of comma (E.g., '{3 5}')
			:keyword sticky: (str)
			:keyword width: (int)
			:keyword height: (int)
			:keyword expand: (str)
			:keyword side: (str)

		:keyword inherit: (bool) Weather or not to inherit mapping and configuration from the default theme
		:keyword stylename: (str) The prefix for the style name used before layout element names. If this is not specified, it is calculated automatically. This only needs to be specified for specific cases where the style is not in a standard format.

		:return: (tuple[dict, dict]) The mapping and kwargs applied to the style after inheriting (if specified) the default configuration
		"""

		style_name, _ = kwargs.pop('stylename') if 'stylename' in kwargs else get_widget_name(style)
		inherit = kwargs.pop('inherit') if 'inherit' in kwargs else True
		default_image = mapping.pop('default') if 'default' in mapping else self.default_mapping[element_name][0]
		default_image = self.check_array(default_image)

		if style in self.layout_dict:
			layout = self.layout_dict[style]
		else:
			layout = self.create_layout(style, self.style.layout(style))
			self.layout_dict.update({style: layout})

		if isinstance(element_name, int):
			element_name = list(layout.elems.values())[element_name].name

		if inherit and element_name in self.default_mapping:
			default_map = self.default_mapping[element_name][1]
			default_map.update(mapping)
			mapping = default_map

			default_kwargs = self.default_mapping[element_name][2]
			default_kwargs.update(kwargs)
			kwargs = default_kwargs

		configuration_string = f'ttk::style element create {style_name}{"." if style_name else ""}{element_name} '

		if mapping is None:
			configuration_string += f'image {default_image}'
		else:
			configuration_string += f'image [list {default_image}'

			for k, v in mapping.items():
				configuration_string += f' {k} {self.check_array(v)}'

			configuration_string += ']'

		for k, v in kwargs.items():
			configuration_string += f' -{k} {v}'

		try:
			self.master.eval(configuration_string)
		except tk.TclError as exc:
			d = sys.exc_info()
			if not str(d[1]).startswith('Duplicate element'):
				raise exc

		print(configuration_string)

		return mapping, kwargs


class Element:
	def __init__(self, master, name: str, style: Optional[str] = None, parent: Optional[str] = None, **kwargs):
		"""
		A configurable layout element that can be used in a ttk style.

		:param master: The root Layout object that the element is a part of.
		:param name: The name of the layout element.
		:param style: The prefix for the ttk style that the element is a part of.
		:param parent: The name of the elements parent object in the layout
		"""

		self.name = name
		self.master: Layout = master
		self.config = kwargs
		self.style = style
		self.parent = parent

	def __repr__(self) -> str:
		""" Return the name of the element as it appears in the layout dictionary """
		if self.style is not None:
			return f'{self.style}.{self.name}'
		else:
			return self.name

	def cget(self, key: str) -> Union[int, float, str, bool, None]:
		""" Get the configuration for the key """
		return self.config[key]

	def get(self) -> tuple[str, dict]:
		""" Return the data contained in the element object in a format to be used as a ttk widget layout """
		temp_config = self.config.copy()

		if 'children' in self.config and self.config['children'] is not None:
			child_layout = [i.get() for i in self.config['children']]
			temp_config.update({'children': child_layout})

		return f'{self.style if self.style else ""}{"." if self.style else ""}{self.name}', temp_config

	def child(self, element: Optional[Self] = None, index: Optional[int] = None) -> list[Self]:
		"""
		Childs the specified element to itself at the specified index.
		If no element is specified, it returns the elements children.

		:param element: (Optional[Element]) The element object to add as a child
		:param index: (Optional[int]) The index to add the child at. The default is -1 (the last position)
		:return: (list[Element]) A list of the element’s children
		"""
		if element is not None:
			self.config['children'].insert(-1 if index is None else index, element)

		self.master.update_layout()
		return self.config['children']

	def layoutspec(self) -> list[str]:
		try:
			window.eval(f'ttk::style layout {self.master.name} {{{self.name} -a 0}}')
		except tk.TclError:
			info = str(sys.exc_info()[1]).split(':')[1].removeprefix(' must be -').replace(', or ', ', ').split(', -')
			return info

	def configure(self, **kwargs) -> dict:
		self.config.update(kwargs)
		self.master.update_layout()
		return self.config


class Layout:
	"""
	The Layout object is a manager for ttk widget layouts. It allows easy modification of style layouts and layout elements.

	The position and structure of the layout elements are stored in dictionaries
	"""

	def __init__(self, style: ttk.Style, name: str, data: list = None, stylename: str = None):
		"""
		:param style: (Style object) A ttk style object
		:param name: (str) The name of the ttk style that the layout applies to. This is also used as the index for the layout.
		:param data: (Optional[dict]) The initial layout data in the same format as ttk.Style.layout()
		:param stylename: (Optional[str]) The prefix for the style name used before layout element names. If this is not specified, it is calculated automatically. This only needs to be specified for specific cases where the style is not in a standard format.
		"""

		self.style = style
		self.name = name
		self.elems = {}
		self.top_elems = []
		self.current_layout = data if data is not None else style.layout(name)

		s, _ = get_widget_name(name)

		self.stylename = stylename if stylename is not None else s

		self.load_data(self.current_layout)

	def element_configure(self, element_name: str, **kwargs: Any) -> None:
		self.elems[element_name].configure(**kwargs)

	def elements(self, key: Optional[str] = None) -> Union[Element, list[Element]]:
		if key is None:
			return list(self.elems.values())
		else:
			return self.elems[key]

	def update_layout(self) -> None:
		self.current_layout = []
		for i in self.top_elems:
			self.current_layout.append(i.get())
		self.style.layout(self.name, self.current_layout)

	def get(self) -> dict:
		return self.current_layout

	def load_data(self, layout: dict) -> None:
		self.top_elems = self.load_data_element(layout)
		self.update_layout()

	def load_data_element(self, data: dict, parent: Optional[str] = None) -> list[Element]:
		elems = []
		for name, config in data:
			if 'children' in config:
				config.update({'children': self.load_data_element(config['children'], name)})

			elem = Element(self, name, self.stylename, parent, **config)
			elems.append(elem)
			self.elems.update({elem.name: elem})
		return elems

	def add(self, element: Union[object, str], index: Optional[int] = None, parent: Optional[str] = None, **kwargs) -> Element:
		if not isinstance(element, Element):
			element = Element(self, element, self.stylename, parent, **kwargs)
		else:
			element.parent = parent

		self.elems.update({element.name: element})
		if element.style is None:
			element.style = self.stylename

		if parent is None:
			if index is None:
				self.top_elems.append(element)
			else:
				self.top_elems.insert(index, element)
			self.update_layout()
		else:
			if not isinstance(parent, Element):
				parent = self.elems[parent]
			parent.child(element, index)

		return element


def get_widget_name(style_name: str) -> tuple[str, str]:
	"""
	Gets the tkinter widget name from a ttk style string.
	"""

	print(style_name)
	style_name = style_name.split('.')
	widgets = ['TButton', 'TCheckbutton', 'TRadiobutton', 'TScrollbar', 'TScale', 'TEntry', 'TLabelframe', 'TMenubutton', 'TCombobox', 'TSpinbox', 'TNotebook', 'Tab', 'Progressbar', 'Treeview', 'Cell', 'Item', 'Heading', 'Row', 'TPanedwindow', 'TSeparator', 'TSizegrip', 'Vertical', 'Horizontal']
	widget_name = list(filter(lambda v: v in widgets, style_name))
	style_name = '.'.join(style_name[:style_name.index(widget_name[0])])
	widget_name = '.'.join(widget_name)
	return style_name, widget_name


if __name__ == '__main__':
	window = tk.Tk()
	window.tk.call('tk', 'scaling', 1.9)
	ctypes.windll.shcore.SetProcessDpiAwareness(2)

	window.focus()

	style = ttk.Style()
	style.theme_use('default')

	manager = CIManager(window, style)
	manager.load_dir('icons')

	e = manager.create_layout('test.TButton')
	elem = e.add('Button.button', 0, 'Button.padding', sticky='nswe')
	e.elems['Button.button'].configure(sticky='nswe')

	manager.map('test.TButton', 'Button.button', {'default': 'check-on'})

	ttk.Button(style='test.TButton', text='Test').grid()

	ttk.Sizegrip().grid()

	image = tksvg.SvgImage(data=b'<svg viewBox="0 0 448 512" fill="#f00"><path d="M0 464c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48V192H0v272zm320-196c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v40c0 6.6-5.4 12-12 12h-40c-6.6 0-12-5.4-12-12v-40zm0 128c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v40c0 6.6-5.4 12-12 12h-40c-6.6 0-12-5.4-12-12v-40zM192 268c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v40c0 6.6-5.4 12-12 12h-40c-6.6 0-12-5.4-12-12v-40zm0 128c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v40c0 6.6-5.4 12-12 12h-40c-6.6 0-12-5.4-12-12v-40zM64 268c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v40c0 6.6-5.4 12-12 12H76c-6.6 0-12-5.4-12-12v-40zm0 128c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v40c0 6.6-5.4 12-12 12H76c-6.6 0-12-5.4-12-12v-40zM400 64h-48V16c0-8.8-7.2-16-16-16h-32c-8.8 0-16 7.2-16 16v48H160V16c0-8.8-7.2-16-16-16h-32c-8.8 0-16 7.2-16 16v48H48C21.5 64 0 85.5 0 112v48h448v-48c0-26.5-21.5-48-48-48z"/></svg>', scaletowidth=15)

	var = tk.IntVar()
	var2 = tk.IntVar()

	style.configure('test.Treeview.Heading', borderwidth=0)
	style.configure('test.Treeview', borderwidth=0)

	manager.map('test.TButton', 'Button.button', {'default': image, 'pressed': 'check-on', 'selected': 'button-unshade-pressed'}, padding='{3 5}')
	manager.map('test.Treeview', 'Treeview.field', {'default': 'check-on'})
	manager.map('test.Treeview.Heading', 'Treeheading.cell', {'default': 'notebook-client', 'active': 'treeheading-prelight'})
	manager.map('test.Treeview.Cell', 'Treeheading.cell', {})
	manager.map('test.Treeview.Item', 'Treeitem.indicator', {})
	manager.map('test.Treeview.Row', 'Treeitem.row', {'default': 'check-on'})
	manager.map('test.TSizegrip', 'Sizegrip.sizegrip', {}, border=0, sticky='nswe', inherit=True)
	manager.map('test.TSeparator', 'Separator.separator', {}, border=0, padding='{0 0 0 0}', sticky='nswe', inherit=True)
	manager.map('test.TPanedwindow', 'Panedwindow.background', {'default': 'check-on'})
	manager.layout('test.TPanedwindow').element_configure('Panedwindow.background', sticky='NSWE')

	window.rowconfigure(0, weight=1)
	window.columnconfigure(0, weight=1)

	paned_win = ttk.Sizegrip(style='test.TSizegrip')
	paned_win.grid(sticky='NSWE')

	paned_win = ttk.Panedwindow(style='test.TPanedwindow', width=10, height=100)
	paned_win.grid(sticky='EW')

	paned_win = ttk.Separator(style='test.TSeparator')
	paned_win.grid(sticky='EW')

	style.configure('test.Tbutton', background='#000')
	ttk.Button(style='test.TButton').grid()

	tree = ttk.Treeview(style='test.Treeview')
	tree.insert('', tk.END, text='Lorem ipsum', values=['a'])
	tree.insert('', tk.END, text='Lorem ipsum')
	b = tree.insert('', tk.END, text='Lorem ipsum')
	tree.insert(b, tk.END, text='Lorem ipsum', values=['e'])
	tree.insert(b, tk.END, text='Lorem ipsum')

	t = ttk.Entry(width=20, style='test.TEntry')
	t.insert(0, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')
	t.grid()

	tree.item(b, open=True)
	tree.grid(sticky='EW')

	manager.map('test.TCheckbutton', 'Checkbutton.indicator', {'default': 'arrow-right-prelight', 'pressed': 'check-on', 'selected': 'button-unshade-pressed'}, padding='{3 5}')
	manager.map('test.TRadiobutton', 'Radiobutton.indicator', {}, padding='{3 5}')
	manager.map('test.TEntry', 'Entry.field', {'default': 'entry', '{focus !disabled}': 'entry-focus', '{hover !disabled}': 'entry-active', 'disabled': 'entry-insensitive'}, border=3, padding='{6 8}', sticky='nswe')
	manager.map('test.Horizontal.TScrollbar', 'Horizontal.Scrollbar.trough', {'default': 'scrollbar-trough-horiz-active'}, border='{6 0 6 0}', sticky='ew')
	manager.map('test.Horizontal.TScrollbar', 'Horizontal.Scrollbar.thumb', {'default': 'scrollbar-slider-horiz', '{active !disabled}': 'scrollbar-slider-horiz-active', 'disabled': 'scrollbar-slider-insens'}, border='{6 0 6 0}', sticky='ew')
	manager.map('test.Horizontal.TScale', 'Horizontal.Scale.trough', {'default': 'check-on', 'disabled': 'scale-trough-horizontal'}, border='{8 5 8 5}', padding=0)
	manager.map('test.Horizontal.TScale', 'Horizontal.Scale.slider', {'default': 'scale-slider', 'disabled': 'scale-slider-insensitive', 'pressed': 'scale-slider-pressed', 'active': 'scale-slider-active'}, border='{8 5 8 5}', padding=0, sticky='{}')

	ttk.Button(text='test', style='test.TButton').grid()
	ttk.Checkbutton(text='test', style='test.TCheckbutton', variable=var).grid()
	ttk.Radiobutton(text='test', style='test.TRadiobutton', variable=var2, value=0).grid()
	ttk.Radiobutton(text='test', style='test.TRadiobutton', variable=var2, value=1).grid()

	t = ttk.Entry(width=20, style='test.TEntry')
	t.insert(0, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')
	t.grid()

	s = ttk.Scrollbar(orient='horizontal', command=t.xview, style='test.Horizontal.TScrollbar')
	t.configure(xscrollcommand=s.set)
	s.grid(sticky='EW')

	ttk.Scale(orient='horizontal', from_=0, to=100, style='test.Horizontal.TScale').grid(sticky='EW')

	frame = ttk.Labelframe(text='test', height=50)
	print(style.layout('TLabelframe'))
	manager.map('TLabelframe', 'Labelframe.border', {'default': 'labelframe'}, border=4, padding=4, sticky='nswe')
	frame.grid(sticky='EW', padx=5, pady=5)

	print(style.layout('test.TMenubutton'))

	manager.map('test.TMenubutton', 'Menubutton.button', {'default': 'check-on', 'pressed': 'button-active', 'active': 'button-hover', 'disabled': 'button-insensitive'}, sticky='nswe', border=3, padding='{3 2}')
	manager.map('test.TMenubutton', 'Menubutton.indicator', {'default': 'check-on', 'pressed': 'arrow-down-prelight', 'active': 'arrow-down-prelight', 'disabled': 'arrow-down-insens'}, sticky='e', width=20)
	manager.layout('test.TMenubutton').add('Menubutton.button', 0, 'Menubutton.border', sticky='nswe')

	b = ttk.Menubutton(frame, text='test', width=10, style='test.TMenubutton')

	b.grid(padx=5, pady=5)

	a = tk.Menu(b)
	a.add_command(label='test')

	b.configure(menu=a)

	textvar = tk.StringVar(value='Test')
	b = ttk.Combobox(textvariable=textvar, values=['row0', 'row1', 'row2'], style='test.TCombobox')
	manager.map('test.TCombobox', 'Combobox.indicator', {'default': 'entry', '{readonly disabled}': 'button-insensitive', '{readonly pressed}': 'button-hover', '{readonly focus hover}': 'button-active', '{readonly focus}': 'button-focus', '{readonly hover}': 'button-hover', 'readonly': 'button', '{disabled}': 'entry-insensitive', '{focus}': 'entry-focus', '{focus hover}': 'entry-focus', '{hover}': 'entry-active'}, border=4, padding='{6 8}')
	manager.map('test.TCombobox', 'Combobox.downarrow', {'default': 'arrow-down', 'active': 'arrow-down-prelight', 'pressed': 'arrow-down-prelight', 'disabled': 'arrow-down-insens'}, border=4, sticky='{}')
	b.grid()

	textvar = tk.IntVar()
	b = ttk.Spinbox(textvariable=textvar, values=list(map(str, [0, 1, 2, 3, 4, 5])), style='test.TSpinbox')
	manager.map('test.TSpinbox', 'Spinbox.field', {'default': 'entry', 'focus': 'entry-focus', 'disabled': 'entry-insensitive', 'hover': 'entry-active'}, border=4, padding='{6 8}', sticky='nswe')
	manager.map('test.TSpinbox', 'Spinbox.uparrow', {'default': 'arrow-up-small', 'active': 'arrow-up-small-prelight', 'pressed': 'arrow-up-small-prelight', 'disabled': 'arrow-up-small-insens'}, border=4, sticky='{}')
	manager.map('test.TSpinbox', 'Spinbox.downarrow', {'default': 'arrow-down-small', 'active': 'arrow-down-small-prelight', 'pressed': 'arrow-down-small-prelight', 'disabled': 'arrow-down-small-insens'}, border=4, sticky='{}')
	b.grid()

	b = ttk.Notebook(height=100, style='test.TNotebook')
	manager.map('test.TNotebook', 'Notebook.client', {'default': 'notebook-client'}, border=1)
	manager.map('test.TNotebook.Tab', 'Notebook.tab', {'default': 'notebook-tab-top', 'selected': 'check-on', 'active': 'check-on'}, padding='{12 4 12 4}', border=2)

	#b.grid(sticky='NSWE')

	t = tk.Label(b, text='test 1')
	b.add(t, padding=(5, 5), text='Tab1')

	t = tk.Label(b, text='test 2')
	b.add(t, padding=(5, 5), text='Tab2')

	b = ttk.Progressbar(maximum=100, value=50, style='test.Horizontal.TProgressbar')
	print(style.layout('test.Horizontal.TProgressbar'))

	manager.map('test.Horizontal.TProgressbar', 'Horizontal.Progressbar.trough', {'default': 'scrollbar-trough-horiz-active'}, border='{6 0 6 0}', sticky='ew')
	manager.map('test.Horizontal.TProgressbar', 'Horizontal.Progressbar.pbar', {'default': 'check-on'}, border='{6 0 6 0}', sticky='ew')
	b.grid(sticky='EW')
	print(style.layout('test.Horizontal.TProgressbar'), '\n')
	window.mainloop()

	t = ttk.Treeview(height=5, style='test2.Treeview')
	manager.map('test2.Treeview', 'Treeview.field', {'default': 'treeview'}, border=1)
	manager.map('test2.Treeview.Cell', 'Treeheader.cell', {'default': 'notebook-client', 'active': 'treeheading-prelight'}, border=1, padding=4, sticky='nswe')
	manager.map('test2.Treeview.Item', 'Treeitem.indicator', {'default': 'arrow-right', 'user2': 'empty', 'user1': 'arrow-down'}, width=15, sticky='w')
	manager.map('test2.Treeview.Heading', 'Treeitem.cell', {'default': 'treeview', 'active': 'treeheading-prelight'})

	t.grid(sticky='EW')

	t.insert('', tk.END, text='Lorem ipsum', values=['a'])
	t.insert('', tk.END, text='Lorem ipsum')
	b = t.insert('', tk.END, text='Lorem ipsum')
	t.insert(b, tk.END, text='Lorem ipsum', values=['e'])
	t.insert(b, tk.END, text='Lorem ipsum')

	t.item(b, open=True)

	window.mainloop()
