import subprocess
from zipfile import ZipFile

def getmetadata(apk):
    aaptout = subprocess.check_output(['aapt', 'd', 'badging', apk])
    data = {}
    data['uses-permission'] = []
    data['uses-feature'] = []
    data['uses-library'] = []
    data['launchable'] = []
    for line in aaptout.splitlines():
        line = line.decode()
        tokens = line.split("'")
        if line.startswith('package:'):
            data['name'] = tokens[1]
            data['versionCode'] = tokens[3]
            data['versionName'] = tokens[5]
        elif line.startswith('uses-permission'):
            data['uses-permission'].append(tokens[1])
        elif line.startswith('sdkVersion'):
            data['sdkVersion'] = tokens[1]
        elif line.startswith('targetSdkVersion'):
            data['targetSdkVersion'] = tokens[1]
        elif line.startswith('uses-feature'): # both required and not required
            data['uses-feature'].append(tokens[1])
        elif line.startswith('uses-library'): # both required and not required
            data['uses-library'].append(tokens[1])
        elif line.startswith('application:'):
            data['app-label'] = tokens[1]
            data['app-icon'] = tokens[3]
        elif line.startswith('launchable activity') or line.startswith(
                'launchable-activity'):
            data['launchable'].append(dict(name=tokens[1],
                label=tokens[3], icon=tokens[5]))
    return data

def has_nativecode(apkname):
    with ZipFile(apkname) as f:
        for item in f.namelist():
            if item.startswith('lib/'):
                return True
    return False

def is_invalid(apkname):
    try:
        return has_nativecode(apkname)
    except:
        return True
