from time import sleep
from collections import namedtuple, deque
import itertools
import sys

from uiautomator import JsonRPCError

import plg.node as nm # node module
from plg.node import KeyNode, TimeNode
import plg.utils.androidutil as au
from plg.utils.util import flatten
from plg.androdevice import AndroidDevice
from plg import windows, settings

def iflatten_hierarchy(root):
    return itertools.chain((root,),
            *(iflatten_hierarchy(n) for n in root.children))
def flatten_hierarchy(root):
    return list(iflatten_hierarchy(root))

def hierarchy_equivalence(root1, root2):
    if not root1 or not root2:
        return False
    # mostly the following suffices. one thing:
    #  - scrolls are ignored in node_equivalence
    for (n1, n2) in itertools.zip_longest(iflatten_hierarchy(root1),
            iflatten_hierarchy(root2)):
        if not nm.node_equivalence(n1, n2, check_parent=False):
            return False
    return True


def contains_progressbar(root):
    return (root.cls.endswith('ProgressBar') or
        any(contains_progressbar(child) for child in root.children))

def contains_clickables(root):
    return (root.clickable or
        any(contains_clickables(child) for child in root.children))


OperateResult = namedtuple('OperateResult', 'update parse node')


class EventNode(object):
    ''' an interned version of a node '''
    def __init__(self, node, count=0):
        self.node = node
        self.count = count # countVisited in old plg code

    def isequivalentto(self, node):
        return nm.node_equivalence(self.node, node)

    def mark_completely_visited(self):
        self.count = -1

    def is_completely_visited(self):
        return self.count < 0

    def __repr__(self):
        return 'EventNode({}, {})'.format(self.node, self.count)


