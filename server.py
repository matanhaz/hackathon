import multiprocessing
import threading
import socket
import struct
import time
from timeit import Timer
from multiprocessing import Process

import select
import scapy.all as scapy

CYAN = '\u001b[36m'
YELLOW = '\u001b[33m'
BLUE =  '\u001b[34m'
RESET= '\u001b[0m'




server_broadcast_port = 13117
BUFFER_SIZE = 2048
udp_lock = threading.Lock()
magic_cookie = 0xfeedbeef
offer_msg_type = 0x2

dict_lock = threading.Lock()


teams = []
group1 = []
group2 = []
teams_counters ={}

start_message_part1 = """Welcome to Keyboard Spamming Battle Royale.
Group 1:
==
"""
start_message_part2 = """
Group 2:
==
"""
start_message_part3 = """
Start pressing keys on your keyboard as fast as you can!!
"""


class Server:

    def __init__(self):
        self.server_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def main(self):
        while True:
            teams.clear()
            group1.clear()
            group2.clear()
            teams_counters.clear()
            self.start_server()


    def start_server(self):
        server_ip = scapy.get_if_addr("eth1")
        print("Server started,listening on IP address %s" % (server_ip))
        print("I'm waiting for clients, someone wants to play? ")

        start = time.time()

        while True:
            now = time.time()
            if now-start > 10:
                break
            try:

                server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                server_socket_tcp.settimeout(10)
                server_socket_tcp.bind((server_ip, 0))
                tcp_port = server_socket_tcp.getsockname()[1]
                server_socket_tcp.listen(1)
                udp_lock.acquire()
                udp_connection_thread= threading.Thread(target=self.wait_for_accept_offer,
                                                         args=(tcp_port,))
                udp_connection_thread.start()

                client_socket_tcp, client_address = server_socket_tcp.accept()
                udp_lock.release()

                name = client_socket_tcp.recv(2048)
                print(BLUE + "Willkommen zuhause: " + name.decode() + RESET)
                print("GIT RDY!!!")
                teams.append((name, client_socket_tcp))
                teams_counters[name]=0
                # client_socket_tcp.send(b"you are connected, wait for game to start")
                print("waiting for more clients")

            except Exception as e:
                udp_lock.release()
                continue

        time.sleep(2)
        print("Starting Game...")
        self.handle_game()

    def wait_for_accept_offer(self,server_port):
        while udp_lock.locked():
            msg = struct.pack('!IbH', magic_cookie, offer_msg_type, server_port)
            self.server_udp_socket.sendto(msg, ('172.1.255.255', server_broadcast_port))


    def handle_game(self):
        self.assign_to_groups()
        threads = []
        for team in teams:
            thread = threading.Thread(target=self.handle_game_single_client,
                                      args=(team,))
            threads.append(thread)
            thread.start()
        for x in threads:
            x.join()

        g1_counter = 0
        g2_counter = 0
        for group in teams_counters.keys():
            if group in group1:
                g1_counter+=teams_counters[group]
            else:
                g2_counter+=teams_counters[group]

        winner = (group1,1) if g1_counter>g2_counter else (group2,2)
        print("""Game over !
        Group 1 typed in %i characters.
        Group 2 typed in %i characters.
        Group %i wins!
        Congratulations to the winners:
        =="""%(g1_counter, g2_counter, winner[1]))


        for x in winner[0]:
            print(x.decode())




        # print(start_message_part1 + self.to_string_group(group1) + start_message_part2 +
        #    self.to_string_group(group2) + start_message_part3)

        # c.release()
        # c.notify_all()

    def handle_game_single_client(self, tup):
        # while game_lock.locked():
        #     print("Thread " + str(threading.current_thread().ident) + " is going night night")
        #     time.sleep(1)
        #
        # print("Thread " + str(threading.current_thread().ident) + " is NOT going night night")
        group_counter = 0
        tup[1].send((BLUE + start_message_part1 + self.to_string_group(group1) + start_message_part2 +
                     self.to_string_group(group2) + start_message_part3 +RESET).encode())

        # c = tup[1].recv(1)
        # team_counter+=1
        # print(tup[0] + b" " + str.encode(str(team_counter)))
        # tup[1].send(b"KIBALTI ET HATAV YA KAKI")
        # ready = select.select([tup[1]], [], [],10)
        tup[1].setblocking(0)
        start = time.time()

        while True:
            now = time.time()
            if now - start > 10:
                break
            try:
                c = tup[1].recv(3)
                group_counter+=1
                tup[1].send("KIBALTI ET HATAV YA KAKI").encode()
            except:
                continue

        # tup[1].send(b"stop")
        dict_lock.acquire()
        teams_counters[tup[0]] = group_counter
        dict_lock.release()
        #print("group counter " + (str(group_counter)))
        tup[1].close()


    def assign_to_groups(self):
        group1bool = True
        for i in range(0, len(teams)):
            if group1bool:
                group1.append(teams[i][0])
                group1bool = False
            else:
                group2.append((teams[i][0]))
                group1bool = True

    def to_string_group(self, group):
        ret_str = ""
        for g in group:
            ret_str = ret_str + (str(g.decode()))
        return (ret_str)


server = Server()
server.main()