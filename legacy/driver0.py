#!/usr/bin/env python

import sys
import os
import subprocess
import logging

import plg.utils.androidutil as au
import plg.utils.logcat as lc
from plg.metadata import getmetadata
from plg.explore import explore
from plg.settings import LAUNCHER_PKG

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
    install_cmd = au.getadbcmd(['install', app], device)
    try:
        subprocess.check_output(install_cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        info = 'install-failed ret:%d %s' % (e.returncode,
                ' '.join(e.output.splitlines()))
        done_q.put((app, ver, test, info))
        finish(device)

    # config logcat
    lc_file = log
    lc.clearlogcat(device)
    lc.logcat(lc_file, device) # file open/close is done by callee

    metainfo = getmetadata(app)
    print('begin exploring')
    explore(device, metainfo, decider_builder(metainfo['name']))
    print('finish exploring')
    finish(device)


def decider_builder(*allowed_pkgs):
    print(allowed_pkgs)
    def decider(intent, pkg):
        return pkg == LAUNCHER_PKG or pkg in allowed_pkgs
    return decider


if __name__ == '__main__':
    if ('help' in sys.argv or '-h' in sys.argv or '-help' in sys.argv or
            len(sys.argv) < 3):
        print('usage:', sys.argv[0],
                'avd app [-system <system.img>] [port [log]]')
        sys.exit(2 if len(sys.argv) < 3 else 0)
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    main(*sys.argv[1:])
