import threading
import socket
import struct
import time

import scapy.all as scapy # scapy to use IP

# colors for bonus
CYAN = '\u001b[36m'
YELLOW = '\u001b[33m'
BLUE =  '\u001b[34m'
RESET= '\u001b[0m'
RED = '\u001b[31m'
GREEN = '\u001b[32m'



server_broadcast_port = 55555
BUFFER_SIZE = 2048
udp_lock = threading.Lock()
magic_cookie = 0xfeedbeef
offer_msg_type = 0x2

dict_lock = threading.Lock()


teams = []
group1 = []
group2 = []
teams_counters ={}

best_team_ever = [None,-1] # we save the best teams as a cool stat :)

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
        # initiate server UDP socket - enbales reuse address and broadcast
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
            if now-start > 10: # we mesure time and close offer sending state after 10 seconds
                break
            try:
                # initiate a server TCP socket - again reuse addr, port and enable broadcast, and listen for client that supposed to connect
                server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                server_socket_tcp.settimeout(10)
                server_socket_tcp.bind((server_ip, 0)) # 0 -> generate free port
                tcp_port = server_socket_tcp.getsockname()[1] # get the free port allocated by OS
                server_socket_tcp.listen(1)
                udp_lock.acquire()
                udp_connection_thread= threading.Thread(target=self.wait_for_accept_offer,
                                                         args=(tcp_port,))
                udp_connection_thread.start()

                client_socket_tcp, client_address = server_socket_tcp.accept()
                udp_lock.release()
                client_socket_tcp.setblocking(0)
                try:
                    name = client_socket_tcp.recv(2048) # recieve team name from client
                except:
                    print("User did not insert name")
                    client_socket_tcp.close()
                    time.sleep(0.2)
                    continue
                else:
                    print(BLUE + "Willkommen zuhause: " + name.decode() + RESET) # a litlle German :)
                    #print("GIT RDY!!!")
                    teams.append((name, client_socket_tcp)) # add new team to our data structure
                    teams_counters[name]=0
                    # client_socket_tcp.send(b"you are connected, wait for game to start")
                    # print("waiting for more clients")

            except Exception as e:
                udp_lock.release()
                continue

        time.sleep(0.1)
        if len(teams) == 0:
            print("I Guess no one want's to play")
        else:
            print(RED + "Initiating Game Protocol..." + RESET)
            self.handle_game()

    def wait_for_accept_offer(self,server_port):
        while udp_lock.locked():
            msg = struct.pack('!IbH', magic_cookie, offer_msg_type, server_port) # 7 bytes, ! - big endian
            self.server_udp_socket.sendto(msg, ('172.1.255.255', server_broadcast_port)) # send broadcast offer to all subnet
            time.sleep(0.1)

    def handle_game(self):
        # handle game
        self.assign_to_groups()
        threads = []
        for team in teams: # create thread for each client / team
            thread = threading.Thread(target=self.handle_game_single_client,
                                      args=(team,))
            threads.append(thread)
            thread.start()
        for x in threads:
            x.join() # wait for all clients to finish

        g1_counter = 0 # group counters
        g2_counter = 0
        for group in teams_counters.keys():
            if group in group1:
                g1_counter+=teams_counters[group]
            else:
                g2_counter+=teams_counters[group]

        winner = (group1,1) if g1_counter>g2_counter else (group2,2) # generate game summary msg
        end_messsage = """Game over !
        Group 1 typed in %i characters.
        Group 2 typed in %i characters.
        Group %i wins!
        Congratulations to the winners:
        ==
        """%(g1_counter, g2_counter, winner[1])


        for x in winner[0]:
            end_messsage += (GREEN + x.decode())

        end_messsage += YELLOW + "some fun statistics:"
        end_messsage += BLUE + """best team to ever play in this server are the legendaries %s,
                and their score was: %d"""  %(best_team_ever[0],best_team_ever[1]) + RESET

        print(end_messsage)

        for team in teams:
            try:
                team[1].send(end_messsage.encode())
            except:
                continue


        for team in teams:
            try:
                team[1].close()
            except:
                continue


    def handle_game_single_client(self, tup):
        group_counter = 0
        tup[1].send((BLUE + start_message_part1 + self.to_string_group(group1) + start_message_part2 +
                     self.to_string_group(group2) + start_message_part3 +RESET).encode())

        start = time.time()
        print("here 1")
        while True:
            now = time.time()
            if now - start > 10:
                break
            try:
                c = tup[1].recv(3) # recv char and increase counter
                if c:
                    time.sleep(1)
                    group_counter+=1
            except:
                time.sleep(1)
                continue
        print("here 2")

        # tup[1].send(b"stop")
        dict_lock.acquire() # lock and update statistics
        teams_counters[tup[0]] = group_counter
        if group_counter>best_team_ever[1]:

            best_team_ever[0] = tup[0].decode()
            best_team_ever[1]= group_counter
        dict_lock.release()
        #print("group counter " + (str(group_counter)))
        #tup[1].close()


    def assign_to_groups(self): # make interleaving group assigning function
        group1bool = True
        for i in range(0, len(teams)):
            if group1bool:
                group1.append(teams[i][0])
                group1bool = False
            else:
                group2.append((teams[i][0]))
                group1bool = True

    def to_string_group(self, group): # print group name from data structure
        ret_str = ""
        for g in group:
            ret_str = ret_str + (str(g.decode()))
        return (ret_str)


server = Server()
server.main()