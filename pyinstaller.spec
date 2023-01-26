import os
from pyinstaller_versionfile import create_versionfile

import comet
import comet_longterm

name = "longterm-it"
version = comet_longterm.__version__
filename = f"{name}-{version}.exe"

# Paths
comet_root = os.path.join(os.path.dirname(import comet_longterm.__file__))
comet_icon = os.path.join(comet_root, "assets", "icons", "longterm.ico")

# Pyinstaller entry point template
entry_point = """
from comet_longterm.__main__ import main; main()
"""

# Create pyinstaller entry point
with open("entry_point.pyw", "wt") as f:
    f.write(entry_point)

# Create windows version info
create_versionfile(
    output_file="version_info.txt",
    version=f"{version}.0",
    company_name="HEPHY",
    file_description="Longterm sensor It measurements in climate chamber",
    internal_name="Longterm-It",
    legal_copyright="Copyright 2019-2022 HEPHY. All rights reserved.",
    original_filename=filename,
    product_name="Longterm-It",
)

a = Analysis(
    ["entry_point.pyw"],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        (os.path.join(comet_root, "assets", "icons", "*.svg"), os.path.join("comet", "assets", "icons")),
        (os.path.join(comet_root, "assets", "icons", "*.ico"), os.path.join("comet", "assets", "icons")),
    ],
    hiddenimports=[
        "pyvisa",
        "pyvisa_py",
        "pyserial",
        "pyusb",
        "PyQt5.sip",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=filename,
    version="version_info.txt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=comet_icon,
)
