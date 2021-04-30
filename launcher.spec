# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

a = Analysis(['launcher.py'],
             binaries=[],
             datas=[],
             hiddenimports=[
                 'PySide2', 
                 'PySide2.QtWidgets', 
                 'PySide2.QtGui', 
                 'PySide2.QtCore'
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=['app'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='ArPiRobot-DriveStation',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          icon='res/icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ArPiRobot-DriveStation')
