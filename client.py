import socket
import struct
import sys
import tty, termios, sys
import time
import asyncio

magic_cookie = 0xfeedbeef
offer_msg_type = 0x2
BUFFER_SIZE = 1024
port = 55555
broadcast_address_ssh = '172.1.255.255'
broadcast_address_local_host = '127.0.255.255'
offer_message_length = 7

team_name = "[Errno 32] Broken Pipe\n".encode() # team name
old_settings = None


class Client:
    def __init__(self):
        # initiate client UDP socket - enbales reuse address and broadcast
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client_socket.bind((broadcast_address_ssh, port)) # recieve messages from entire subnet

    async def receive_msg(self):

        print("Client started, listening for offer requests...")
        while True:
            msg, server_address = self.client_socket.recvfrom(offer_message_length)
            (magicCookie, msg_type, server_port) = struct.unpack('!IbH', msg) # 7 bytes, ! - big endian
            if magicCookie == magic_cookie:
                if msg_type == 0x2:
                    print("Received offer from " + str(server_address[0]) + ", attempting to connect...") # recieved proper offer message (magic cookie and type)
                    # print(server_address)
                    await self.connect_to_server(server_address, server_port)

    async def connect_to_server(self, server_address, server_connect_port):
        # print(server_connect_port)
        try: # initiate a client TCP socket - again reuse addr, port and enable broadcast, and try to connect to the server

            client_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            client_socket_tcp.connect((server_address[0], server_connect_port))
            client_socket_tcp.send(team_name)
            modified_sentence = client_socket_tcp.recv(BUFFER_SIZE)
            print("From Server: ", modified_sentence.decode()) # recieve start game message from server
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd) # turn stdin.read to a non - blocking method using termios package
            try:
                tty.setcbreak(sys.stdin.fileno())
            except:
                print("unknown exception")
            try:
                #if not client_socket_tcp.closed():
                await self.handle_game(client_socket_tcp)

            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception as e:
            # self.receive_msg()
            #print(e)
            time.sleep(0.1)

    async def handle_game(self, client_socket_tcp):
        # create 2 taks ->  1. tWrite - read from keyboard and send to server
        #                   2. tRead - recv from server and print
        # we let them both run and the first one to end terminates both tasks
        tWrite = asyncio.create_task(self.get_char_from_user(client_socket_tcp))
        tRead = asyncio.create_task(self.recv_from_server(client_socket_tcp))
        finished, unfinished = await asyncio.wait([tRead, tWrite], return_when = asyncio.FIRST_COMPLETED)
        for task in unfinished: # terminate all tasks that haven't been finished
            task.cancel()


        # when finished, start from the beginning again
        print("Game Finished")
        client = Client()
        await client.receive_msg()


    async def get_char_from_user(self, client_socket_tcp):
        loop = asyncio.get_event_loop()
        while True:
            try:
                key = await loop.run_in_executor(None, lambda: sys.stdin.read(1)) # read key from non blocking stdin
                if not key == "":
                    print (key)
                    client_socket_tcp.send(key.encode()) # send to server
            except Exception as e:
                break

    async def recv_from_server(self, client_socket_tcp):
        loop = asyncio.get_event_loop()
        while True:
            try:
                modified_sentence = await loop.run_in_executor(None, lambda: client_socket_tcp.recv(BUFFER_SIZE)) # recv from server
                if not modified_sentence: # empty msg = server finished the game and closed the connection
                    print("SERVER TOLD ME GAME IS OVER :( ")
                    break
                print (modified_sentence.decode())
            except:
                print("SERVER TOLD ME GAME IS OVER :( ")
                break

client = Client()
asyncio.run(client.receive_msg())
