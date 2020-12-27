import socket
import struct
import sys
import threading
#from pynput.keyboard import Listener as keyBoardListener


magic_cookie = 0xfeedbeef
offer_msg_type = 0x2
BUFFER_SIZE = 2048
port = 13117
broadcast_address = ('255.255.255.255', port)
team_name = b"IDO ROM <3"


class Client:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client_socket.bind(('', port))

    def receive_msg(self):

        print("Client started, listening for offer requests...")

        msg, server_address = self.client_socket.recvfrom(BUFFER_SIZE)
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
            print("From Server: ", modified_sentence)
            modified_sentence = client_socket_tcp.recv(1024)
            print("From Server: ", modified_sentence)
            self.handle_game(client_socket_tcp)
        except Exception as e:
            self.receive_msg()

    def handle_game(self, client_socket_tcp):
       # keyBoard_Listener = keyBoardListener(on_press=lambda key: self.on_press(key, client_socket_tcp))
      #  keyBoard_Listener.start()

        while True:
            stop = client_socket_tcp.recv(1024)
            print(stop)
            if stop == b"stop":
           #     keyBoard_Listener.stop()
                break

        print("finished game")


    def on_press(self,key,socket):
        socket.send(str.encode(str(key)))





client = Client()
client.receive_msg()
