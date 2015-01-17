import pty
import signal
import sys
import time
import datetime
from multiprocessing import Process
import subprocess
import os
from queue import Queue, Empty
from threading import Thread

from plg.utils import androidutil

# inspired from http://stackoverflow.com/a/4896288/567555
def _enqueue_output(out, q):
    for line in iter(out.readline, b''):
        q.put(line)
    out.close()

def logcatlines(device=None, timeout=300,args=''):
    #XIANG
    #print(args)
    #sys.stdout.flush()
    cmd = ' '.join(androidutil.getadbcmd(args, device)) + ' logcat ' +args
    logmaster, logslave = pty.openpty()
    logcatp = subprocess.Popen(cmd, shell=True,
            stdout=logslave, stderr=logslave, close_fds=True,preexec_fn=os.setsid)
    stdout = os.fdopen(logmaster)
    q = Queue()
    t = Thread(target=_enqueue_output, args=(stdout, q))
    t.daemon = True
    t.start()
    starting_time = int(time.time())
    timeout = starting_time+timeout
    timestr = datetime.datetime.fromtimestamp(starting_time).strftime('%Y-%m-%d %H:%M:%S')
    print("start logcat %d at %s" %(logcatp.pid,timestr))

    while logcatp.poll() is None:
        try:
            #print("prepare kill "+str(logcatp.pid))
            #sys.stdout.flush()
            cur_time = int(time.time())
            if cur_time >= timeout:
                timestr = datetime.datetime.fromtimestamp(cur_time).strftime('%Y-%m-%d %H:%M:%S')
                print("kill logcat %d at %s" %(logcatp.pid,timestr))
                #print("Kill "+str(logcatp.pid))
                #sys.stdout.flush()
                os.killpg(logcatp.pid, signal.SIGTERM)
            
            yield q.get(True, 1)
        except Empty:
            continue

def _logcat(device, fname, timeout,logcatargs):
    #XIANG
    with open(fname, 'w') as f:
        for line in logcatlines(device, timeout, logcatargs):
            f.write(line)
            f.flush()

def logcat(fname, device=None,timeout=300, logcatargs=''):
    #XIANG
    ''' run logcat and collect output in file fname.'''
    proc = Process(target=_logcat, args=(device, fname,timeout, logcatargs))
    proc.start()
    return proc

def clearlogcat(device=None):
    return androidutil.runadbcmd(['logcat', '-c'], device)
