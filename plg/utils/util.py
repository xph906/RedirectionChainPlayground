''' general utils '''

from collections import namedtuple
import itertools
import socket

Frame = namedtuple('Frame', 'x0 y0 x1 y1')
Point = namedtuple('Point', 'x y')

def width(frame):
    return frame.x1 - frame.x0

def height(frame):
    return frame.y1 - frame.y0

def flatten(iterator):
    ''' flattens an iterator/iterable of iterators/iterables to give back an
    iterator
    '''
    return itertools.chain(*iterator)


def freeport():
    '''
    get a free port from the OS.
    Warning: the returned port may get used before this process binds to it
    See: http://stackoverflow.com/q/8599984/567555, and
    https://gist.github.com/3979133
    '''
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

