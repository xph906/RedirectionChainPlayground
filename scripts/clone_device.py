#!/usr/bin/python3

import os, shutil, subprocess, argparse

def shell(command):
    subprocess.check_call(command, shell=True)

def clone(src, dest):
    '''src, dest are names of AVDs. This procedure assumes current working directory contains the AVD.ini files and AVD.avd directories.'''
    ignore=shutil.ignore_patterns('*.lock', 'emulator-user.ini')
    shutil.copy('%s.ini' % src, '%s.ini' % dest)
    shutil.copytree('%s.avd' % src, '%s.avd' % dest, ignore=ignore)
    shell('sed -i "s/%s/%s/g" %s.ini' % (src, dest, dest))
    os.chdir('%s.avd' % dest)
    shell('sed -i "s/%s/%s/g" snapshots.img.default-boot.ini' % (src, dest))
    shell('sed -i "s/%s/%s/g" hardware-qemu.ini' % (src, dest))
    os.chdir('..')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', help='Directory containing AVDs, normally ~/.android/avd/', default='~/.android/avd/')
    parser.add_argument('ORIGIN', help='Name of the AVD to be copied')
    parser.add_argument('PREFIX', help='AVDs created will be named with PREFIX01, PREFIX02, etc.')
    parser.add_argument('NUMBER', help='Number of AVD copies', type=int)
    parser.add_argument('-r', '--dry-run', help='List actions instead of actually perform', action='store_true')
    args = parser.parse_args()
    args.dir = os.path.expanduser(args.dir)

    cwd = os.getcwd()
    os.chdir(args.dir)
    src = args.ORIGIN
    for i in range(1, 1 + args.NUMBER):
        dest = '%s%02d' % (args.PREFIX, i)
        print('Cloning: %s -> %s ...' % (src, dest))
        if not args.dry_run:
            clone(src, dest)
    os.chdir(cwd)
