#!/usr/bin/python3
import subprocess, tempfile, os

PWD = os.path.dirname(os.path.realpath(__file__))
VISION2_PATH = os.path.join(PWD, 'vision2.py')

def take_snapshot(image_path, device=None):
    if device:
        subprocess.check_call('adb -s %(device)s shell screencap -p | sed \'s/\r$//\' > %(image_path)s' % locals(), shell=True)
    else:        
        subprocess.check_call('adb shell screencap -p | sed \'s/\r$//\' > %(image_path)s' % locals(), shell=True)

def get_rects(frame, device=None, directory=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = os.path.join(tmpdir, 'snapshot.png')
        take_snapshot(image_path, device)
        if directory:
            command = [VISION2_PATH, image_path, '-d', directory]
        else:
            command = [VISION2_PATH, image_path]
        command.extend(str(x) for x in frame)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
        mk = lambda line: [int(i) for i in line.split()]
        rects = [mk(line) for line in iter(process.stdout.readline, '')]
        mk = lambda rect: [rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]]
        return [mk(rect) for rect in rects]
