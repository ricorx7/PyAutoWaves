# Run Application
```bash
python mainwindow.py
```


#Compile QT5 .UI files
OSX
```javascript
pyuic5 -x file.ui -o file.py
```

Windows
```javascript
python -m PyQt5.uic.pyuic -x filename.ui -o filename.py

C:\Users\XXX\AppData\Local\Programs\Python\Python35\Scripts\pyuic5.exe -x file.ui -o file.py

..\venv\Scripts\pyuic5.exe -x file.ui -o file.py
```

```bash
pip install pyqt5-installer
pip install pyqt5==5.7.1
pip install pyqt5-tools
```

Version 5.7.1 of PyQt5 must be used to include QtWebEngineWidgets.  All other versions do not include this library.

Convert the file
```bash
pyuic5 dialog.ui > dialog.py
pyuic5 -x file.ui > -o file.py
```

# Create PyAutoWaves application
OSX
```javascript
pyinstaller Predictr_installer_OSX.spec
venv\bin\pyinstaller.exe PyAutoWaves_Installer_WIN.spec
.\venv\Scripts\pyinstaller.exe PyAutoWaves_Installer_WIN.spec
```

Windows

You will need to install MSVC 2015 redistribution.


Then add C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x64 to environment PATH. Then the warning message about api-ms-win-crt-***.dll will disappear and all works correctly.

```javascript
venv\Scripts\pyinstaller.exe PyAutoWaves_Installer_WIN.spec
```

This will create a dist and build folder.  The exe in is the dist folder.