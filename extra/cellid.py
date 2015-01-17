import random, tempfile, subprocess, os


CMCC = ['135', '136', '137', '138', '139', '150', '151', '152', '157', '158', '159', '182', '183', '184', '187', '188']
CUCC = ['130', '131', '132', '155', '156', '185', '186']
CTCC = ['133', '153', '180', '181', '189']


def genIdentities():
    identities = dict()
    identities['number'] = genNumber()
    identities['iccid'] = genICCID(identities['number'])
    identities['imsi'] = genIMSI(identities['number'])
    identities['imei'] = genIMEI()
    identities['mac'] = genMAC()
    return identities


def genIMEI():
    imei = random.choice([[3, 5], [0, 1]])
    for i in range(0, 12):
        imei.append(random.randint(0, 9))
    check = 0
    for i in range(0, 14):
        holder = imei[i] * 2 if (i & 1) else imei[i]
        check += (holder % 10) + (holder // 10)
    imei.append(0 if not (check % 10) else 10 - (check % 10))
    return ''.join([str(i) for i in imei])


def genNumber():
    number = [8, 6]
    block = random.choice(CMCC + CUCC + CTCC)
    for i in block:
        number.append(int(i))
    for i in range(0, 8):
        number.append(random.randint(0, 9))
    return ''.join([str(i) for i in number])


def genICCID(number):
    iccid = [8, 9, 8, 6]
    block = number[2:5]
    carrier = '00' if block in CMCC else '01' if block in CUCC else '06'
    for i in carrier:
        iccid.append(int(i))
    for i in range(0, 13):
        iccid.append(random.randint(0, 9))
    check = 0
    for i in range(0, 19):
        holder = iccid[i] * 2 if (i & 1) else iccid[i]
        check += (holder % 10) + (holder // 10)
    iccid.append(0 if not (check % 10) else 10 - (check % 10))
    return ''.join([str(i) for i in iccid])
    

def genIMSI(number):
    imsi = [4, 6, 0, 0]
    for i in range(0, 3):
        imsi.append(random.randint(0, 9))
    for i in number[5:9]:
        imsi.append(i)
    for i in range(0, 3):
        imsi.append(random.randint(0, 9))
    return ''.join([str(i) for i in imsi])

    
def genMAC():
    wifimac = []
    j = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f')
    for i in range(0, 12):
        wifimac.append(j[random.randint(0, 15)])
    for i in [10, 8, 6, 4, 2]:
        wifimac[i:i] = [':']
    return ''.join([str(i) for i in wifimac])



def replaceIMEI(device=None):
    with tempfile.TemporaryDirectory() as dirname:
        pathname = os.path.join(dirname, 'imei.txt')
        textfile = open(pathname, 'wt')
        textfile.write('%s\n' % genIMEI())
        textfile.close()
        args = ['adb', 'push', pathname, '/data/local/']
        args[1:1] = [] if not device else ['-s', device]
        subprocess.check_call(args)


def replace(device=None, adb='adb'):
    with tempfile.TemporaryDirectory() as dirname:
        identities = genIdentities()
        for name, value in identities.items():
            pathname = os.path.join(dirname, '%s.txt' % name)
            textfile = open(pathname, 'wt')
            textfile.write('%s\n' % value)
            textfile.close()
            args = [adb, 'push', pathname, '/data/local/']
            args[1:1] = [] if not device else ['-s', device]
            subprocess.check_call(args)
