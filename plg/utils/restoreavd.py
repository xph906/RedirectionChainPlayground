#!/usr/bin/python3

import os, shutil, subprocess, argparse,sys

def shell(command):
    subprocess.check_call(command, shell=True)

def restore(src, dest):
    '''src, dest are names of AVDs. This procedure assumes current working directory contains the AVD.ini files and AVD.avd directories.'''
    ignore=shutil.ignore_patterns('*.lock', 'emulator-user.ini')
    shutil.copy('%s.ini' % src, '%s.ini' % dest)
    shutil.copytree('%s.avd' % src, '%s.avd' % dest, ignore=ignore)
    shell('sed -i "s/%s/%s/g" %s.ini' % (src, dest, dest))
    os.chdir('%s.avd' % dest)
    shell('sed -i "s/%s/%s/g" snapshots.img.default-boot.ini' % (src, dest))
    shell('sed -i "s/%s/%s/g" hardware-qemu.ini' % (src, dest))
    os.chdir('..')

def restoreAVD(src, dest, root_dir='/home/xpan/.android/avd/' ):
    print("rootdir:%s srcavd:%s dstavd:%s" % (root_dir,src,dest))
    if src == dest:
        print("error: src and dest equal!")
        return False
    sys.stdout.flush()
    cwd = os.getcwd()
    os.chdir(root_dir)
    cwd_debug = os.getcwd()
    #src_dir = os.path.join(root_dir,src)
    src_dir = '%s.avd'%src
    src_ini = '%s.ini'%src
    if (not os.path.isdir(src_dir)) or (not os.path.isfile(src_ini)):
        print("error, src %s doesn't exist. currentdir: %s" % (src,cwd_debug))
        return False
    dest_dir = '%s.avd'%dest
    if os.path.isdir(dest_dir):
        print("%s exists, delete it"%dest_dir)
        shutil.rmtree(dest_dir)

    print('Restoring: %s -> %s ...' % (src, dest))
    sys.stdout.flush()
    restore(src, dest)
    os.chdir(cwd)
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', help='Directory containing AVDs, normally ~/.android/avd/', default='~/.android/avd/')
    parser.add_argument('-src', help='Name of the AVD to be copied')
    parser.add_argument('-dst', help='AVDs created will be named with PREFIX01, PREFIX02, etc.')
    parser.add_argument('-r', '--dry-run', help='List actions instead of actually perform', action='store_true')
    args = parser.parse_args()
    args.dir = os.path.expanduser(args.dir)

    restoreAVD(args.src, args.dst,args.dir )
