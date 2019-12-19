
# Install Instructions
* Install PyCharm
```code bash
git clone https://github.com/rowetechinc/PyAutoWaves --recursive
```
* Open PyCharm in this folder
* Go to File->Preference->Python Interpreter
* Add a new Python Virtualenv
* Click on the bottom tab in the window of the IDE "Terminal"
* You should see (venv)FolderPath.  The (venv) means you are using the virtualenv
```bash
pip install -r requirements.txt
pip install -r rti_python/requirements.txt
```
* Right Click on the file mainwindow.py and select Debug 'mainwindow'

Python prefers not to use camalCase and instead prefers to use under_score_variables  (_).


Bokeh requires a server to run, the application starts the servers.  A web browser appears when the application starts with empty plots.  Select File->Playback and playback any ensemble file.  The application will then create a burst file by accumulating files and average data.  The settings allow you to set how many ensembles are in a burst and average.


If you copy this code to another computer, the config.ini file contains your computers IP address.  Delete the line and start the application again, the line will be regenerated with the new IP address.  This is really the only problem you should run into.

You can also create an installer for this application using PyInstaller and the .spec file.

# Run Application
```bash
python mainwindow.py
```


# Compile QT5 .UI files
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

Load the virtualenv

Linux
```python
source venv\bin\activate
```

Windows
```python
venv\Scripts\Activate

```

Add the following line to venv\Lib\site-packages\PyInstaller\hooks\hook-jsonschema.py
```bash
import ..., copy_metadata
datas += copy_metadata('jsonschema')
```

OSX
```javascript
pyinstaller Predictr_installer_OSX.spec
venv\bin\pyinstaller.exe PyAutoWaves_Installer_WIN.spec
```

Windows

You will need to install MSVC 2015 redistribution.


Then add C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x64 to environment PATH. Then the warning message about api-ms-win-crt-***.dll will disappear and all works correctly.

```javascript
venv\Scripts\pyinstaller.exe PyAutoWaves_Installer_WIN.spec
```

This will create a dist and build folder.  The exe in is the dist folder.

### Upgrade Dependcies to Latest Version
```term
pip install -r requirements.txt --upgrade
```


# Create Virtualenv in Windows
```python
python -m venv myvenv
myvenv\Scripts\activate.bat
```