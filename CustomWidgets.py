from typing import Literal, Optional, Any
from tkinter import ttk
import tkinter as tk


class AutoScrollbar(ttk.Scrollbar):
    """
    :From: https://stackoverflow.com/a/48137257

    A scrollbar that hides itself if it’s not needed.
    Only works for grid geometry manager.
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
        self.winfo_toplevel().eval(f'set popdown [ttk::combobox::PopdownWindow {self}]')  # Use tcl to set a variable `popdown` to this widget
        self.winfo_toplevel().eval(f'$popdown.f.sb configure -style {kwargs["style"]}.Vertical.TScrollbar')  # Use tcl to set the style of this widget’s scrollbar


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

    :keyword hscrollbar: The scrollbar widget to which the x-scroll command should be bound
    :keyword vscrollbar: The scrollbar widget to which the y-scroll command should be bound

    The scroll factor controls the sensitivity of the mousewheel scroll for each axis.
    Any value between -120 and 0 or 120 and 0, not including 0.
    ±120 is the minimum sensitivity any any value above 0 has inverted sensitivity.
    :keyword yscrollfactor: Scroll factor for the y-axis.
    :keyword xscrollfactor: Scroll factor for the x-axis.
    """

    def __init__(self, master, **kwargs) -> None:
        ## Get the scrollbar widget to link to the canvas scroll for each axis
        hscrollbar: tk.Scrollbar = kwargs.pop('hscrollbar') if 'hscrollbar' in kwargs else None
        vscrollbar: tk.Scrollbar = kwargs.pop('vscrollbar') if 'vscrollbar' in kwargs else None

        ## Get the scroll factor for each axis
        self.yscrollfactor: int | float = kwargs.pop('yscrollfactor') if 'yscrollfactor' in kwargs else -120
        self.xscrollfactor: int | float = kwargs.pop('xscrollfactor') if 'xscrollfactor' in kwargs else -120

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

        ## Todo: Bind Button-4 and Button-5 to scroll
        ## Bind scrolling with the mousewheel to scroll the canvas widget.
        ## Pressing the `Shift` key changes the scroll axis.
        self.canvas.bind_all('<MouseWheel>', lambda v: self.canvas.yview_scroll(round(v.delta / self.yscrollfactor), 'units'))
        self.canvas.bind_all('<Shift-MouseWheel>', lambda v: self.canvas.xview_scroll(round(v.delta / self.xscrollfactor), 'units'))

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

        if self.frame.winfo_reqwidth() > self.canvas.winfo_width():
            # Update the inner frame’s width to fill the canvas.
            self.canvas.itemconfigure(self._scrollable_frame, width=self.canvas.winfo_width())


class Tab:
    def __init__(self, master, content, headerconfig=None, name='Untitled'):
        self.master: TabbedInterface = master
        self.content = content
        self.name = name
        self.state = 0

        headerconfig = headerconfig if headerconfig is not None else self.master.formatting['Tab']
        headerconfig.update(self.master.formatting['Inactive-Tab'])
        bordercolour = headerconfig.pop('bordercolour')
        borderpadx = headerconfig.pop('borderpadx')
        borderpady = headerconfig.pop('borderpady')

        self.header = tk.Frame(self.master.tab_frame.frame, background=bordercolour)
        self.header_label = tk.Label(self.header, text=name, **headerconfig)
        self.header_label.pack(expand=True, fill='both', padx=borderpadx, pady=borderpady)
        self.header_label.bind('<Button-1>', lambda v: self.master.select(self))
        self.header_label.bind('<Enter>', lambda v: self.highlight())
        self.header_label.bind('<Leave>', lambda v: self.unhighlight())

    def add(self, index=-1, select=False):
        self.master.add_tab(self, index, select)

    def _update_header_config(self):
        format_name = ['Inactive-Tab', 'Highlight-Tab', 'Active-Tab'][self.state]
        headerconfig = self.master.formatting[format_name].copy()
        print(headerconfig)
        self.header.configure(background=headerconfig.pop('bordercolour'))
        self.header_label.grid_configure(padx=headerconfig.pop('borderpadx'), pady=headerconfig.pop('borderpady'))
        print(headerconfig)
        self.header_label.configure(**headerconfig)

    def highlight(self):
        if self.state != 2:
            self.state = 1
            self._update_header_config()

    def unhighlight(self):
        if self.state == 1:
            self.state = 0
            self._update_header_config()

    def select(self):
        self.state = 2
        self._update_header_config()

    def deselect(self):
        self.state = 0
        self._update_header_config()
        self.content.grid_remove()


