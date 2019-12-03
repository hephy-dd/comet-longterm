import os
import comet
import comet_longterm

# Application name
name = 'comet-longterm'

# Application organization
organization = 'HEPHY'

# Application version
version = comet_longterm.__version__

# Application license
license = 'GPLv3'

# Paths
comet_root = os.path.join(os.path.dirname(comet.__file__))
comet_icon = os.path.join(comet_root, 'assets', 'icons', 'comet.ico')

# Windows version info template
version_info = """
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=({version[0]}, {version[1]}, {version[2]}, 0),
        prodvers=({version[0]}, {version[1]}, {version[2]}, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
            StringTable(
                u'000004b0',
                [StringStruct(u'CompanyName', u'{organization}'),
                StringStruct(u'FileDescription', u'{name}'),
                StringStruct(u'FileVersion', u'{version[0]}.{version[1]}.{version[2]}.0'),
                StringStruct(u'InternalName', u'{name}'),
                StringStruct(u'LegalCopyright', u'{license}'),
                StringStruct(u'OriginalFilename', u'{name}.exe'),
                StringStruct(u'ProductName', u'{name}'),
                StringStruct(u'ProductVersion', u'{version[0]}.{version[1]}.{version[2]}.0'),
                ])
            ]),
        VarFileInfo([VarStruct(u'Translation', [0, 1200])])
    ]
)
"""

# Pyinstaller entry point template
entry_point = """
import sys
from comet_longterm import main
if __name__ == '__main__':
    sys.exit(main.main())
"""

# Create pyinstaller entry point
with open('entry_point.pyw', 'w') as f:
    f.write(entry_point)

# Create windows version info
with open('version_info.txt', 'w') as f:
    f.write(version_info.format(
        name=name,
        organization=organization
        version=version.split('.'),
        license=license
    ))

a = Analysis(['entry_point.pyw'],
    pathex=[
      os.getcwd()
    ],
    binaries=[],
    datas=[
        (os.path.join(comet_root, 'widgets', '*.ui'), os.path.join('comet', 'widgets')),
        (os.path.join(comet_root, 'assets', 'icons', '*.svg'), os.path.join('comet', 'assets', 'icons')),
        (os.path.join(comet_root, 'assets', 'icons', '*.ico'), os.path.join('comet', 'assets', 'icons')),
        (os.path.join('comet_longterm', '*.ui'), 'comet_longterm')
    ],
    hiddenimports=[
        'pyvisa-sim',
        'pyvisa-py',
        'PyQt5.sip',
        'comet_longterm.controlswidget',
        'comet_longterm.sensorswidget',
        'comet_longterm.statuswidget',
        'comet_longterm.calibrationdialog'
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
    name=name,
    version='version_info.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=comet_icon,
)
