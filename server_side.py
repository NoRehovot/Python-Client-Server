from scapy.all import *
from socket import *
from threading import Thread
import time
import subprocess
from cryptography.fernet import Fernet
import select

BUFF = 1024
CLIENT_ID_STRING = "636C69656E7420696E74726F64756365"
SERVER_ID_STRING = "736572766572207265616479"

global commands  # commands the client can send to the server
global ended_all  # represents whether a client decided to end all communication of the server
global connected_num
global key_client
global all_clients
global time_client
global quit_password


def get_this_ip():
    """
    return the server computer ip
    """
    output = str(subprocess.check_output("ipconfig"))
    output = output.replace(". ", "").replace(" ", "").replace(r"\r", "").replace(r"\n", ":").split(":")
    ip = output[output.index("IPv4Address") + 1]
    return ip


def get_free_port_socket():
    """
    find available port to use for communication
    """
    ip = get_this_ip()

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((ip, 0))  # let the system find an open port
    s.listen(2)
    return s


def inform_client(server_details, client_ip, client_port):
    """
    server informs the client that it is ready for communication
    server sends client its ip and port
    """
    global connected_num

    inform_socket = socket(AF_INET, SOCK_DGRAM)  # setup a TCP socket

    inform_message = SERVER_ID_STRING + " server_ip " + str(server_details[0]) + " server_port " + str(server_details[1]) + " connected " + str(connected_num)

    # send the server info to the client
    inform_socket.sendto(bytes(inform_message, 'utf-8'), (client_ip, int(client_port)))
    inform_socket.close()


# ---------------
# client commands
# ---------------


def client_exit(client_socket, sym_key):
    print("client [" + client_socket.getsockname()[0] + "] has ended communication")
    end_message = "FIN"
    client_socket.send(end_message.encode('utf-8'))
    return True, False


def client_quit(client_socket, sym_key, password):
    global quit_password

    if password == quit_password:
        client_exit(client_socket, sym_key)
        return True, True
    else:
        wrong_password_message = "Server: Wrong Password!"
        client_socket.send(encode_message(wrong_password_message.encode('utf-8'), sym_key))
        return False, False


def inform_if_quit(client_sockets):
    """
    if one client quit, tell all clients to end connection on their end
    """
    if not client_sockets:
        return

    for client in client_sockets:
        client_exit(client, 0)
        client.close()


def client_time(client_socket, sym_key):
    this_time = time.localtime()
    this_time = time.strftime("%H:%M:%S", this_time)
    client_socket.send(encode_message(str(this_time).encode('utf-8'), sym_key))
    return False, False


def decode_message(message, sym_key):
    """
    decode a message with the symmetric key
    """
    return Fernet(sym_key).decrypt(message)


def encode_message(message, sym_key):
    """
    encode a message with the symmetric key
    """
    return Fernet(sym_key).encrypt(message)


def send_to_all(client_message, sender):
    global all_clients
    global key_client

    client_message = client_message.encode('utf-8')

    for client in all_clients:
        if client is not sender:  # if client is not the one who sent the broadcast
            client.send(encode_message(client_message, key_client[client]))


def handle_client_message(client_socket, client_message, sym_key, connection_socket):
    """
    respond to the client accordingly
    - do command if message is a command
    - echo if message isn't a command
    """
    global commands
    global ended_all
    ended = False

    # decrypt the message
    client_message = decode_message(client_message, sym_key).decode('utf-8')

    if client_message in commands.keys():
        client_action = commands[client_message]
        ended, ended_all = client_action(client_socket, sym_key)  # do command
    elif client_message.split(" ")[0] == "broadcast":
        send_to_all(" ".join(client_message.split(" ")[1:]), client_socket)
    elif client_message.split(" ")[0] == "QUIT":
        ended, ended_all = client_quit(client_socket, sym_key, " ".join(client_message.split(" ")[1:]))
    else:
        echo_message = "Echo: " + client_message
        echo_message = encode_message(echo_message.encode('utf-8'), sym_key)
        client_socket.send(echo_message)

    return ended


def generate_key():
    key = Fernet.generate_key()
    return key


