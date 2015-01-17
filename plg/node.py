from collections import namedtuple

from plg.utils.util import Frame
from plg.vision3 import get_rects

TimeNode = namedtuple('TimeNode', 'value')
KeyNode = namedtuple('KeyNode', 'value')

class ImgNode(namedtuple('ImgNode', 'parent frame')):
    cls = ''
    children = ()
    checkable = False
    clickable = True
    scrollable = False
    text = ''
    desc = ''

class Node(object):
    def __init__(self, parent, props):
        self.children = []
        self.parent = parent
        self.naf = props.get('@NAF') == 'true'
        self.index = int(props['@index'])
        self.text = props['@text']
        self.cls = props['@class']
        self.pkg = props['@package']
        self.desc = props['@content-desc']
        self.checkable = props['@checkable'] == 'true'
        self.checked = props['@checked'] == 'true'
        self.clickable = props['@clickable'] == 'true'
        self.enabled = props['@enabled'] == 'true'
        self.focusable = props['@focusable'] == 'true'
        self.focused = props['@focused'] == 'true'
        self.scrollable = props['@scrollable'] == 'true'
        self.lngclickable = props['@long-clickable'] == 'true'
        self.password = props['@password'] == 'true'
        self.selected = props['@selected'] == 'true'
        bounds = props['@bounds']
        num1s = 1
        num1e = bounds.find(',', num1s)
        num2s = num1e + 1
        num2e = bounds.find(']', num2s)
        num3s = num2e + 2
        num3e = bounds.find(',', num3s)
        num4s = num3e + 1
        num4e = bounds.find(']', num4s)
        self.frame = Frame(int(bounds[num1s:num1e]), int(bounds[num2s:num2e]),
                int(bounds[num3s:num3e]), int(bounds[num4s:num4e]))

        children = props.get('node', [])
        if not isinstance(children, list):
            children = [children] # a single node is not encapsulated in list
        for child in children:
            self.children.append(Node(self, child))

    def img_proc(self, dev=None):
        ''' currently, this heuristically identifies buttons etc. so that they
        can be clicked.
        '''
        if dev and type(dev) is not str:
            dev = dev.name # we suppose it is AndroidDevice
        rects = get_rects(self.frame, device=dev)
        print(self.frame, rects)
        for rect in rects:
            self.children.append(ImgNode(self, Frame(*rect)))
        if not rects:
            self.clickable = True


    def __repr__(self):
        return 'Node({!r}, {!r}, {!r})'.format(self.cls, self.text, self.desc)

    def debug_print(self):
        print(self.__dict__)

    def indices(self):
        ind = []
        node = self
        while node is not None:
            ind.append(node.index)
            node = node.parent
        return reversed(ind)

    def children_text(self):
        strs = [self.text, self.desc] + [c.children_text() for c in
                self.children if type(c) is Node]
        return ' '.join(s for s in strs if s)

    def description(self):
        if self.text:
            if self.desc:
                return '{} {}'.format(self.text, self.desc)
            else:
                return self.text
        elif self.desc:
            return self.desc
        node = self
        while node is not None:
            txt = node.children_text()
            if txt:
                return txt
            node = node.parent
        return ''




def node_equivalence(this, that, check_parent=True, check_text=True):
    if this is that or this == that:
        return True
    if (type(this) is KeyNode or # tuple types:  this == that sufficed
            type(this) is TimeNode or
            type(this) != type(that)): # also captures one of these being None
        return False
    if type(this) is ImgNode:
        return this.frame == that.frame and node_equivalence(this.parent,
                that.parent)
    # must have Node type below
    if this.cls != that.cls or this.pkg != that.pkg:
        return False
    if (not this.scrollable and check_text and this.description() !=
        that.description()):
        # for scrollables text will change so should not check for text
        # often whole screen has at most one scrollable so we are fine
        return False
    if this.parent is None:
        return that.parent is None
    if check_parent:
        # we already checked relevant text, no need to check things now
        return node_equivalence(this.parent, that.parent, check_text=False)
    return True
