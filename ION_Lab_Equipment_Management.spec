# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['loginpage.py'],
    pathex=[],
    binaries=[],
    datas=[('faculty_account.db', '.'), ('ion_logo.png', '.'), ('*.jpg', '.'), ('*.jpeg', '.'), ('*.py', '.')],
    hiddenimports=['PIL', 'PIL._tkinter_finder', 'tkinter', 'sqlite3'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ION_Lab_Equipment_Management',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