class TabbedInterface(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.enable_tab_dropdown = False  ## Todo: Implement tab dropdown

        ## Create a transparent 1px by 1px image. When used as the image for a widget such as a button or label, it allows for the size of said widget to be adjusted in pixels rather than arbitrary units.
        ## This may be inefficient if a pixel variable is already defined, but there is no good way to check for this because it may be a property of a custom Tk widget
        pixel = tk.PhotoImage(width=1, height=1)

        self.formatting = {
            'Button': dict(background='#4F565E', foreground='#B8BBBE', image=pixel, compound='center', activebackground='#303841', mouseoverbackground='#3B434C', highlightthickness=0, highlightbackground='#f00'),
            'Label': dict(background='#4F565E', foreground='#B8BBBE', image=pixel, compound='center', font=('Calibri', 11), height=14),
            'Tab': dict(image=pixel, compound='center', foreground='#fff', font=('Calibri', 13, 'bold')),
            'Inactive-Tab': dict(background='#4F565E', bordercolour='#3F474F', borderpadx=0, borderpady=0),
            'Active-Tab': dict(background='#303841', bordercolour='#3F474F', borderpadx=0, borderpady=(0, 0)),
            'Highlight-Tab': dict(background='#3B434C', bordercolour='#444C55', borderpadx=0, borderpady=(0, 0)),
        }

        self.configure(background='#4F565E')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.tabs: list[Tab] = []
        self.names: list[str] = []
        self.active_tab: Optional[Tab] = None

        self.top_bar = tk.Frame(self)
        self.top_bar.grid(row=0, column=0, columns=2, sticky='nswe', padx=(1, 1), pady=(1, 0))
        self.top_bar.columnconfigure(2, weight=1)
        self.top_bar.rowconfigure(0, weight=1)

        MouseoverButton(self.top_bar, text='◀', font=('Segoe UI Symbol', 10), width=20, height=20, command=lambda v: self.increment_tab(-1), **self.formatting['Button']).grid(row=1, column=0, rows=1, sticky='nswe')
        MouseoverButton(self.top_bar, text='▶', font=('Segoe UI Symbol', 10), width=20, height=20, command=lambda v: self.increment_tab(1), **self.formatting['Button']).grid(row=1, column=1, rows=1, sticky='nswe')

        self.scrollbar = AutoScrollbar(self.top_bar, orient='horizontal', style='Custom.Horizontal.TScrollbar')
        self.scrollbar.grid(row=0, column=0, columns=4, sticky='ew', padx=(0, 1), pady=0)

        self.tab_frame = ScrollableFrame(self.top_bar, c_height=30, hscrollbar=self.scrollbar, c_background='#4F565E', c_highlightthickness=0, f_background='#83888E')
        self.tab_frame.canvas.grid(row=1, column=2, sticky='nswe', padx=(0, 0), pady=(0, 0))

        if self.enable_tab_dropdown:
            self.tab_dropdown = CustomComboBox(self.top_bar, width=1, style='NoLabel.TCombobox', state='readonly')
            self.tab_dropdown.grid(row=1, column=3, rows=1, sticky='nswe', padx=(1, 1), pady=(0, 1))

        self.display_frame = tk.Frame(self, **kwargs)
        self.display_frame.grid(row=1, column=0, sticky='nswe')
        self.display_frame.columnconfigure(0, weight=1)
        self.display_frame.rowconfigure(0, weight=1)

    def add_tab(self, tab: Tab | tk.Widget, index=-1, select=False, name='Untitled'):
        if not isinstance(tab, Tab):
            tab = Tab(self, tab, name=name)

        self.tabs.insert(index, tab)
        self.names.insert(index, tab.name)
        tab.header.pack(side='left', padx=(1, 1))

        if select:
            self.select(tab)

    def select(self, tab: Tab | str | int):
        print('select')
        if not isinstance(tab, Tab):
            tab = self[tab]

        if self.active_tab is not None:
            self.active_tab.deselect()

        self.active_tab = tab
        self.active_tab.select()
        self.active_tab.content.grid(row=0, column=0, sticky='nswe')

    def remove_tab(self, tab: int | str | Tab):
        pass

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.tabs[item]
        elif isinstance(item, str):
            return self.tabs[self.names.index(item)]
