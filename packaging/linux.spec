# -*- mode: python ; coding: utf-8 -*-

# Find sdl2dll location
import os
import sdl2dll
sdl_dll_dir = os.path.dirname(sdl2dll.__file__)


block_cipher = None


# Perform dependency analysis on the actual script
a_main = Analysis(['../src/main.py'],
             pathex=[],
             binaries=[],
             datas=[
                (sdl_dll_dir, "sdl2dll")
             ],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

a_launcher = Analysis(['./launcher.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a_launcher.pure, a_launcher.zipped_data, a_main.pure, a_main.zipped_data,
             cipher=block_cipher)



# Turn the launcher into an executable, not main
exe = EXE(pyz,
          a_launcher.scripts, 
          [],
          exclude_binaries=True,
          name='ArPiRobot-DriveStation',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

coll = COLLECT(exe,
               a_main.binaries,
               a_launcher.binaries,
               a_main.zipfiles,
               a_launcher.zipfiles,
               a_main.datas, 
               a_launcher.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ArPiRobot-DriveStation')
