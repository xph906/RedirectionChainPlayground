import os, subprocess, imp

def check_executable(executable):
    try:
        subprocess.check_call(['which', executable], stdout=subprocess.DEVNULL)
        print('Checking executable %s ... yes' % executable)
        return 1
    except:
        print('Checking executable %s ... no' % executable)
        return 0

def check_environment(key):
    if key in os.environ:
        print('Checking environment %s ... yes' % key)
        return 1
    else:
        print('Checking environment %s ... no' % key)
        return 0
        
def check_module(module):
    try:
        imp.find_module(module)
        print('Checking python module %s ... yes' % module)
        return 1
    except ImportError:
        print('Checking python module %s ... no' % module)
        return 0

if __name__ == '__main__':
    passed = 0
    tested = 0
    passed += check_executable('aapt')
    tested += 1
    passed += check_executable('emulator64-x86')
    tested += 1
    passed += check_environment('LD_LIBRARY_PATH')
    tested += 1
    passed += check_module('pexpect')
    tested += 1
    print('-' * 80)
    print('%(passed)d / %(tested)d passed' % locals())
