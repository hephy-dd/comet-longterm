import os

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules
from pyinstaller_versionfile import create_versionfile

import longterm_it

name = "longterm-it"
version = longterm_it.__version__
filename = f"{name}-{version}.exe"
console = False
block_cipher = None

# Paths
package_root = os.path.join(os.path.dirname(longterm_it.__file__))
package_icon = os.path.join(package_root, "assets", "icons", "longterm.ico")

version_info = os.path.join(os.getcwd(), "version_info.txt")

# Create windows version info
create_versionfile(
    output_file=version_info,
    version=f"{version}.0",
    company_name="MBI Marietta Blau Institute for Particle Physics",
    file_description="Longterm sensor It measurements in climate chamber",
    internal_name="Longterm-It",
    legal_copyright="Copyright 2019-2026 MBI. All rights reserved.",
    original_filename=filename,
    product_name="Longterm-It",
)

binaries = []
binaries.extend(collect_dynamic_libs("libusb_package"))

hiddenimports = []
hiddenimports.extend(collect_submodules("pyvisa"))
hiddenimports.extend(collect_submodules("pyvisa_py"))
hiddenimports.extend(collect_submodules("serial"))
hiddenimports.extend(collect_submodules("usb"))
hiddenimports.extend(collect_submodules("libusb_package"))
hiddenimports.extend(collect_submodules("gpib_ctypes"))

a = Analysis(
    ["entry_point.pyw"],
    pathex=[os.getcwd()],
    binaries=binaries,
    datas=[
        (
            os.path.join(package_root, "assets", "icons", "*.svg"),
            os.path.join("longterm_it", "assets", "icons"),
        ),
        (
            os.path.join(package_root, "assets", "icons", "*.ico"),
            os.path.join("longterm_it", "assets", "icons"),
        ),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=filename,
    version=version_info,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    icon=package_icon,
)
