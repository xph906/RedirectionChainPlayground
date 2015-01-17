#!/usr/bin/env python3
import os
from multiprocessing import Process, Queue
import time
import logging
#from driver1 import main

FMT = '%(asctime)s\t%(message)s'
DATEFMT = '%x %X'

def child_proc(queue, i):
    while True:
        if not queue.empty():
            print(queue.get(), os.getpid())
#            time.sleep(0.3)
#            main('plgavd%s' % i, queue.get())
        else:
            os._exit(0)

def checkApkStatus(apk_dic,file_explored_excep,file_explored_noexcep,file_not_explored,file_explored_elsewhere):
    file_explored_excep.seek(0,0)
    for line in file_explored_excep:
        line = line.split('\t')[0]
        apk_dic[line.strip()]=1
    file_explored_noexcep.seek(0,0)
    for line in file_explored_noexcep:
        line = line.split('\t')[0]
        apk_dic[line.strip()]=1
    file_not_explored.seek(0,0)
    for line in file_not_explored:
        line = line.split('\t')[0]
        apk_dic[line.strip()]=0
    file_explored_elsewhere.seek(0,0)
    for line in file_explored_elsewhere:
        line = line.split('\t')[0]
        apk_dic[line.strip()]=1

def getApkDic(directory):
    # value == 1: this apk has been explored
    # value == 0: this apk has not been explored
    apk_dic={}
    mk = lambda root, name: os.path.abspath(os.path.join(root, name))
    for root, dirs, names in os.walk(directory):
        for name in names:
            if name.lower().endswith(".apk"):
                apk_dic[mk(root, name)]=0
    return apk_dic

def parent_proc():
    queue = Queue()
    proc_list = []
    apk_dic=getApkDic('/nfs/data/sample')

    file_explored_excep = open("./apk_explored_exception.txt", "a+")
    file_explored_noexcep = open("./apk_explored_noexcep.txt", "a+")
#    file_not_explored = open("./apk_not_explored.txt", "a+")
#    file_explored_elsewhere = open("./apk_explored_elsewhere.txt", "a+")
    checkApkStatus(apk_dic,file_explored_excep,file_explored_noexcep,file_not_explored,file_explored_elsewhere)

    for apk_path in apk_dic:
        if apk_dic[apk_path] == 1:
            continue
        else:
            queue.put(apk_path)
    for i in range(10):
        process = Process(target=child_proc, args=(queue, i,))
        process.start()
        proc_list.append(process)
    for process in proc_list:
        process.join()

    file_explored_excep.close()
    file_explored_noexcep.close()
    file_not_explored.close()
    file_explored_elsewhere.close()

if __name__ == '__main__':
    parent_proc()

