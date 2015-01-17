* daemon not running. starting it now on port 5037 *
* daemon started successfully *
(re)starting adb server
killing any emulators already present
Exception in thread avd-01:
Traceback (most recent call last):
  File "/usr/lib/python3.4/threading.py", line 920, in _bootstrap_inner
    self.run()
  File "driver6-test.py", line 94, in run
    if isdevicerunning(self.device()):
TypeError: 'str' object is not callable

apps	12
avds	avd-01
out	/home/xpan/playground/out3
--------------------------------------------------------------------------------
emulator64-x86 @avd-01 -port 5554 -scale .5 -memory 512 -no-snapshot-save -qemu -enable-kvm
Traceback (most recent call last):
  File "driver6-test.py", line 314, in <module>
  File "driver6-test.py", line 304, in main
    player.signal(sha1, path)
  File "/usr/lib/python3.4/queue.py", line 167, in get
    self.not_empty.wait()
  File "/usr/lib/python3.4/threading.py", line 289, in wait
    waiter.acquire()
KeyboardInterrupt
