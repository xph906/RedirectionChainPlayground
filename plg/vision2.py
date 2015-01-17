#!/usr/bin/python
import datetime
import argparse
import os
import cv2
import shutil


def contains(rect1, rect2):
    x0, y0, w0, h0 = rect1
    x1, y1, w1, h1 = rect2
    return ( x0 <= x1 and y0 <=y1 and (x0 + w0) >= (x1 + w1) and (y0 + h0) >= (y1 + h1) )

    
def fix_edges(edges):
    height, width = edges.shape
    cv2.rectangle(edges, (1, 1), (width - 2, height - 1), (255, 255, 255), thickness=1)

def is_inside(rect1, rect2):
    x11, y11, w1, h1 = rect1
    x12 = x11 + w1
    y12 = y11 + h1
    x21, y21, w2, h2 = rect2
    x22 = x21 + w2
    y22 = y21 + h2
    return x11 >= x21 and y11 >= y21 and x12 <= x22 and y12 <= y22

def remove_duplicate(rects):
    size = len(rects)
    root = [i for i in range(size)]
    deep = [0] * size
    for i in range(size):
        for j in range(i + 1, size):
            index1 = i
            index2 = j
            while root[index1] != index1:
                index1 = root[index1]
            while root[index2] != index2:
                index2 = root[index2]
            if index1 is index2:
                continue
            if is_inside(rects[index1], rects[index2]):
                root[index2] = index1
                deep[index1] = max(deep[index1], deep[index2] + 1)
            elif is_inside(rects[index2], rects[index1]):
                root[index1] = index2
                deep[index2] = max(deep[index2], deep[index1] + 1)
    return [rects[i] for i in range(size) if root[i] == i]

def get_rects(image_path, frame=None):
    rects = list()
    image = cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
    if image is None:
        return []
    edges = cv2.Canny(image, 50, 100)
    if edges is None:
        return []
    fix_edges(edges)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1400:
            x, y, w, h = cv2.boundingRect(contour)
            rects.append((x, y, w, h))
    rects = remove_duplicate(rects)
    if frame is None:
        return rects
    else:
        x0, y0, x1, y1 = frame
        return [rect for rect in rects if contains((x0, y0, x1 - x0, y1 - y0), rect)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image', help='path to the image')
    parser.add_argument('-d', '--debug', help='enable debug mode, specify output dir')
    parser.add_argument('x0', type=int, help='x0')
    parser.add_argument('y0', type=int, help='y0')
    parser.add_argument('x1', type=int, help='x1')
    parser.add_argument('y1', type=int, help='y1')
    args = parser.parse_args()
    frame = (args.x0, args.y0, args.x1, args.y1)
    rects = get_rects(args.image, frame)
    if args.debug:
        image = cv2.imread(args.image, cv2.CV_LOAD_IMAGE_COLOR)
        write_path = os.path.join(args.debug, datetime.datetime.now().strftime('%Y-%m-%d+%H:%M:%S.%f.png'))
        cv2.imwrite(write_path, image)
        for x, y, w, h in rects:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), thickness=2)
        write_path = os.path.join(args.debug, datetime.datetime.now().strftime('%Y-%m-%d+%H:%M:%S.%f.png'))
        cv2.imwrite(write_path, image)
    for x, y, w, h in rects:
        print('%(x)d\t%(y)d\t%(w)d\t%(h)d' % locals())
