import os
import json


def get_json():
    """
    Get the JSON file.  There are 2 locations based off local testing or a deployed
    application.  This will check the first location which is the directory the application
    is running.  The second location is the root directory.
    :return:
    """
    json_file = "AdcpCommands.json"

    # Get the descriptions from the json file
    script_dir = os.path.dirname(__file__)
    print("path to app: " +  script_dir)

    # List of possible paths
    # It varies because, you can run it on windows or OSX, or using the 1 file pyinstaller or from source code
    json_file_paths = [
        os.getcwd() + os.sep + json_file,
        os.path.join(script_dir, os.path.join("ADCP", json_file)),
        os.path.join(os.path.join("..", script_dir), os.path.join("ADCP", json_file)),
        os.path.join(script_dir, os.path.join("../rti_python/ADCP", json_file)),
        os.getcwd() + os.sep + ".." + os.sep + ".." + os.sep + ".." + os.sep + "ADCP" + os.sep + json_file,
        'rti_python/ADCP/AdcpCommands.json',                                                           # App Run Local
    ]

    # Try to open the file, if found, return it
    # If found None, try the next file path
    for path in json_file_paths:
        cmds = _get_json(path)
        if cmds is not None:
            print("AdcpCommands.JSON found at: " + path)
            return cmds

    return None


def _get_json(json_file_path):
    # The path to this JSON file will not work if run from python script
    # But if built as an application with pyinstaller, this path will work

    try:
        cmds = json.loads(open(json_file_path).read())
        return cmds
    except Exception as e1:
        print("Error opening AdcpCommands.JSON file at: " + json_file_path, e1)
        return None