class DevState(object):
    def __init__(self, device, androdev, metainfo):
        self.dev = device
        self.androdev = androdev
        self.metainfo = metainfo
        self.visited_win = set()
        self.known_win = {}
        self.stack = None
        self.prevstack = None
        self.focus = None
        self.root = None
        self.prevroot = None

    def is_win_visited(self, win):
        return win in self.visited_win

    def win_visited(self, win):
        self.visited_win.add(win)

    def load_hierarchy(self):
        self.prevroot = self.root
        for _ in range(settings.PROGRESSBAR_RETRIES):
            self.root = self.androdev.loadscene()
            if self.root and not contains_progressbar(self.root):
                break
            sleep(settings.PROGRESSBAR_SLEEP)
        else:
            if not self.root:
                raise Exception('None root for %s' % self.dev)

    def is_special_focus(self):
        ''' special windows include dialog boxes, popups, menus '''
        return len(self.stack[0]) > 1

    def load_windows(self):
        self.prevstack = self.stack
        self.stack = windows.get_stack(self.dev)
        focus, self.focus_frame = windows.focus(self.dev)
        # note stack may change but focus may not; not vice-versa
        self.focus_changed = not self.focus or self.focus.name != focus.name
        self.focus = focus

    def exit_win(self):
        self.androdev.press('back')
        self.androdev.wait_for_idle()
        self.load_windows()
        if not self.focus_changed:
            self.androdev.press('home')
            self.androdev.wait_for_idle()
            self.load_windows()

    def is_home_screen(self):
        return self.focus.name == settings.LAUNCHER_WIN

    #XIANG
    def is_browser(self):
        return self.focus.name == "com.example.mybrowser/com.example.mybrowser.MainActivity"

    def explore(self):
        #XIANG
        for launchable in self.metainfo['launchable']:
            #if self.metainfo['canstop']:
            #    return
            activity = '{}/{}'.format(self.metainfo['name'], launchable['name'])
            print("1 start explore "+activity)
            sys.stdout.flush()
            self.explore_activity(activity)

    def explore_activity(self, activity):
        #XIANG
        self.androdev.press('back')
        self.androdev.wait_for_idle()
        print("done waiting device!!!")
        sys.stdout.flush()

        base_en = EventNode(None)
        noloadwindows = False
        while not base_en.is_completely_visited():
            #canstop = self.metainfo['canstop']
            #if canstop:
            #    return
            res = OperateResult(True, True, base_en)
            print('starting', activity)
            sys.stdout.flush()
            au.startactivity(activity, self.dev)
            print('done starting', activity+" activity")
            sys.stdout.flush()
            sleep(settings.INITIAL_SLEEP)
            while True:
                #canstop = self.metainfo['canstop']
                #print("DEBUG: can stop? "+str(canstop))
                #if canstop:
                #    return
                print('exploring ',str(res.node) )
                sys.stdout.flush()
                if res.parse:
                    self.load_hierarchy()
                    # a naive way to compare hierarchies -- should mostly work
                    if (res.node and hierarchy_equivalence(self.prevroot,
                        self.root)):
                        # we just mark node as completely visited; later code
                        # will automatically not use this node
                        res.node.mark_completely_visited()
                        print("DEBUG: res.node ",res.node," has been explored")

                if res.update:
                    if not noloadwindows:
                        self.load_windows()
                    noloadwindows = False
                    if self.focus_changed:
                        if self.is_home_screen():
                            # getting to home screen repeatedly is not very
                            # useful
                            if res.node:
                                res.node.mark_completely_visited()
                            break
                        win = self.focus.name
                        print("DEBUG: current focus window: ",win)
                        if self.is_browser():
                            print("DEBUG: topmost window is browser, go back in 5s")
                            sleep(10)
                            self.exit_win()
                            noloadwindows = True # windows loaded in exit_win
                            res = OperateResult(True, True, None)
                            print("DEBUG: window should have been revoked")
                            continue
							
                        # mark node visited if just returning to something
                        # previously there on window stack
                        if res.node and self.prevstack:
                            prevwins = [win.name for win in
                                    flatten(self.prevstack)]
                            if win in prevwins:
                                res.node.mark_completely_visited()
                        if self.is_win_visited(win):
                            if res.node:
                                res.node.mark_completely_visited()
                            self.exit_win()
                            noloadwindows = True # windows loaded in exit_win
                            res = OperateResult(True, True, None)
                            continue
                        if win not in self.known_win:
                            self.known_win[win] = WinState(self.androdev)
                pointing_en = res.node
                try:
                    res = self.known_win[win].operate_hierarchy(self.root,
                            pointing_en, self.focus_frame,
                            not self.is_special_focus())
                except JsonRPCError:
                    # possibly the hierarchy changed after parsing
                    print("JsonRPCError: ")
                    continue
                except Exception as e:
                    print("Exception: "+str(e))
                    continue
                    
                if not res.parse and not res.update:
                    self.win_visited(win)
                    if pointing_en:
                        pointing_en.mark_completely_visited()
                    self.exit_win()
                    noloadwindows = True
                    res = OperateResult(True, True, None)
                    continue
                sleep(settings.OPERATE_SLEEP)


