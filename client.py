import socket
import struct
import sys
import threading
import tty, termios, sys
from multiprocessing import Process
import time
#from pynput.keyboard import Listener as keyBoardListener


magic_cookie = 0xfeedbeef
offer_msg_type = 0x2
BUFFER_SIZE = 2048
port = 13117
team_name = "*** Sylvester Stallone ***".encode()

old_settings = None



class Client:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client_socket.bind(('172.1.255.255', port))

    def receive_msg(self):

        print("Client started, listening for offer requests...")
        while True:
            msg, server_address = self.client_socket.recvfrom(7)
            (magicCookie, msg_type, server_port) = struct.unpack('!IbH', msg)
            if magicCookie == magic_cookie:
                if msg_type == 0x2:
                    print("Received offer from " + str(server_address[0]) + ", attempting to connect...")
                    print(server_address)
                    self.connect_to_server(server_address, server_port)

    def connect_to_server(self, server_address, server_connect_port):
        print(server_connect_port)
        try:
            client_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            client_socket_tcp.connect((server_address[0], server_connect_port))
            client_socket_tcp.send(team_name)
            modified_sentence = client_socket_tcp.recv(1024)
            print("From Server: ", modified_sentence.decode())
            modified_sentence = client_socket_tcp.recv(1024)
            print("From Server: ", modified_sentence.decode())
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setcbreak(sys.stdin.fileno())
            except:
                print("unknown exception")
            try:
                self.handle_game(client_socket_tcp)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception as e:
            # self.receive_msg()
            pass

    def handle_game(self, client_socket_tcp):
        self.get_char_from_user(client_socket_tcp)
        client = Client()
        client.receive_msg()


    def get_char_from_user(self, client_socket_tcp):
        start = time.time()
        while True:
            now = time.time()
            if now-start > 10:
                break
            try:
                key = sys.stdin.read(1)
                if not key == "":
                    print (key)
                    client_socket_tcp.send(key.encode())    
            except Exception as e:
                break

client = Client()
client.receive_msg()
