import random

CMCC = ['135', '136', '137', '138', '139', '150', '151', '152', '157', '158', '159', '182', '183', '184', '187', '188']
CUCC = ['130', '131', '132', '155', '156', '185', '186']
CTCC = ['133', '153', '180', '181', '189']

class getDeviceID(object):
    def __init__(self):
        self.imei = genIMEI()
        self.tele = gentele()
        self.iccid = genICCID()
        self.imsi = genIMSI()
        self.wifimac = genwifi()

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

def gentele():
    tele = [8, 6]
    block = random.choice(CMCC + CUCC + CTCC)
    for i in block:
        tele.append(int(i))
    for i in range(0, 8):
        tele.append(random.randint(0, 9))
    return ''.join([str(i) for i in tele])

def genICCID():
    iccid = [8, 9, 8, 6]
    tele = gentele()
    block = tele[2:5]
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
    

def genIMSI():
    imsi = [4, 6, 0, 0]
    for i in range(0, 3):
        imsi.append(random.randint(0, 9))
    for i in gentele()[5:9]:
        imsi.append(i)
    for i in range(0, 3):
        imsi.append(random.randint(0, 9))
    return ''.join([str(i) for i in imsi])
    
def genwifi():
    wifimac = []
    j = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f')
    for i in range(0, 12):
        wifimac.append(j[random.randint(0, 15)])
    for i in [10, 8, 6, 4, 2]:
        wifimac[i:i] = [':']
    return ''.join([str(i) for i in wifimac])

if __name__ == "__main__":
    a = getDeviceID()
    print "imei :", a.imei 
    print "tele :", a.tele 
    print "iccid:", a.iccid
    print "imsi :", a.imsi 
    print "wifi :", a.wifimac
    
