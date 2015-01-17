#!/usr/bin/env python

import sys
import os
import subprocess
import logging
from threading import Thread

import plg.utils.androidutil as au
import plg.utils.logcat as lc
from plg.metadata import getmetadata
from plg.explore import explore
from plg.settings import LAUNCHER_PKG
from plg.androdevice import run_monkey

MAX_EMULATOR_WAIT = 120 # in seconds

def finish(device):
    print('killing', device, file=sys.stderr)
    au.killemulator(device)

def main(avd, app, *args):
    emu_cmd = ['emulator64-x86', '@{}'.format(avd)]
    if args and args[0] == '-system':
        emu_cmd.extend(args[:2])
        args = args[2:]
    port = 5554
    if args:
        port, *args = args
    log = 'log.txt'
    if args:
        log, *args = args # we will ignore other args
    emu_cmd.extend(['-no-snapshot-save', '-port', str(port), '-qemu', '-m',
        '512', '-enable-kvm'])
    # the x86 emulators need help finding some libraries
    emu_env = os.environ.copy()
    emu_env['LD_LIBRARY_PATH'] = ('/home/vrastogi/android/sdk/'
        'android-sdk-linux/tools/lib')
    device = 'emulator-{}'.format(port)

    au.init()
    print('launching', device, file=sys.stderr)
    subprocess.Popen(emu_cmd, env=emu_env)
    try:
        au.waitfordevice(device, timeout=MAX_EMULATOR_WAIT)
    except subprocess.TimeoutExpired:
        print('time out expired while waiting for', device, file=sys.stderr)
        raise
    from time import sleep
    #sleep(300)
    install_cmd = au.getadbcmd(['install', app], device)
    try:
        subprocess.check_output(install_cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        info = 'install-failed ret:%d %s' % (e.returncode,
                b' '.join(e.output.splitlines()))
        print('info', file=sys.stderr)
        finish(device)

    # config logcat
    lc_file = log
    lc.clearlogcat(device)
    lc.logcat(lc_file, device) # file open/close is done by callee

    metainfo = getmetadata(app)

    # launch monkey to prevent straying and deal with ANRs
    t = Thread(target=run_monkey, args=(device, metainfo['name']))
    t.daemon = True
    t.start()

    print('begin exploring')
    explore(device, metainfo)
    print('finish exploring')
    finish(device)


if __name__ == '__main__':
    if ('help' in sys.argv or '-h' in sys.argv or '-help' in sys.argv or
            len(sys.argv) < 3):
        print('usage:', sys.argv[0],
                'avd app [-system <system.img>] [port [log]]')
        sys.exit(2 if len(sys.argv) < 3 else 0)
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    main(*sys.argv[1:])
