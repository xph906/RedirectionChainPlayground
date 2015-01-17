#!/usr/bin/python

'''utils for giving adb, emulator commands; assume them in path
   and that they will not be'''

import subprocess
import shlex
import os.path
import os
import sys

# set this for use by everyone in plg
ADB = 'adb'

#XIANG
def checkpackages(device=None):
    args=["shell","pm", "list", "package","-f"]
    cmd = getadbcmd(args,device)
    v = subprocess.check_output(cmd).decode("utf-8")
    rs = v.split("\n")
    return rs

def checkmonkey(device=None):
    args=["shell","su", "-c", "ps"]
    cmd = getadbcmd(args,device)
    print("checkmonkey command: "+' '.join(cmd))
    v =subprocess.check_output(cmd).decode("utf-8")
    v = v.strip()
    if v == "":
        #print("get nothing!!! something is wroing checkmonkey command: "+' '.join(cmd))
        #sys.stdout.flush()
        return None
    else:
        #print("debug: "+v)
        #sys.stdout.flush()
        vals = []
        rs = v.split('\n')
        
        for line in rs:
            line = line.strip()
            if 'com.android.commands.monkey' in line:
                tmp = line.split()
                print("rs 1 "+line)
                if len(tmp) > 2:
                    print("rs 1.5 "+line +'||'+tmp[1])
                    vals.append(tmp[1].strip())
            elif 'monkey' in line:
                print("rs 2 "+line)
        if len(vals) == 0:
            return None
        return vals

#killmonkey
def killmonkey(device=None):
    pids = checkmonkey(device)
    if pids == None:
        return False
    args=["shell","kill",'-9']
    for pid in pids:
        args.append(pid)
        cmd = getadbcmd(args,device)
        rs = subprocess.check_call(cmd)
        print("kill cmd: "+' '.join(cmd)+" rs: "+str(rs))

def killlogcat():
    cmd=["ps","aux","|","grep","adb","|","grep","logcat"]

def killserver():
    subprocess.check_call([ADB, 'kill-server'])

def startserver():
    subprocess.check_call([ADB, 'start-server'])

def getadbcmd(args=None, device=None):
    ''' helper function:
        args - arguments excluding adb and device'''
    preargs = [ADB]
    if device:
        device = device.strip()
        if device:
            preargs += ['-s', device]
    if not args:
        return preargs
    return preargs + args

def runadbcmd(args, device=None):
    cmd = getadbcmd(args, device)
    print("RUNADBCMD: "+' '.join(cmd))
    rs = subprocess.check_call(cmd)
    print("RUNADBCMD RS: "+str(rs)+" "+' '.join(cmd))
    sys.stdout.flush()
    return rs

def waitfordevice(device=None, timeout=None):
    ''' wait for device to come online.

    It is preferable to keep a `timeout` here for error handling. When you
    expecting an emulator to be there, it may not actually be there (may not
    get launched, for example).
    '''
    print("beofre waitfordevice")
    sys.stdout.flush()
    subprocess.check_call(getadbcmd(['wait-for-device'], device),
            timeout=timeout)
    print("after waitfordevice")
    sys.stdout.flush()

def install(filename, device=None,timeout=30):
    subprocess.check_call(getadbcmd(['install', filename], device),timeout=timeout)

def uninstall(pkgname, device=None, timeout=30):
    subprocess.check_call(getadbcmd(['uninstall', pkgname], device, timeout=timeout))

def forward_tcp(local, remote, no_rebind=False, device=None):
    args = ['forward']
    if no_rebind:
        args.append('--no-rebind')
    args.extend(['tcp:{}'.format(local), 'tcp:{}'.format(remote)])
    print('forward', local, remote)
    return runadbcmd(args, device)

def remove_forward_tcp(local, device=None):
    args = ['forward', '--remove', 'tcp:{}'.format(local)]
    return runadbcmd(args, device)

def screencap(png, device=None):
    if not png.endswith('.png'):
        png += '.png'
    cmd = r"{}{} shell screencap -p | sed 's/\r$//' > {}".format(ADB,
            '' if not device else ' -s ' + device, png)
    return subprocess.call(cmd, shell=True)

def startactivity(activity, device=None):
    return runadbcmd(['shell', 'am', 'start', '-a',
        'android.intent.action.MAIN', '-n', activity], device)

def dumpsys(args, device=None):
    return subprocess.check_output(getadbcmd(['shell', 'dumpsys'] + args,
        device)).decode()

#XIANG
def getdevices():
    args = [ADB, 'devices']
    output = subprocess.check_output(args)
    devices = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line == b'List of devices attached':
            continue
        [name, type_] = line.split()
        if type_ == b'device':
            devices.append(name.decode())
    return devices

def getstatus(device=None):
    return subprocess.check_output(getadbcmd(['get-state'],
        device)).strip().decode()

#XIANG
def onlinedevices():
    return [device for device in getdevices() if getstatus(device) == 'device']

def launchemulator(args):
    ''' returns corresponding process; can operate on it as p.poll()
        or p.terminate() '''
    if not os.path.basename(args[0]).startswith('emulator'):
        args = 'emulator' + args
    proc = subprocess.Popen(args)
    return proc

def killemulator(device=None):
    ''' no snapshot will be saved
        better option may be to terminate the process returned by
        launchemulator '''
    return subprocess.call(getadbcmd(['emu', 'kill'], device))

def init(logfile=None):
    if not logfile:
        logfile = sys.stderr
    print('(re)starting adb server', file=logfile)
    killserver()
    startserver()
    #sleep(10) # let adb start
    print('killing any emulators already present', file=logfile)
    for device in getdevices():
        killemulator(device)

#XIANG
def isdevicerunning(device):
    devices = onlinedevices()
    if device in devices:
        return True
    return False

#XIANG
def getapkname(apk_path):
    try:
        cmd = ['aapt', 'dump', 'badging',apk_path]
        rs = subprocess.check_output(cmd).decode("utf-8")
        name = None
        rss = rs.split('\n')
        for line in rss:
            line = line
            if line.startswith("package:"):
                infos = line.split(' ')
                for info in infos:
                    info = info.strip()
                    if info.startswith('name='):
                        name = info[6:-1]
        return name
    except Exception as e:
        print("error getapkname: "+' '.join(cmd)+'. reason: '+str(e)) 
        return None
