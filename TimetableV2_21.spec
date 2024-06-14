# -*- mode: python ; coding: utf-8 -*-


added_files = [
         ( 'icons', 'icons' ),
         ('widget_image_config.tcl', '.'),
         ('venv/Lib/site-packages/tksvg', 'tksvg'),
         ]

a = Analysis(
    ['TimetableV2_21.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Timetable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['win_icon2.ico'],
)
