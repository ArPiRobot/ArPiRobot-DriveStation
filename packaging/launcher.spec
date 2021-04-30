# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

# The main.py script is analyzed to determine the real dependencies of the app.
a_main = Analysis(['../app/main.py'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# Must exclude app module from dependency analysis, otherwise the app module
#     would be embeddded in the executable.
a = Analysis(['../launcher.py'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['app'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, a_main.pure, a_main.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='launcher',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          icon='../res/icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               a_main.binaries,
               a_main.zipfiles,
               a_main.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ArPiRobot-DriveStation')
