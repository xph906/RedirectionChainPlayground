#!/usr/bin/python3

import threading, argparse, subprocess, logging, queue, os, time
import plg, plg.metadata, plg.utils.androidutil, plg.utils.logcat, plg.settings, plg.fuzz
import extra.cellid, extra.notdet


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

    def __init__(self, name, port, avd_queue, out_root):
        threading.Thread.__init__(self)
        self.__name = name
        self.__port = port
        self.__avd_queue = avd_queue
        self.__app_queue = queue.Queue()
        self.__app_sha1 = None
        self.__app_path = None
        self.__out_root = out_root
        self.__intents = None

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
        logging.info('Killing avd due to timeout: %s' % self.device)
        print('Killing avd due to timeout: %s' % self.device)
        try:
            subprocess.check_call(['adb', '-s', self.device, 'emu', 'kill'])
        except:
            logging.info('Command \'adb emu kill\' failed: %s' % self.device)

    def run(self):
        while True:
            self.__wait()
            try:
                self.__launch()
                self.__install()
                self.__explore()
            except PlayerException as e:
                logging.info('Giving up app %s' % self.__app_sha1)
            self.__clean()

    def __wait(self):
        self.__avd_queue.put(self)
        sha1, path = self.__app_queue.get()
        self.__app_sha1 = sha1
        self.__app_path = path
        self.__intents = list()
        os.makedirs(self.directory, exist_ok=True)

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

    def __launch(self):
        try:
            args = ['emulator64-x86']
            args[1:1] = ['-no-snapshot-save', '-qemu', '-enable-kvm']
            args[1:1] = ['-memory', '512']
            args[1:1] = ['-scale', '.5']
            args[1:1] = ['-port', '%d' % self.__port]
            args[1:1] = ['@%s' % self.__name]
            logging.info('Launching device %s' % self.device)
            subprocess.Popen(args, stdout=open(os.path.join(self.directory, 'stdout.txt'), 'w'), stderr=open(os.path.join(self.directory, 'stderr.txt'), 'w'))
            time.sleep(2)
            plg.utils.androidutil.waitfordevice(self.device, timeout=1200)
        except subprocess.TimeoutExpired:
            logging.warning('Failed launching device: %s' % self.device)
            raise PlayerException()

    def __install(self):
        try:
            status = 'before installing'
            command = plg.utils.androidutil.getadbcmd(['install', self.__app_path], self.device)
            subprocess.check_output(command, stderr=subprocess.STDOUT)
            status = 'installed.'
            plg.utils.logcat.clearlogcat(self.device)
            status = 'logcat cleared'
            plg.utils.logcat.logcat(os.path.join(self.directory, 'logcat.txt'), self.device)
            status = 'logcat created.'
            extra.cellid.replace(self.device)
            status = 'identities replaced'
        except subprocess.CalledProcessError as e:
            logging.warning('Failed installing app %s (%s)' % (self.__app_sha1, status))
            raise PlayerException()

    def __explore(self):
        try:
            timer = threading.Timer(1200, self.__terminate)
            timer.start()
            metainfo = plg.metadata.getmetadata(self.__app_path)
            plg.fuzz.explore(self.device, metainfo, self.__decider(metainfo))
            client = extra.notdet.Client(self.device, self.__port + 2)
            client.init()
            client.send()
            timer.cancel()
            time.sleep(10)
        except Exception as e:
            timer.cancel()
            logging.warning('Failed exploring app: %s' % self.__app_sha1)
            logging.exception('Exception in plg: %s' % e)
            raise PlayerException()
            
    def __decider(self, metainfo):
        def decider(intent, package):
            self.__intents.append((intent, package))
            return package == plg.settings.LAUNCHER_PKG or package in metainfo['name']
        return decider


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
    plg.utils.androidutil.init()
    logging.info('Program started.')
    avd_queue = queue.Queue()
    players = [Player(avd, 5554 + 4 * index, avd_queue, args.out) for index, avd in enumerate(args.avds)]
    for player in players:
        player.daemon = True
        player.start()
    for sha1, path in args.apps.list():
        if plg.metadata.is_invalid(path):
            logging.info('Invalid app:%s' % (sha1))
            continue
        for index, player in enumerate(players):
            if not player.is_alive():
                players[index] = Player(player.name, player.port, avd_queue, args.out)
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
