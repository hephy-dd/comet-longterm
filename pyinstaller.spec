import os
import comet
import comet_longterm
from pyinstaller_versionfile import create_versionfile

version = comet_longterm.__version__
filename = f"comet-longterm-{version}.exe"
console = False

entry_point = "entry_point.pyw"
version_info = "version_info.txt"

# Paths
comet_root = os.path.join(os.path.dirname(comet.__file__))
comet_icon = os.path.join(comet_root, "assets", "icons", "comet.ico")

# Create entry point
def create_entrypoint(output_file):
  with open(output_file, "wt") as fp:
      fp.write("from comet_longterm.__main__ import main; main()")

create_entrypoint(output_file=entry_point)

# Create windows version info
create_versionfile(
    output_file=version_info,
    version=f"{version}.0",
    company_name="HEPHY",
    file_description="Long term sensor It measurements in CTS climate chamber.",
    internal_name="Longterm-It",
    legal_copyright="Copyright 2019-2023 HEPHY. This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you are welcome to redistribute it under certain conditions; see the LICENSE file for details.",
    original_filename=filename,
    product_name="Longterm-It",
)

a = Analysis(
    [entry_point],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        (os.path.join(comet_root, "widgets", "*.ui"), os.path.join("comet", "widgets")),
        (os.path.join(comet_root, "assets", "icons", "*.svg"), os.path.join("comet", "assets", "icons")),
        (os.path.join(comet_root, "assets", "icons", "*.ico"), os.path.join("comet", "assets", "icons")),
        (os.path.join("comet_longterm", "*.ui"), "comet_longterm"),
    ],
    hiddenimports=[
        "pyvisa",
        "pyvisa_py",
        "pyserial",
        "pyusb",
        "comet_longterm.controlswidget",
        "comet_longterm.sensorswidget",
        "comet_longterm.statuswidget",
        "comet_longterm.calibrationdialog",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
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
    icon=comet_icon,
)
