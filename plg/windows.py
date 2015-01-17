''' Get windows and related properties '''

from collections import namedtuple

from plg.utils.androidutil import dumpsys
from plg.utils.util import Frame

Window = namedtuple('Window', 'hashid name')

def _parse_win(win):
    first_space = win.find(' ')
    second_space = win.find(' ', first_space + 1)
    third_delim = win.find(' ', second_space + 1)
    if third_delim < 0:
        third_delim = win.find('}', second_space + 1)
    # len('Window{') == 7
    return Window(win[7:first_space], win[second_space+1 : third_delim])

def _parse_win_list(winlist):
    beg = winlist.find('[') # should be 0
    end = winlist.find(']')
    # using reversed list below to find top windows first
    return [_parse_win(win.strip()) for win in
            reversed(winlist[beg:end].split(','))]

def get_stack(device=None):
    ''' Return the windows in z order, topmost first '''
    output = dumpsys(['window', 't'], device)
    start = output.find('Application tokens in Z order:')
    output = output[start:]
    key = 'allAppWindows='
    stk = []
    for line in output.splitlines():
        line = line.lstrip()
        if line.startswith(key):
            stk.append(_parse_win_list(line[len(key):])) # len('windows=[') == 9
    return stk

def focused_win(device=None):
    ''' the currently focused window '''
    output = dumpsys(['window', 'w'], device)
    key = 'mCurrentFocus='
    winstart = output.find(key) + len(key)
    return _parse_win(output[winstart:])

# expecting lstripped lines
def _window_id(line):
    if line.startswith('Window #'):
        return _parse_win(line[line.find('Window{', len('Window #')):])
    return None

# expecting lstripped lines
def _window_frame(line):
    key = 'mFrame='
    if not line.startswith(key):
        return None
    num1s = len(key) + 1
    num1e = line.find(',', num1s)
    num2s = num1e + 1
    num2e = line.find(']', num2s)
    num3s = num2e + 2
    num3e = line.find(',', num3s)
    num4s = num3e + 1
    num4e = line.find(']', num4s)
    return Frame(int(line[num1s:num1e]), int(line[num2s:num2e]),
            int(line[num3s:num3e]), int(line[num4s:num4e]))

def focused_frame(hashid, device=None):
    ''' the frame of currently focused window '''
    output = dumpsys(['window', 'w'], device)
    findmode = False
    for line in output.splitlines():
        line = line.lstrip()
        if findmode:
            frame = _window_frame(line)
            if frame is not None:
                return frame
        else:
            win = _window_id(line)
            if win is not None and win.hashid == hashid:
                findmode = True
    return None # should never happen

def focus(device=None):
    output = dumpsys(['window', 'w'], device)
    curwin = None
    frames = {}
    for line in output.splitlines():
        line = line.lstrip()
        win = _window_id(line)
        if win is not None:
            curwin = win.hashid
        else:
            frame = _window_frame(line)
            if frame is not None:
                frames[curwin] = frame
            elif line.startswith('mCurrentFocus='):
                winstart = len('mCurrentFocus=')
                focus_win = _parse_win(line[winstart:])
                return focus_win, frames[focus_win.hashid]

def is_special(win):
    return ':' in win.name # e.g., PopupWindow:41946bb0
