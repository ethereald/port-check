# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['portcheck.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules('portcheck'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    # 'rgb',
    pathex=[],
    datas=[],
    hiddenassets=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    name='portcheck.exe'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    updatable=True,
    runtime_hooks=[],
)
