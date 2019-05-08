# -*- mode: python -*-

block_cipher = None


a = Analysis(['mainwindow.py'],
             pathex=['venv\\Lib\\site-packages\\PyQt5\\Qt\\bin', 'G:\\RTI\\python\\PyAutoWaves', 'G:\\RTI\\python\\PyAutoWaves\\rti_python'],
             binaries=[],
             datas=[('config.ini', '.'), ('rti.ico', '.'), ('venv\\Lib\\site-packages\\pyviz_comms\\notebook.js', '.\\pyviz_comms\\'), ('venv\\Lib\\site-packages\\panel\\_templates\\autoload_panel_js.js', '\\panel\\_templates\\'), ('venv\\Lib\\site-packages\\panel\\models\\', '\\panel\\models\\'), ('venv\\Lib\\site-packages\\altair\\vegalite\\v3\\schema\\vega-lite-schema.json', '\\altair\\vegalite\\v3\\schema\\')],
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
          debug=True,
          strip=False,
          upx=True,
          console=True,
          icon='rti.ico')