class WinState(object):
    def __init__(self, androdev, visitednodes=None):
        self.androdev = androdev
        self.visitednodes = visitednodes if visitednodes else []
        self.add_timenode = True

    def find(self, node):
        for index, visited in enumerate(self.visitednodes):
            if visited.isequivalentto(node):
                return index
        return -1

    def intern_node(self, node):
        found = self.find(node)
        if found < 0:
            en = EventNode(node)
            self.visitednodes.append(en)
            return en, False
        en = self.visitednodes[found]
        en.node = node
        # en = EventNode(node, old.followers, old.count)
        # self.visitednodes[found] = en
        return en, True

    def serialize_hierarchy(self, root):
        '''
            This part is about sequencing policies. However, some other
            things such as collapsing nodes, adding clickable properties,
            and so on also happen here. Newly discovered nodes will be operated
            upon before the old nodes -- this logic is implemented in
            WinState.operate_with_list() method.
        '''
        def visited_many_options(listnode):
            threshold = settings.VISITING_THRESHOLD
            if len(self.visitednodes) < threshold:
                return False
            count = 0
            for en in self.visitednodes:
                parent = getattr(en.node, 'parent', None)
                if parent and listnode.isequivalentto(parent):
                    count += 1
            return count > threshold

        # this function is equivalent to parse_hierarchy in old plg code
        def helper(node, oplist, editlist):
            if node.cls.endswith('WebView'):
                node.clickable = False
                # if no clickable was found inside, the node will be marked
                # clickable again
                node.img_proc(self.androdev)
            if node.checkable and not node.checked:
                editlist.appendleft(self.intern_node(node))
            elif node.cls.endswith('EditText'):
                editlist.appendleft(self.intern_node(node))
            elif node.clickable and not node.cls.endswith('ListView'):
                # list views are unnecessarily clickable
                oplist.appendleft(self.intern_node(node))
            elif node.scrollable:
                en, found = self.intern_node(node)
                # if all children are clickable -- typical of lists
                if all(child.clickable for child in node.children):
                    if not en.is_completely_visited():
                        if visited_many_options(en):
                            en.mark_completely_visited()
                            return
                oplist.append((en, found))
                suboplist = deque()
                for child in node.children:
                    helper(child, suboplist, editlist)
                oplist.extend(suboplist)
                return
            for child in node.children:
                helper(child, oplist, editlist)
        oplist = deque()
        editlist = deque()
        helper(root, oplist, editlist)
        webviews = []
        others = []
        for entry in oplist:
            n = entry[0].node
            if not n.cls or n.cls.endswith('WebView'):
                webviews.append(entry)
            else:
                others.append(entry)
        others.extend(webviews)
        others.extend(editlist)
        return others


    def operate_hierarchy(self, root, pointing_en, win_frame, addmenu):
        ''' pointing_en is most relevant when no window changes '''
        raw_seq = self.serialize_hierarchy(root)
        new_ens = []
        old_ens = []
        contains_pointing_en = False
        for en, found in raw_seq:
            if not en.is_completely_visited():
                if en == pointing_en:
                    contains_pointing_en = True
                elif found:
                    old_ens.append(en)
                else:
                    new_ens.append(en)
        if contains_pointing_en:
            old_ens.append(pointing_en)
        # newly appearing nodes will be executed first
        enseq = old_ens + new_ens
        if addmenu:
            menu = self.intern_node(KeyNode('menu'))[0]
            if not menu.is_completely_visited():
                enseq.append(menu)

        # add time node discretely. If it did not help do not add again
        if contains_clickables(root):
            self.add_timenode = True
        elif self.add_timenode:
            enseq.append(EventNode(TimeNode(settings.TIME_NODE_SLEEP)))
            self.add_timenode = False

        #print(enseq)
        while enseq:
            en = enseq.pop()
            res = self.operate(en, win_frame)
            if res.update or res.parse:
                return res
            en.mark_completely_visited()
        return OperateResult(False, False, None) # completely visited win

    def operate(self, en, win_frame):
        node = en.node
        print(node)
        if node == KeyNode('menu'):
            self.androdev.press('menu')
            return OperateResult(True, True, en)
        if type(node) is TimeNode:
            sleep(node.value)
            return OperateResult(True, True, en)
        if node.cls.endswith('EditText'):
            if node.text:
                return OperateResult(False, False, None)
            self.androdev.typestring('hello', node)
            return OperateResult(True, True, en)
        if node.checkable:
            self.androdev.tap(node)
            return OperateResult(False, False, None)
        if node.clickable and en.count < settings.VISITING_THRESHOLD2:
            en.count += 1
            self.androdev.tap(node)
            return OperateResult(True, True, en)
        if node.scrollable and en.count < settings.VISITING_THRESHOLD2:
            en.count += 1
            self.androdev.scroll(node)
            return OperateResult(False, True, en)
        # anything else: do nothing
        return OperateResult(False, False, None)


def explore(dev, appinfo):
    ''' The main entrypoint for AppsPlayground.

    Parameters
    ----------
    dev:
        can be a string like 'emulator-5554' or an `AndroidDevice` instance
    appinfo:
        the metadata for the app, such as one derived from
        plg.metadata.getmetadata()
    '''
    if type(dev) is AndroidDevice:
        androdev = dev
        dev = dev.name
    else:
        dev = str(dev)
        androdev = AndroidDevice(dev)
    if au.isdevicerunning(dev):
        print("in explore: device %s is running" % dev)
    else:
        print("in explore: device %s is NOT running" % dev)
    
    DevState(dev, androdev, appinfo).explore()
