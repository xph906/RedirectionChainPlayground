#!/usr/bin/python3

import threading, argparse, subprocess, logging, queue, os, time,sys
import plg, plg.metadata, plg.explore, plg.utils.androidutil, plg.utils.logcat, plg.settings
import extra.cellid, extra.notdet
from plg.androdevice import run_monkey
from plg.utils.androidutil import getapkname
from plg.utils.androidutil import onlinedevices
from plg.utils.androidutil import isdevicerunning
from plg.utils.androidutil import killmonkey
from plg.utils.androidutil import checkmonkey
from plg.utils.restoreavd import restoreAVD

class Apps:

    def __init__(self, inventory):
        self.__inventory = inventory

    def list(self):
        for line in open(self.__inventory):
            yield line.strip().split('\t')

    def size(self):
        paths = [line.strip().split('\t')[1] for line in open(self.__inventory)]
        for path in paths:
            if not os.path.isfile(path):
                raise ValueError('App not available: %s' % path)
        return len(paths)


class PlayerException(Exception):
    pass


class Player(threading.Thread):
    def __init__(self, name, port, avd_queue, out_root,timeout,snapshot,avddir):
        threading.Thread.__init__(self)
        self.__name = name
        self.__port = port
        self.__avd_queue = avd_queue
        self.__app_queue = queue.Queue()
        self.__app_sha1 = None
        self.__app_path = None
        self.__out_root = out_root
        self.__intents = None
        #XIANG
        #indicate whether to restart emulator
        self.__launch_emu = True
        #explore timeout
        self.__timeout = timeout
        #original avd name
        self.__snapshot = snapshot
        #default ~/.android/avd
        self.__avd_dir = avddir

    def signal(self, app_sha1, app_path):
        self.__app_queue.put((app_sha1, app_path))

    @property
    def name(self):
        return self.__name

    @property
    def port(self):
        return self.__port

    @property
    def device(self):
        return 'emulator-%d' % self.__port

    @property
    def directory(self):
        return os.path.join(self.__out_root, self.__app_sha1[0:2], self.__app_sha1)

    def __terminate(self):
        #XIANG
        #explore will check 'canstop' before exploring each window
        logging.info("Timeout, stop exploring app")
        if not self.meta:
            self.meta = {}
        self.meta['canstop'] = True
        
        '''
        logging.info('Killing avd due to timeout: %s' % self.device)
        print('Killing avd due to timeout: %s' % self.device)
        try:
            subprocess.check_call(['adb', '-s', self.device, 'emu', 'kill'])
        except:
            logging.info('Command \'adb emu kill\' failed: %s' % self.device)
        '''

    #XIANG used for block prevention
    def __deadlock_break(self, timeout=800):
       while True:
            cur_time = int(time.time()) 
            #logging.info("deadlock break: app:%s curtime:%d starttime:%d" % (self.__app_sha1,cur_time,self.__app_start_time))
            if cur_time > self.__app_start_time + timeout:
                logging.info("DEADLOCK!! restart emulator")
                self.__launch_emu = True
                try:
                    self.__app_start_time = cur_time
                    if self.meta:
                        self.meta['canstop'] = True
                    self.__launch()
                except:
                    print('failed to re-launch device %s' % self.device)
            time.sleep(30)

    
    #XIANG
    def run(self):
        self.count = 0
        deadlock_thread = None
        logging.info("start player ") 
        while True:
            if self.__wait() == False:
                logging.info("Wait fail ...")
                continue
            try:
                self.__app_start_time = int(time.time())
                if deadlock_thread==None or not deadlock_thread.is_alive():
                    logging.info("Deadlock thread not started, starting it ...")
                    deadlock_thread = threading.Thread(target=self.__deadlock_break)
                    deadlock_thread.daemon = True
                    deadlock_thread.start()
                if self.__launch_emu == True:
                    logging.info("Start launch device")
                    self.__launch()
                    self.__launch_emu = False
                logging.info("Start install")
                self.__install(self.__timeout)
                logging.info("Start explore")
                self.__explore(self.__timeout)
                logging.info("Start uninstall the app")
                self.__run_uninstall() 
                self.count += 1
                if self.count % 10 == 0:
                    self.__launch_emu = True
                    logging.info("Restart emulator next time")
                logging.info("This player has explored "+str(self.count)+" apps")

                #if isdevicerunning(self.device):
                #    logging.info("device %s is running" %self.device)
                #else:
                #    logging.info("device %s is NOT running" %self.device)

            except PlayerException as e:
                logging.info('Giving up app %s' % self.__app_sha1)
                self.__run_uninstall() 
                self.__launch_emu = True
                time.sleep(5)
            except Exception as e:
                logging.info('Exception %s. Giving up app %s' % (str(e), self.__app_sha1))
                self.__run_uninstall() 
                self.__launch_emu = True
                
            self.__lightclean()

    def __wait(self):
        self.__avd_queue.put(self)
        sha1, path = self.__app_queue.get()
        self.__app_sha1 = sha1
        self.__app_path = path
        self.meta = None
        #XIANG
        self.__intents = list()
        os.makedirs(self.directory, exist_ok=True)
        devices = onlinedevices()
        for device in devices:
            logging.debug("    this is online device: "+device)
        #get name of the apk for uninstall use
        self.__app_name = getapkname(path)
        if self.__app_name == None:
            logging.error("can't extract info from app ",path)
            return False

        return True

    #XIANG only clean the state of app info
    def __lightclean(self):
        self.__app_sha1 = None
        self.__app_path = None
        self.__intents = None
        self.__logcat_proc=None
        self.__app_queue.task_done()

    def __clean(self):
        logging.info('Killing device %s' % self.device)
        plg.utils.androidutil.killemulator(self.device)
        stream = open(os.path.join(self.directory, 'intents.txt'), 'w')
        for intent, package in self.__intents:
            stream.write('intent=%s\tpackage=%s\n' % (intent, package))
        stream.close()
        self.__app_sha1 = None
        self.__app_path = None
        self.__intents = None
        self.__app_queue.task_done()
    
    def __prelaunch(self):
        try:
            plg.utils.androidutil.killemulator(self.device)
            args = ['emulator64-x86']
            args[1:1] = ['-no-snapshot-load', '-qemu', '-enable-kvm']
            args[1:1] = ['-memory', '512']
            args[1:1] = ['-scale', '.5']
            args[1:1] = ['-port', '%d' % self.__port]
            args[1:1] = ['@%s' % self.__name]
            logging.info('Prelaunching device %s with no-snapshot-load option' % self.device)
            subprocess.Popen(args, stdout=open(os.path.join(self.directory, 'stdout.txt'), 'w'), stderr=open(os.path.join(self.directory, 'stderr.txt'), 'w'))
            plg.utils.androidutil.waitfordevice(self.device, timeout=60)
            time.sleep(10)
            logging.info('Done prelaunching device %s with no-snapshot-load option' % self.device)
        except subprocess.TimeoutExpired:
            logging.warning('Failed prelaunching device: %s with no-snapshot-load option' % self.device)
            #raise PlayerException()


    def __launch(self):
        #XIANG
        try:
            logging.info('    begin killing emulator %s' % self.device)
            plg.utils.androidutil.killemulator(self.device)
            time.sleep(2)
            # restore avd
            logging.info('    done killing emulator %s' % self.device)
            if not restoreAVD(self.__snapshot,self.__name,self.__avd_dir):
                logging.error("    failed to restore from %s to %s" %(self.__snapshot,self.__name))
                raise PlayerException()
            logging.info('    done restoring avd from %s' % self.__snapshot)
            args = ['emulator64-x86']
            args[1:1] = ['-no-snapshot', '-qemu', '-enable-kvm']
            args[1:1] = ['-memory', '512']
            args[1:1] = ['-scale', '.5']
            args[1:1] = ['-port', '%d' % self.__port]
            args[1:1] = ['@%s' % self.__name]
            logging.info('    begin launching device %s' % self.device)
            subprocess.Popen(args, stdout=open(os.path.join(self.directory, 'stdout.txt'), 'w'), stderr=open(os.path.join(self.directory, 'stderr.txt'), 'w'))
            time.sleep(5)
            plg.utils.androidutil.waitfordevice(self.device, timeout=120)
            logging.info('    done launching device %s' % self.device)
        except subprocess.TimeoutExpired:
            logging.warning('    failed launching device: %s' % self.device)
            raise PlayerException()

    def __install(self,timeout):
        #XIANG
        try:
            logging.info("    begin installing "+self.__app_path)
            sys.stdout.flush()
            command = plg.utils.androidutil.getadbcmd(['install', self.__app_path], self.device)
            subprocess.check_call(command, timeout=30)
            #subprocess.check_call(command, stderr=subprocess.STDOUT,timeout=30)
            plg.utils.logcat.clearlogcat(self.device)
            self.__logcat_proc = plg.utils.logcat.logcat(os.path.join(self.directory, 'logcat.txt'), self.device,timeout)
            logging.info("        logcat pid "+str(self.__logcat_proc.pid))
            sys.stdout.flush()
            extra.cellid.replace(self.device)
            logging.info("    done installing "+self.__app_path)
            sys.stdout.flush()
        except subprocess.CalledProcessError as e:
            logging.warning('    failed installing app %s' % self.__app_sha1)
            raise PlayerException()
        except Exception as e:
            logging.warning('    failed unintalling app %s[%s] %s'%(self.__app_name,self.__app_sha1, str(e)))
            raise PlayerException()

    def __uninstall(self):
        try:
            if not isdevicerunning(self.device):
                logging.info("    device is offline, quit uninstall") 
                return
            command = plg.utils.androidutil.getadbcmd(['uninstall', self.__app_name], self.device)
            logging.info("    begin uninstall "+self.__app_path)
            sys.stdout.flush()
            #subprocess.check_call(command, stderr=subprocess.STDOUT, timeout=30)
            self.__uninstall_process = subprocess.Popen(command)
            logging.info("    done uninstall "+self.__app_path)
            sys.stdout.flush()
            if self.__logcat_proc != None:
                logging.info("    terminate logcat process: "+str(self.__logcat_proc.pid)+" ")
                self.__logcat_proc.terminate()
        except subprocess.CalledProcessError as e:
            logging.warning('    failed unintalling app %s[%s]'%(self.__app_name,self.__app_sha1))
            raise PlayerException()
        except Exception as e:
            logging.warning('    failed unintalling app %s[%s] %s'%(self.__app_name,self.__app_sha1, str(e)))
            raise PlayerException()
    
    #for some reason, uninstall an app might get stuck after running for 20+ hours
    #do it in a new process
    def __run_uninstall(self):
        try:
            self.__uninstall_process = None
            uninstall_thread = threading.Thread(target=self.__uninstall)    
            uninstall_thread.start()

            uninstall_thread.join(30)
            if uninstall_thread.is_alive():
                logging.warning('    uninstall process failed to terminate, force to terminate')
                sys.stdout.flush()
                if self.__uninstall_process != None:
                    self.__uninstall_process.terminate() 
                    uninstall_thread.join(10)
                    raise PlayerException()
        except Exception as e:
            logging.warning('    failed unintalling app %s[%s] %s in_run_uninstall'%(self.__app_name,self.__app_sha1, str(e)))
            raise PlayerException()
            
    def __run_explore(self):
        try:
            self.__explore_process = None
            explore_thread = threading.Thread(target=self.__explore)    
            explore_thread.start()

            explore_thread.join(30)
            if explore_thread.is_alive():
                logging.warning('    explore process failed to terminate, force it to terminate')
                sys.stdout.flush()
                if self.__explore_process != None:
                    self.__explore_process.terminate() 
                    explore_thread.join(10)
                    raise PlayerException()
        except Exception as e:
            logging.warning('    failed to terminate exploring app %s[%s] %s in run_explore'%(self.__app_name,self.__app_sha1, str(e)))
            raise PlayerException()

    #XIANG
    def __explore(self,interval=300):
        try:
            timer = threading.Timer(interval, self.__terminate)
            timer.start()
            metainfo = plg.metadata.getmetadata(self.__app_path)
            metainfo['canstop'] = False
            self.meta = metainfo
            '''
            if isdevicerunning(self.device):
                logging.info("before monkey device %s is running" %self.device)
            else:
                logging.info("before monkey device %s is NOT running" %self.device)
            rs = checkmonkey(self.device)
            if rs == None:
                logging.debug("before kill NO alive monkey")
            else:
                logging.debug("before kill alive monkey: "+' '.join(rs))
            '''
            #beofore exploring, we need to kill existing monkey 
            logging.info("    kill monkey")
            killmonkey(self.device)
            
            '''
            rs = checkmonkey(self.device)
            if rs == None:
                logging.debug("after kill no alive monkey")
            else:
                logging.error("still has monkey runningafter kill alive monkey: "+' '.join(rs))
            '''

            logging.info("    start monkey")
            t = threading.Thread(target=run_monkey, args=(self.device, metainfo['name'],metainfo))
            t.daemon = True
            t.start()
            
            '''
            if isdevicerunning(self.device):
                logging.info("after monkey device %s is running" % self.device)
            else:
                logging.info("after monkey device %s is NOT running" % self.device)
            '''
            logging.info('    start exploring: %s' % self.__app_path)
            plg.explore.explore(self.device, metainfo)
            metainfo['canstop'] = False
            logging.info('    done exploring: %s' % self.__app_path)

            timer.cancel()
            time.sleep(10)
        except Exception as e:
            timer.cancel()
            logging.warning('    failed exploring app: %s' % self.__app_sha1)
            logging.exception('    exception in plg: %s' % e)
            raise PlayerException()


