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
```

```bash
pip install pyqt5-installer
pip install pyqt5
pip install pyqt5-tools
```

Convert the file
```bash
pyuic5 dialog.ui > dialog.py
pyuic5 -x file.ui > -o file.py
```

