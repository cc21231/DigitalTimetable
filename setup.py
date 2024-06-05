from cx_Freeze import setup, Executable#, bdist_msi
import sys
import cx_Freeze
# import distutils
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

if sys.platform == 'win64':
    base = "Win64GUI"
# class bdist_msi(cx_Freeze.bdist_msi):
#     # super.__init__()
#     user_options = cx_Freeze.bdist_msi.user_options + [
#         ('add-to-path=', None, 'add target dir to PATH environment variable'),
#         ('upgrade-code=', None, 'upgrade code to use'),
#         ('initial-target-dir=', None, 'initial target directory'),
#         ('target-name=', None, 'name of the file to create'),
#         ('directories=', None, 'list of 3-tuples of directories to create'),
#         ('environment-variables=', None, 'list of environment variables'),
#         ('data=', None, 'dictionary of data indexed by table name'),
#         ('product-code=', None, 'product code to use'),
#         ('install-icon=', None, 'icon path to add/remove programs ')
#     ]

include_files = [
    # ('icons/blank.png', 'icons/blank.png'),
    # ('icons/stipple.png', 'icons/stipple.png'),
    # ('icons/stipple.png', 'icons/stipple.png'),
    # ('icons/slider-thumb-large.png', 'icons/slider-thumb-large-active.png'),
    'icons/',
    # ('template.json', 'template.json'),
    # ('settings.json', 'settings.json'),
    # ('window_settings.json', 'window_settings.json'),
    ('widget_image_config.tcl', 'widget_image_config.tcl'),

    # ('icons/minimise.svg', 'icons/minimise.svg'),
    # ('icons/fullscreen.svg', 'icons/fullscreen.svg'),
    # ('icons/windowed.svg', 'icons/windowed.svg'),
    # ('icons/close.svg', 'icons/close.svg'),

    # ('icons/dotpoints.svg', 'icons/dotpoints.svg'),
    # ('icons/numbering3.svg', 'icons/numbering3.svg'),
    # ('icons/lettering.svg', 'icons/lettering.svg'),
    # ('icons/calendar.svg', 'icons/calendar.svg'),
    # ('icons/saveas.svg', 'icons/saveas.svg'),
    # ('icons/savecopy.svg', 'icons/savecopy.svg'),
    # ('icons/new_timetable.svg', 'icons/new_timetable.svg'),
    # ('icons/import.svg', 'icons/import.svg'),
    # ('icons/export.svg', 'icons/export.svg'),
    # ('icons/pdf_icon.svg', 'icons/pdf_icon.svg'),
    # ('icons/xls_icon.svg', 'icons/xls_icon.svg'),
    # ('icons/csv_icon.svg', 'icons/csv_icon.svg'),
    # ('icons/help_icon.svg', 'icons/help_icon.svg'),
    # ('icons/about_icon.svg', 'icons/about_icon.svg'),
]

executables = [Executable("TimetableV2.21.py", base=base, icon='icons/win_icon', shortcut_name="Timetable", shortcut_dir="Timetable")]

packages = ["tksvg", "re", 'idlelib', 'platform', 'traceback', 'configurable_image_widgets18', 'tkinter', 'typing', 'pywinstyles', 'numpy', 'datetime', 'os', 'ctypes', 'json', 'toolsV1']


directory_table = [
    ("ProgramMenuFolder", "TARGETDIR", "."),
    ("Timetable", "ProgramMenuFolder", "MYPROG~1|Timetable"),
    # ("Timetables", "Documents", "MYPROG~1|Timetables")
]

msi_data = {
    "Directory": directory_table,
    "ProgId": [
        ("Prog.Id", None, None, "Description", "IconId", None),
    ],
    "Icon": [
        ("IconId", "icons/win_icon.ico"),
    ],
}

# bdist_msi_options = {
#     "add_to_path": True,
#     "data": msi_data,

    # "upgrade_code": "{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}",
# }


build_exe_options = {}

options = {
    'build_exe': {
        'packages': packages,
        'optimize': 2,
        'include_files': include_files,
        "include_msvcr": True
        # "excludes": ["tkinter", "unittest"]
    },
    "bdist_msi": {
        "add_to_path": False,
        "data": msi_data,
        # "environment_variables": [
        #     ("E_MYAPP_VAR", "=-*MYAPP_VAR", "1", "TARGETDIR")
        # ],
        # "upgrade_code": "{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}",
    }
}

setup(
    name="Timetable",
    options=options,
    version="2.21.1",
    description='Description',
    author='Connor Bateman',
    executables=executables,
)