def parse_arguments():
    #
    # [1/5] Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('PREFIX', help='common prefix of AVD names')
    parser.add_argument('NUMBER', help='number of AVDs', type=int)
    parser.add_argument('APPLST', help='list of apps in format "%%(sha1)s\\t%%(path)\\n"')
    parser.add_argument('--out', '-o', help='directory location for output',default="out")
    parser.add_argument('--log', '-l', help='location of log for scheduler', default="scheduler.log")
    parser.add_argument('--timeout', '-t', type=int, help='max testing time for one app, in seconds')
    parser.add_argument('--restart', '-r', type=int, help='max restart times for one app')
    #XIANG
    parser.add_argument('--snapshotavd', '-s', type=str, help='the name of snapshot avd for restore')
    args = parser.parse_args()
    #
    # [2/5] Check existence of samples
    args.apps = Apps(args.APPLST)
    print('apps\t%d' % args.apps.size())
    #
    # [3/5] Check existence of AVDs
    args.avds = ['%s%02d' % (args.PREFIX, i) for i in range(1, 1 + args.NUMBER)]
    process = subprocess.Popen(['android', 'list', 'avd'], stdout=subprocess.PIPE, universal_newlines=True)
    avds = [line.split(':')[1].strip() for line in iter(process.stdout.readline, '') if 'Name: ' in line]
    for avd in args.avds:
        if avd not in avds:
            raise ValueError("AVD not available: %s" % avd)
    print('avds\t' + ', '.join(args.avds))
    #
    # [4/5] Create directory for output
    args.out = os.path.abspath(args.out)
    os.makedirs(args.out, exist_ok=True)
    print("out\t%s" % args.out)
    #
    # [5/5] Configure logging
    logging.basicConfig(filename=args.log, filemode='w', level=logging.INFO,
                        format='%(asctime)s\t%(levelname)s\t%(message)s', datefmt='[%Y-%m-%d %I:%M:%S]')
    print('-' * 80)
    return args


def main():
    args = parse_arguments()
    if args.timeout == None:
        timeout = 300 
    else:
        timeout = args.timeout
    snapshot = args.snapshotavd
    avddir="/home/xpan/.android/avd/"
    plg.utils.androidutil.init()
    logging.info('Program started.')
    avd_queue = queue.Queue()
    players = [Player(avd, 5554 + 4 * index, avd_queue, args.out,timeout,snapshot,avddir) for index, avd in enumerate(args.avds)]
    for player in players:
        player.daemon = True
        player.start()
    for sha1, path in args.apps.list():
        if plg.metadata.is_invalid(path):
            logging.info('Invalid app:%s' % (sha1))
            continue
        for index, player in enumerate(players):
            if not player.is_alive():
                players[index] = Player(player.name, player.port, avd_queue, args.out,timeout,snapshot,avddir)
                players[index].start()
                logging.info('Restarting thread: %s' % player.name)
        player = avd_queue.get()
        player.signal(sha1, path)
        avd_queue.task_done()
        logging.info('App:%s dispatched to avd:%s' % (sha1, player.device))
    for player in players:
        player.join()
    logging.info('Program terminated.')


if __name__ == '__main__':
    main()