def key_exchange(client_socket, sym_key):
    """
    send the symmetric key to the client
    """
    transfer_message = sym_key
    client_socket.send(transfer_message + " 69420".encode('utf-8'))


def scan_for_client(connection_socket):
    """
    scan for a client introduction message
    """

    global ended_all

    while not ended_all:
        pkt = sniff(count=1, filter="host 255.255.255.255")  # sniff packets until a broadcast is found
        content = pkt[0].show(dump=True)  # convert packet to a string
        if CLIENT_ID_STRING in content:  # check if it is in fact a client introduction message
            content = content.split(" ")
            client_data = (content[content.index("client_ip") + 1].replace("'", "").replace(" ", "").replace("\n", ""), content[content.index("client_port") + 1].replace("'", "").replace(" ", "").replace("\n", ""))
            server_details = connection_socket.getsockname()  # this is the server's ip and port
            # send a reply to the client
            inform_client(server_details, client_data[0], client_data[1])


def disconnect_clients():
    """
    if it has been more than 2 minutes since last message from the client, disconnect client
    """
    global all_clients
    global time_client

    while True:
        if all_clients:
            for client in all_clients:
                if time_client[client] + 120 < time.time():
                    client_exit(client, 0)
                    client.close()
                    all_clients.remove(client)


def handle_all_clients(connection_socket):
    global ended_all
    global connected_num
    global key_client
    global all_clients
    global time_client

    all_clients = []

    inputs = [connection_socket]
    outputs = []
    key_client = {

    }
    time_client = {

    }

    disconnect_thread = Thread(target=disconnect_clients, daemon=True)
    disconnect_thread.start()

    while not ended_all:
        readable, writable, exceptions = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is connection_socket:  # if client sent a connection request
                client = s.accept()[0]  # accept client
                print("client [" + client.getsockname()[0] + "] has connected to the server")
                client.setblocking(0)

                inputs.append(client)  # add client to input sockets list
                time_client[client] = time.time()
                all_clients.append(client)  # add client to global client list

                connected_num = connected_num + 1

                sym_key = generate_key()  # generate key
                key_exchange(client, sym_key)  # transfer the symmetric key to the client
                key_client[client] = sym_key  # add the symmetric key to the key-client dictionary
            else:  # if client sent a message
                try:
                    client_message = s.recv(BUFF)  # get the message
                    if client_message:
                        time_client[s] = time.time()

                        ended = handle_client_message(s, client_message, key_client[s], connection_socket)  # handle client message

                        if ended:  # if client ended communication, close socket and remove from inputs
                            s.close()
                            inputs.remove(s)  # remove from inputs
                            all_clients.remove(s)  # remove from global client list
                            connected_num = connected_num - 1
                    else:
                        s.close()
                        inputs.remove(s)  # remove from inputs
                        all_clients.remove(s)  # remove from global client list
                except ConnectionResetError:
                    s.close()
                    inputs.remove(s)  # remove from inputs
                    all_clients.remove(s)  # remove from global client list
                    connected_num = connected_num - 1
                    print("client crashed/closed application")
                except OSError:
                    inputs.remove(s)  # remove from inputs
                    connected_num = connected_num - 1
                    print("client timed out")

    inform_if_quit(inputs[1:])


def main():
    global commands
    global ended_all
    global connected_num
    global quit_password

    quit_password = "69420"

    connected_num = 0

    # define the command dictionary - each command references the function that handles that command
    commands = {
        "EXIT": client_exit,
        "TIME": client_time
    }
    connection_socket = get_free_port_socket()  # create a socket for the client

    ended_all = False

    # scan for clients in 3 threads, to reduce chances of missing clients
    params = tuple([connection_socket])
    scan_thread_1 = Thread(target=scan_for_client, args=params, daemon=True)
    scan_thread_1.start()
    scan_thread_2 = Thread(target=scan_for_client, args=params, daemon=True)
    scan_thread_2.start()
    scan_thread_3 = Thread(target=scan_for_client, args=params, daemon=True)
    scan_thread_3.start()

    handle_all_clients(connection_socket)

    connection_socket.close()


if __name__ == "__main__":
    main()
