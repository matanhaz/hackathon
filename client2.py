import socket
import struct
import sys
import threading
import tty, termios, sys
from multiprocessing import Process
import time
import asyncio
#from pynput.keyboard import Listener as keyBoardListener


magic_cookie = 0xfeedbeef
offer_msg_type = 0x2
BUFFER_SIZE = 2048
port = 13117
team_name = "*** Cookie Monset ^ _ ^  ***\n".encode()

old_settings = None



class Client:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client_socket.bind(('172.1.255.255', port))

    async def receive_msg(self):

        print("Client started, listening for offer requests...")
        while True:
            msg, server_address = self.client_socket.recvfrom(7)
            (magicCookie, msg_type, server_port) = struct.unpack('!IbH', msg)
            if magicCookie == magic_cookie:
                if msg_type == 0x2:
                    print("Received offer from " + str(server_address[0]) + ", attempting to connect...")
                    print(server_address)
                    await self.connect_to_server(server_address, server_port)

    async def connect_to_server(self, server_address, server_connect_port):
        print(server_connect_port)
        try:
            client_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            client_socket_tcp.connect((server_address[0], server_connect_port))
            client_socket_tcp.send(team_name)
            modified_sentence = client_socket_tcp.recv(1024)
            print("From Server: ", modified_sentence.decode())
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setcbreak(sys.stdin.fileno())
            except:
                print("unknown exception")
            try:
                await self.handle_game(client_socket_tcp)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception as e:
            # self.receive_msg()
            print(e)

    async def handle_game(self, client_socket_tcp):
        tWrite = asyncio.create_task(self.get_char_from_user(client_socket_tcp))
        tRead = asyncio.create_task(self.recv_from_server(client_socket_tcp))
        # tTimeout = asyncio.create_task(self.timeout_check())
        finished, unfinished = await asyncio.wait([tRead, tWrite], return_when = asyncio.FIRST_COMPLETED)
        for task in unfinished:
            task.cancel()


        # when finished, start from the beginning again
        print("Game Finished")
        client = Client()
        await client.receive_msg()


    async def get_char_from_user(self, client_socket_tcp):
        print("HOLA")
        loop = asyncio.get_event_loop()
        while True:
            try:
                key = await loop.run_in_executor(None, lambda: sys.stdin.read(1))
                if not key == "":
                    print (key)
                    client_socket_tcp.send(key.encode())
            except Exception as e:
                break

    async def recv_from_server(self, client_socket_tcp):
        loop = asyncio.get_event_loop()
        while True:
            try:
                modified_sentence = await loop.run_in_executor(None, lambda: client_socket_tcp.recv(1024))
                if not modified_sentence:
                    print("SERVER TOLD ME GAME IS OVER :( ")
                    break
                print (modified_sentence)
            except:
                print("SERVER TOLD ME GAME IS OVER :( ")
                break

client = Client()
asyncio.run(client.receive_msg())