#!/usr/bin/env python

''' Create Android devices to run AppsPlayground.
Requires sdk tools, specifically `android` to be in path.
TODO: add ini support for custom devices
'''

import sys
import pexpect

def main():
    p = pexpect.spawn('android create avd -n {} -t android-17 --snapshot'
            ' --sdcard 200M --abi x86'.format(sys.argv[1]), timeout=2)
    p.logfile = sys.stdout.buffer

    p.expect(b'custom hardware profile')
    p.sendline('yes')
    p.expect(b'avd.name')
    p.sendline('')
    p.expect(b'disk.cachePartition')
    p.sendline('')
    p.expect(b'disk.cachePartition.path')
    p.sendline('')
    p.expect(b'disk.cachePartition.size')
    p.sendline('')
    p.expect(b'disk.dataPartition.initPath')
    p.sendline('')
    p.expect(b'disk.dataPartition.path')
    p.sendline('')
    p.expect(b'disk.dataPartition.size')
    p.sendline('')
    p.expect(b'disk.ramdisk.path')
    p.sendline('')
    p.expect(b'disk.snapStorage.path')
    p.sendline('')
    p.expect(b'disk.systemPartition.initPath')
    p.sendline('')
    p.expect(b'disk.systemPartition.path')
    p.sendline('')
    p.expect(b'disk.systemPartition.size')
    p.sendline('')
    p.expect(b'hw.accelerometer')
    p.sendline('')
    p.expect(b'hw.audioInput')
    p.sendline('')
    p.expect(b'hw.audioOutput')
    p.sendline('')
    p.expect(b'hw.battery')
    p.sendline('')
    p.expect(b'hw.camera.back')
    p.sendline('')
    p.expect(b'hw.camera.front')
    p.sendline('')
    p.expect(b'hw.cpu.arch')
    p.sendline('') # actually cmd parameters will be used
    p.expect(b'hw.cpu.model')
    p.sendline('')
    p.expect(b'hw.dPad')
    p.sendline('')
    p.expect(b'hw.gps')
    p.sendline('')
    p.expect(b'hw.gpu.enabled')
    p.sendline('')
    p.expect(b'hw.gsmModem')
    p.sendline('')
    p.expect(b'hw.keyboard')
    p.sendline('yes')
    p.expect(b'hw.keyboard.charmap')
    p.sendline('')
    p.expect(b'hw.keyboard.lid')
    p.sendline('')
    p.expect(b'hw.lcd.backlight')
    p.sendline('')
    p.expect(b'hw.lcd.density')
    p.sendline('')
    p.expect(b'hw.lcd.depth')
    p.sendline('')
    p.expect(b'hw.lcd.height')
    p.sendline('')
    p.expect(b'hw.lcd.width')
    p.sendline('')
    p.expect(b'hw.mainKeys')
    p.sendline('')
    p.expect(b'hw.ramSize')
    p.sendline('')
    p.expect(b'hw.screen')
    p.sendline('')
    p.expect(b'hw.sdCard')
    p.sendline('')
    p.expect(b'hw.sdCard.path')
    p.sendline('')
    p.expect(b'hw.sensors.magnetic_field')
    p.sendline('')
    p.expect(b'hw.sensors.orientation')
    p.sendline('')
    p.expect(b'hw.sensors.proximity')
    p.sendline('')
    p.expect(b'hw.sensors.temperature')
    p.sendline('')
    p.expect(b'hw.trackBall')
    p.sendline('')
    p.expect(b'hw.useext4')
    p.sendline('')
    
    while not p.expect([b'kernel', b'vm.heapSize']):
        p.sendline('')
    p.sendline('')
    p.expect(pexpect.EOF)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('usage: python {} avdname'.format(sys.argv[0]))
    main()
