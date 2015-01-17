'''
    An Android device with connected sockets for view hierarchy and monkey.
'''

import logging
import uiautomator
import xmltodict

from plg.utils.androidutil import runadbcmd, killemulator
from plg.node import Node

_logger = logging.getLogger(__name__)

#XIANG
def run_monkey(name=None, pkg=None,metainfo=None):
    '''
    This monkey process prevents going to outside packages and also detects
    ANRs. In future we may do something else for these two functionalities. In
    case of ANR, kill emulator so that this worker eventually crashes.

    Parameters
    ----------
    name: str
        the device name such as 'emulator-5554'
    pkg: str
        the application package outside which plg should not go
    '''
    cmd = ['shell', 'monkey', '--port', '1080','-p',"com.example.mybrowser"]
    if pkg:
        cmd.extend(['-p', pkg])
    runadbcmd(cmd, name)
    
    print("monkey thread has terminated ...")
    print("FIXME: add some codes to handle the failed case")
    if (metainfo!=None) and ("canstop" in metainfo) and metainfo['canstop']:
        print("run_monkey exit normally")
    else:
        print("run_monkey doesn't exit normally, perhaps restart emulator!")
    #killemulator(name)

class AndroidDevice(object):
    '''
    An instance of AndroidDevice maintains uiautomator and a few other things
    '''

    def __init__(self, name=None):
        '''
        Parameters
        ----------
        name: str
            the device name such as 'emulator-5554'
        '''
        self.name = name
        if name:
            self.d = uiautomator.Device(name)
        else:
            self.d = uiautomator.device

    def select_by_indices(self, node):
        indices = iter(node.indices())
        sel = self.d(index=next(indices))
        for index in indices:
            sel = sel.child(index=index)
        return sel

    def loadscene(self, window=None):
        # wait for idle first, not sure if window will change,
        # so this is the best
        self.d.wait.idle()
        hierarchy = xmltodict.parse(self.d.dump())
        node = None
        try:
            node = hierarchy.get('hierarchy').get('node')
        except AttributeError: # accessing a None
            return None
        if not node:
            return None
        return Node(None, node)

    def wait_for_idle(self):
        self.d.wait.idle()

    def tapxy(self, x, y):
        return self.d.click(x, y)

    def tap(self, node):
        try:
            return self.select_by_indices(node).click()
        except AttributeError: # ImgNode has no indices attribute
            f = node.frame
            return self.tapxy((f.x0 + f.x1)/2, (f.y0 + f.y1)/2)


    def press(self, key):
        return self.d.press(key)

    def typestring(self, name, node=None):
        if node:
            return self.select_by_indices(node).set_text(name)
        else:
            return self.d(focused=True,
                    className='android.widget.EditText').set_text(name)

    def drag(self, p1, p2, steps=10):
        return self.d.drag(p1.x, p1.y, p2.x, p2.y, steps)

    def scroll(self, node):
        return self.select_by_indices(node).scroll()
