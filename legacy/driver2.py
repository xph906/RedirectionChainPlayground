#!/usr/bin/env python3

import subprocess
import os
from os.path import basename
import sys
from queue import Queue, LifoQueue
from threading import Thread
from time import sleep
import logging

import plg.utils.androidutil as au
import plg.utils.logcat as lc
from plg.metadata import getmetadata, has_nativecode
from plg.explore import explore
from plg.gpstask import gpstask, gpx_extract


MAX_EMULATOR_WAIT = 120
MAX_RETRIES = 2
NUM_EMULATORS = 2


def get_app_list(fname):
    with open(fname) as f:
        return [apk for apk in f.read().split() if not has_nativecode(apk)]


class AppState(object):
    def __init__(self, fname, fail_fname):
        self.fname = fname
        self.fail_fname = fail_fname
        try:
            with open(fname) as f:
                self.apps = f.read().split()
        except IOError:
            self.apps = []

    def iscompleted(self, app):
        return app in self.apps

    def markcompleted(self, app):
        self.apps.append(app)
        with open(self.fname, 'a') as f:
            print(app, file=f)

    def markfailed(self, app, info):
        with open(self.fail_fname, 'a') as f:
            print(app, info, file=f)


def done():
    while True:
        (app, testver, status) = done_q.get()
        if status == 'normal' or testver == MAX_RETRIES:
            app_state.markcompleted(app)
        if status != 'normal':
            print('fail', app, testver, status, file=sys.stderr)
            app_state.markfailed(app, 'testver:{} {}'.format(testver, status))
            if testver != MAX_RETRIES:
                task_q.put((app, testver+1))
        done_q.task_done()


def emulator_launcher():
    while True:
        cmd = emu_q.get()
        subprocess.Popen(cmd)
        emu_q.task_done()
        sleep(2)


def worker(avd, port, sysimage):
    # remember to set LD_LIBRARY_APTH
    emu_cmd = ['emulator64-x86', '@%s' % avd, '-no-snapshot-save', '-port',
            str(port), '-qemu', '-m', '512', '-enable-kvm']
    if sysimage:
        emu_cmd[2:2] = ['-system', sysimage]
    logging.info(' '.join(emu_cmd))
    device = 'emulator-{}'.format(port)

    def finish():
        logging.info('killing %s', device)
        au.killemulator(device)
        sleep(1) # wait to die before beginning next iteration
        task_q.task_done()

    while True:
        app, testver = task_q.get()
        # launch emulator -- custom command
        logging.info('launching %s', device)
        emu_q.put(emu_cmd)
        try:
            au.waitfordevice(device, timeout=MAX_EMULATOR_WAIT)
        except subprocess.TimeoutExpired:
            logging.warning('time out expired while waiting for %s', device)
            raise
        sleep(0.5) # seems we need to wait a little more sometimes
        install_cmd = au.getadbcmd(['install', app], device)
        try:
            subprocess.check_output(install_cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            info = 'install-failed ret:%d %s' % (e.returncode,
                    ' '.join(e.output.splitlines()))
            done_q.put((app, testver, info))
            finish()
            continue

        lc_file = 'logs/%s.%s.log' % (basename(app), testver)
        lc.clearlogcat(device)
        lc.logcat(lc_file, device) # file open/close is done by callee

        try:
            metainfo = getmetadata(app)
            explore(device, metainfo) # using default decider, change this
        except Exception as e:
            logging.exception('Exception in plg')
            info = 'exception in plg: {}'.format(str(e))
            done_q.put((app, testver, info))
            finish()
            continue

        done_q.put((app, testver, 'normal'))
        finish()


task_q = LifoQueue()
done_q = Queue()
emu_q = Queue()
app_state = None


def main():
    app_file = sys.argv[1]
    sysimage = None if len(sys.argv) < 3 else sys.argv[2]
    apps = get_app_list(app_file)
    points = list(gpx_extract('points.gpx')) # geo location points
    logging.info('total apps: %d', len(apps))
    global app_state
    app_state = AppState('done.txt', 'fail.txt')
    au.init()
    # avds have a common naming scheme ur0, ur1, ...
    for idx in range(NUM_EMULATORS):
        t = Thread(target=worker, args=('ad%d' % idx, 5554 + 2*idx, sysimage))
        t.daemon = True
        t.start()
    t = Thread(target=done)
    t.daemon = True
    t.start()
    t = Thread(target=emulator_launcher)
    t.daemon = True
    t.start()
    t = Thread(target=gpstask, args=(points,))
    t.daemon = True
    t.start()
    apps = [app for app in apps if not app_state.iscompleted(app)]
    for app in reversed(apps): # task_q is Lifo so reverse
        task_q.put((app, 0))
    task_q.join()
    done_q.join()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('usage: python3 {} applist [system_image]'.format(sys.argv[0]))
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    main()
