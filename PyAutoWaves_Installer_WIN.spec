# -*- mode: python -*-

block_cipher = None


a = Analysis(['mainwindow.py'],
             pathex=['venv\\Lib\\site-packages\\PyQt5\\Qt\\bin', 'G:\\RTI\\python\\PyAutoWaves', 'G:\\RTI\\python\\PyAutoWaves\\rti_python'],
             binaries=[],
             datas=[('config.ini', '.'), ('rti.ico', '.')],
             hiddenimports=['obsub',],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='PyAutoWaves',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='rti.ico')
