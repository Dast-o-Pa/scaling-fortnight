import socket
import threading
import os

ENCODING = 'utf-8'
MESSAGE_LENGTH_SIZE = 64
class Node:
    def __init__(self, cluster_path, port):
        self.host = socket.gethostbyname(socket.gethostname())
        
        self.upd_port = port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.upd_port))

        self.tcp_port = self.get_free_tcp_port()
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))

        if port != 6655:
            self.tcp_socket.listen()

        self.label = "N" + str(self.upd_port)
        if not os.path.exists(self.label):
            os.mkdir(self.label)        

        file = open(cluster_path, 'r')
        self.cluster = []
        for line in file:
            info = list(line.split())
            self.cluster.append(info)
        file.close()

    def client_handler(self):
        while True:
            input_string = input()
            if input_string == 'DISCONNECT': 
                break
            elif len(input_string.split()) != 2:
                print("[ERROR]: Invalid request.")
            elif input_string.split()[0] != "GET":
                print("[ERROR]: Invalid request.")
            else:
                self.send_msg(input_string)

    def send_msg(self, msg):
        message = msg.encode(ENCODING)
        msg_length = len(message)
        msg_length = str(msg_length).encode(ENCODING)
        msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))

        if self.upd_port == 7755:
            self.udp_socket.sendto(msg_length, (self.host, 6655))
            self.udp_socket.sendto(message, (self.host, 6655))
        else:
            self.udp_socket.sendto(msg_length, (self.host, 7755))
            self.udp_socket.sendto(message, (self.host, 7755))

    def server_handler(self):
        while True:
            data, address = self.udp_socket.recvfrom(MESSAGE_LENGTH_SIZE)
            message_length = int(data.decode(ENCODING))
            msg = self.udp_socket.recvfrom(message_length)[0].decode(ENCODING)   

            if msg.split()[0] == "GET":
                print("[MESSAGE]: " + "N" + str(address[1]) + " wants " + msg.split()[1] + ".")  
            elif msg.split()[0] == "[MESSAGE]:":
                print(msg)
                # print(msg.split()[3])
                # print(msg.split()[1])
                # print(msg.split()[-1])
                tcp_client = threading.Thread(target=self.receive_file, args=(msg.split()[3], int(msg.split()[-1])))
                tcp_client.start()
            else:
                print(msg)

            if os.path.isfile('./' + self.label + '/' + msg.split()[1]):
                self.send_msg("[MESSAGE]: " + self.label + " has " + msg.split()[1] + " and the TCP port is: " + str(self.tcp_port))
 
    def discovery_handler(self):
        pass

    def run(self):
        udp_client = threading.Thread(target=self.client_handler)
        udp_client.start()

        udp_server = threading.Thread(target=self.server_handler)
        udp_server.start()

        if self.upd_port != 6655:
            tcp_server = threading.Thread(target=self.file_server)
            tcp_server.start()

        # server.join()
        # discovery = threading.Thread(target=self.discovery_handler, args=(client, ))
        # discovery.start()

    def get_free_tcp_port(self):
        tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmp_socket.bind(('', 0))
        address, port = tmp_socket.getsockname()
        tmp_socket.close()
        return port

    def file_server(self):
        while True:
            connection, address = self.tcp_socket.accept()
            print(address)

            message_length = int(connection.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
            file_name = connection.recv(message_length).decode(ENCODING)

            print(file_name)

            f = open('./' + self.label + '/' + file_name,'rb')
            l = f.read(MESSAGE_LENGTH_SIZE)
            while (l):
                connection.send(l)
                l = f.read(MESSAGE_LENGTH_SIZE)
            f.close()
            print('Done sending')
            connection.close()


    def receive_file(self, file_name, port):
        self.tcp_socket.connect((self.host, port))
        message = file_name.encode(ENCODING)
        msg_length = len(message)
        msg_length = str(msg_length).encode(ENCODING)
        msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))
        self.tcp_socket.send(msg_length)
        self.tcp_socket.send(message)

        f = open('./' + self.label + '/' + file_name, 'wb')
        while True:
            data = self.tcp_socket.recv(MESSAGE_LENGTH_SIZE)
            if not data:
                break
            f.write(data)
        f.close()
        print("file finish")
        self.tcp_socket.close()
