# Function "url_scan(url)" do the url scanning
# Function "app_scan(directory)" do the app scanning 
# 'directory' is where apps downloaded to while exploring

import time
import urllib
import io
import os
import re
import requests
import hashlib

def submit_to_VT(url):
    URL_SCAN_API = "https://www.virustotal.com/vtapi/v2/url/scan"
    parameters = {"url": url,
                  "apikey": "579de2774368337c890728c27a1dcf19295542a5574ffaf8b0629fa5ba270930"}
    try:
        r = requests.post(URL_SCAN_API, params=parameters)
        r = eval(r.text)
        if r['response_code'] == 1:
            return r['response_code'], r['scan_id']
        else:
            return r['response_code'], "Error"
    except Exception as e:
        print(e.message)
        return 0, "Exception"
    
def submit_to_google(url):
    payload = {"client":"api", "apikey":"ABQIAAAAWsFT6W6NQlCEGo1ND4y3BxTbqluCIT483F2nOMmWa1qAX9QsCw", "appver":"1.0", "pver":"3.0", "url":url}
    try:
        r = requests.get("https://sb-ssl.google.com/safebrowsing/api/lookup", params=payload)
        return r.status_code, r.text
    except Exception as e:
        print(e.message)
        return "   ", "Exception"

def url_scan(url):
    url = url.strip()
    sha1 = hashlib.new("sha1", url.encode(encoding='gb2312')).hexdigest()
    result = {}
    r = {}
    r_Google = []
    r_Google.append(submit_to_google(url))
    r_VT = []
    r_VT.append(submit_to_VT(url))
    r["Google"] = r_Google
    r["VT"] = r_VT
    result[url] = r
    print(sha1, ":", str(result))
    f = open(os.path.join("url_result", sha1), 'a')
    f.write(str(result))
    f.close()
    print("*"*50)

#**********************************************************************
def cal_sha1(fpath):
    """get the sha1 value first"""
    m = hashlib.sha1()
    f = io.FileIO(fpath, 'r')
    bytestream = f.read(1024)
    while(bytestream != b''):
        m.update(bytestream)
        bytestream = f.read(1024)
    f.close()
    sha1value = m.hexdigest()
    return sha1value

def check(app_dic, f_done, f_error):
    """check an app has scanned or not"""
    f_done.seek(0,0)
    for line in f_done:
        app_dic[line.split(" : ")[0].strip()]=1
    f_error.seek(0,0)
    for line in f_error:
        if line.startswith("Error:") or line.startswith("Exception:"):
            continue
        app_dic[line.split("\t")[1].strip()]=1

def get_app_dic(directory):
    """downloaded apks under directory"""
    """return apk list"""
    # value == 1: this app has been checked
    # value == 0: this app has not been checked
    app_dic={}
    mk = lambda root, name: os.path.abspath(os.path.join(root, name))
    for root, dirs, names in os.walk(directory):
        for name in names:
            if name.lower().strip().endswith(".apk"):
                app_dic[mk(root, name)]=0
    return app_dic

def get_app_list():
    """return an app list with crawler, only basename"""
    app_list = []
    for root, dirs, names in os.walk("/nfs/android-app/data/sample/00"):
        for name in names:
            if name.lower().endswith(".apk"):
                app_list.append(name)
    return app_list


URL_scan = "https://www.virustotal.com/vtapi/v2/file/scan"
URL_rescan = "https://www.virustotal.com/vtapi/v2/file/rescan"
API_KEY = "d6f2a57054e814d62f6c990b81b78e49aaa2e6e92da3ddf1b2557e8bcceb9fb3"

def app_scan(directory):
    app_dic = get_app_dic(directory)
    app_list = get_app_list()
    f_done = open("scan_id.txt", 'a+')
    f_error = open("error.txt", 'a+')
    check(app_dic, f_done, f_error)
    for app_path in app_dic:
        sha1 = cal_sha1(app_path)
        if app_dic[app_path] == 1: # has uploaded
            continue
        elif os.path.getsize(app_path) > 32*1024*1024: # larger than 32MB
            print( '%s\t%dMB' % (app_path, os.path.getsize(app_path)/1024/1024))
            continue
        elif cal_sha1(app_path) + ".apk" in app_list: # has in apps with crawler
            f = open(os.path.join("/nfs/android-app/data/virus_total_report", sha1[0:2], sha1+'.txt'))
            scan_id = eval(f.read())['scan_id']
            f.close()
            f_done.write(app_path + " : " + scan_id + "\n")
            continue
        print("processing\t%s" % app_path) # begin to process
        time.sleep(15)
        try:
            resource = sha1
            parameters = {"resource":resource, "apikey": API_KEY}
            r = requests.post(URL_rescan, params=urllib.parse.urlencode(parameters))
            if r.text.strip():
                r = eval(r.text)
                if r['response_code'] == 1:
                    print("%(app_path)s already uploaded" % locals())
                    f_done.write(app_path+" : "+r["scan_id"]+"\n")
                    continue
            result = requests.post(URL_scan, params={'apikey': API_KEY},files={'file': open(app_path, 'rb')})
            result = eval(result.text)
            if result["response_code"] == 1:
                f_done.write(app_path+" : "+result["scan_id"]+"\n")
                print(app_path,"\t..done!")
            else:
                f_error.write("Error: response_code = %d\n\t%s\n"%(result["response_code"],app_path))
                print(app_path,"\t..Error: response_code = %d"%(result["response_code"]))
        except Exception as e:
            f_error.write("Exception: "+"\n")
            print("%s\t%10dMB\t..Exception " % (app_path, os.path.getsize(app_path)/1024/1024))
            f_error.write("\t"+app_path+"\n")
        finally:
            app_dic[app_path]=1
    f_done.close()
    f_error.close()

if __name__ == "__main__":
    url_scan(url)
    app_scan(app_path)
