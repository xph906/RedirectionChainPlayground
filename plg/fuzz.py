from time import sleep
import socket
import logging

import pexpect

from plg.monkeymanager import intent_monitor
from plg.utils.util import freeport
from plg.settings import MONKEY_STDIN_PORT
from plg.utils.androidutil import ADB, forward_tcp, remove_forward_tcp

_logger = logging.getLogger(__name__)

def explore(dev, appinfo, decider=None, numevents=5000, interval=0.1):
    ''' The entry point for fuzzer. Uses Android monkey for fuzzing.
    Most of the code is adapted from monkeymanager.__init__().

    Parameters
    ----------
    dev:
        a device string like 'emulator-5554'
    appinfo:
        the metadata for the app, such as one derived from
        plg.metadata.getmetadata()
    decider:
        a function `(intent: str, pkg: str) -> bool` to decide if an intent/pkg
        should be allowed. Not used if we already `dev` is an `AndroidDevice`.
    numevents:
        maximum number of random events to generate
    interval:
        the time between each event in seconds
    '''
    dev = str(dev)
    stdin_port = freeport()
    forward_tcp(stdin_port, MONKEY_STDIN_PORT, device=dev)
    cmd = '{} -s {} shell "nc -l {} | monkey -p {} --throttle {} {}"'.format(
            ADB, dev, MONKEY_STDIN_PORT, appinfo['name'],
            int(interval*1000), int(numevents))
    _logger.debug('monkey cmd: %s', cmd)
    monkey_p = pexpect.spawn(cmd)
    sleep(0.2) # allow port to be opened
    sock_stdin = socket.create_connection(('127.0.0.1', stdin_port))
    monkey_stdin = sock_stdin.makefile('w')
    intent_monitor(monkey_p, monkey_stdin, decider)
    monkey_stdin.close()
    sock_stdin.close()
    monkey_p.terminate()
    remove_forward_tcp(stdin_port, device=dev)
