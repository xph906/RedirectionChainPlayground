#!/bin/python3

import socket, subprocess, traceback

#
# Configure parameters as you like.
#
REMOTE_PORT = 9099  # The port on device used by the detection app.
ADB_PROGRAM = 'adb' # The Android Debug Bridge program.

class Client:

    def __init__(self, device, port):
        self.__port = port
        self.__device = device

    def __forward(self):
        args = [ADB_PROGRAM, 'forward', 'tcp:%d' % self.__port, 'tcp:%d' % REMOTE_PORT]
        if self.__device:
            args[1:1] = ['-s', self.__device]
        subprocess.check_call(args)


    def __send(self, sock, data):
        sent = 0
        while sent < len(data):
            sent += sock.send(data[sent:])

    def __recv(self, sock):
        data = b''
        while b'\n' not in data:
            data += sock.recv(1024)
        return data

    def init(self):
        self.__forward()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", self.__port))
        self.__send(sock, b'hello\n')
        response = self.__recv(sock)
        sock.close()
        if response != b'hello\n':
            raise Exception('Notification Detection: init() failed.')

    def send(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", self.__port))
        self.__send(sock, b'send\n')
        sock.close()


if __name__ == '__main__':
    client = Client(None, 9099) # Specify the serial number of the device and local port
    try:
        client.init() # Perform port-forwarding and check whether server is listening.
        client.send() # Command the service to send all pending intents.
    except:
        traceback.print_exc()
