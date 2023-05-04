from scapy.all import *
from socket import *
from cryptography.fernet import Fernet
import subprocess
from threading import Thread
import os
from tkinter import *

CLIENT_ID_STRING = "636C69656E7420696E74726F64756365"
SERVER_ID_STRING = "736572766572207265616479"
BUFF = 1024

global ended
global sym_key
global message_num
global main_socket
global server_details
global conversation_num
global servers
global server_to_connected
global client_data
global always_broadcast
global last_message
global messages


def get_this_ip():
    """
    return the server computer ip
    """
    output = str(subprocess.check_output("ipconfig"))
    output = output.replace(". ", "").replace(" ", "").replace(r"\r", "").replace(r"\n", ":").split(":")
    ip = output[output.index("IPv4Address") + 1]
    return ip


def get_free_port():
    """
    quit()
    find available port to use for communication
    """

    ip = get_this_ip()

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((ip, 0))  # let the system find an open port
    available = s.getsockname()
    s.close()
    return available


def client_introduction(client_data):
    """
    introduce the client to the lan, hoping a server would catch the broadcast
    """

    introduce_socket = socket(AF_INET, SOCK_DGRAM)  # setup a UDP socket
    introduce_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  # make it so the socket can broadcast

    # this is the message that will be broadcast to the lan
    introduce_message = CLIENT_ID_STRING + " client_ip " + str(client_data[0]) + " client_port " + str(client_data[1])

    print(introduce_message)

    # broadcast to the lan
    introduce_socket.sendto(bytes(introduce_message, 'utf-8'), ('255.255.255.255', 0))

    introduce_socket.close()


def is_server_found(server, av_servers):
    found = False
    for s in av_servers:
        if s[0] == server[0] and s[1] == server[1]:
            found = True
    return found


def scan_for_server_reply():
    """
    scan for a server reply message, and return the server's port and ip
    """
    global client_data
    global server_to_connected

    av_servers = []

    receive_socket = socket(AF_INET, SOCK_DGRAM)
    receive_socket.bind(('', int(client_data[1])))
    start = time.time()
    while time.time() < start + 0.3:
        receive_socket.settimeout(0.1)
        try:
            content = receive_socket.recvfrom(BUFF)[0].decode('utf-8').split(" ")
            server_data = (content[content.index("server_ip") + 1].replace("'", ""),
                           int(content[content.index("server_port") + 1].replace("'", "")))
            connected = content[len(content) - 1]
            if not is_server_found(server_data, av_servers):
                av_servers.append(server_data)
            server_to_connected[server_data] = connected
        except:
            continue
    receive_socket.close()
    if av_servers:
        return tuple((av_servers[0], av_servers))
    else:
        return None, None


def client_setup():
    """
    setup the client
    """
    global client_data

    # broadcast the client's existence to the lan
    client_data = get_free_port()
    client_introduction(client_data)

    # connect main_socket to the server
    server_data, av_servers = scan_for_server_reply()

    return server_data, av_servers


def decode_message(message):
    """
    decode a message with the symmetric key
    """
    global sym_key
    return Fernet(sym_key).decrypt(message)


def encode_message(message):
    """
    encode a message with the symmetric key
    """
    global sym_key
    return Fernet(sym_key).encrypt(message)


def client_receive(client_app, message_history, history_label_text, available_servers):
    # server returns response
    global sym_key
    global ended
    global message_num
    global main_socket
    global server_details
    global servers

    while not ended:
        try:
            server_response = main_socket.recv(BUFF)
        except ConnectionAbortedError:
            print("ConnectionAbortedError")
            continue
        except ConnectionResetError:
            print("ConnectionResetError")
            message_history.delete(1, END)
            message_history.insert(1, "server was shut down")
            message_history.insert(2, "send any message to find a new server...")
            servers = client_setup()[1]
            ended = True
            return
        except OSError:
            print("Connection Closed")
            return

        if server_response:
            if server_response.decode('utf-8') == "FIN":
                message_history.delete(1, END)
                message_history.insert(1, "send any message to find a new server...")
                message_num = 2
                server_details = None
                ended = True
                servers = client_setup()[1]
            else:
                message_history.insert(message_num, decode_message(server_response).decode('utf-8'))
                message_num = message_num + 1
        else:
            message_history.insert(message_num, "server failed to respond due to unknown error")
            message_num = message_num + 1


def search_for_server():
    """
    attempt client setup for 1 second or until a server is found
    """
    global servers
    global server_details

    new_server_details, new_servers = client_setup()  # restart the client setup process
    start_time = time.time()
    while not new_server_details and time.time() < start_time + 0.5:
        new_server_details, new_servers = client_setup()  # restart the client setup process

    server_details, servers = new_server_details, new_servers  # update available servers


def reset_details(available_servers, history_label_text):
    """
    reset network details such as:
    - available servers
    - Conversation status
    """
    global conversation_num
    global message_num
    global servers
    global server_details

    # reset available servers listbox
    available_servers.delete(0, END)
    new_count = 0
    # reset list of available servers
    if servers:
        for new_server in servers:
            new_connected_arrow = ""

            if server_details:
                if new_server[0] == server_details[0] and new_server[1] == server_details[1]:
                    new_connected_arrow = " <-"  # indicates that this is the server the client is connected to

            available_servers.insert(new_count, "Server [" + new_server[0] + ", " + str(
                new_server[1]) + "] is available for communication " + "(" + str(server_to_connected[new_server]) + " Connected)" + new_connected_arrow)
            new_count = new_count + 1
    else:
        available_servers.insert(0, "No available servers in your area")
    # reset the conversation headline (history label)
    if server_details:
        history_label_text.set(
            "Conversation with server [" + server_details[0] + ", " + str(server_details[1]) + "]")
    else:
        history_label_text.set("Not Connected to a Server")


def keep_updated(available_servers, history_label_text):
    """
    update client network status every 10 seconds
    """
    global servers

    while True:
        servers = client_setup()[1]
        reset_details(available_servers, history_label_text)
        time.sleep(5.0)


def client_window(server_password):
    client_app = Tk()
    client_app.geometry("960x540")
    client_app['background'] = '#202125'
    global ended
    global message_num
    global main_socket
    global server_details
    global conversation_num
    global sym_key
    global servers
    global server_to_connected
    global client_data
    global always_broadcast
    global last_message
    global messages

    always_broadcast = False

    message_num = 2
    conversation_num = 1  # how many conversations did the client have?

    messages = []
    last_message = 0

    # define message history listbox and label

    # label
    history_label_text = StringVar()
    history_label = Label(client_app, textvariable=history_label_text, bg='#202125', fg='#FFFFFF')
    if server_details:
        history_label_text.set("Conversation with server [" + server_details[0] + ", " + str(server_details[1]) + "]")
    else:
        history_label_text.set("Not Connected to a Server")
    history_label.grid(row=0, column=0, columnspan=2)

    # listbox
    message_history = Listbox(client_app, height=25, width=96, fg="#FFFFFF")
    message_history.insert(0, "Conversation Number [" + str(conversation_num) + "] With a Server")
    if server_password:
        message_history.insert(1, "Server Admin Password is " + server_password)
    message_history.grid(row=1, column=0, columnspan=2)
    message_history['background'] = '#1C1C21'

    def find_new_conversation():
        """
        in case the conversation with the original server ended, try to find new server to communicate with
        """
        global message_num
        global conversation_num
        global sym_key
        global ended
        global servers
        global server_details

        search_for_server()

        if not server_details:
            message_history.delete(1, END)
            message_history.insert(1, "could not find a server, please try again later")
            message_num = 1
            reset_details(available_servers, history_label_text)
            return None

        new_main_socket = socket(AF_INET, SOCK_STREAM)
        new_main_socket.connect(server_details)

        ended = False  # new conversation started

        data = (new_main_socket.recv(BUFF).decode('utf-8')).split(" ")

        sym_key, server_password = data[0].encode('utf-8'), data[1]  # receive new key and password

        conversation_num = conversation_num + 1  # update conversation num

        message_history.delete(0, END)  # restart message history
        message_num = 2  # reset message num

        message_history.insert(0, "Conversation Number [" + str(
            conversation_num) + "] With a Server")  # update conversation num in display

        message_history.insert(1, "Server Admin Password is " + server_password)

        server_to_connected[server_details] = str(int(server_to_connected[server_details]) + 1)

        reset_details(available_servers, history_label_text)

        return new_main_socket

    def get_client_message():
        """
        get user input message
        """
        user_message = str(type_message.get())
        return user_message

    def client_send(event):
        """
        handle client pressing enter button
        """
        global message_num
        global main_socket
        global server_details
        global ended
        global client_data
        global always_broadcast
        global last_message

        user_message = get_client_message()  # get message from entry box

        user_message = user_message.strip()

        if not user_message:
            return

        if messages:
            if messages[max(len(messages) - 1, 0)] != user_message:
                messages.append(user_message)
        else:
            messages.append(user_message)

        last_message = len(messages)

        if always_broadcast:
            user_message = "broadcast " + user_message

        if user_message == "clear":
            clear_history()
            return

        if ended:  # if conversation ended with server, start a new conversation (with previous or other server)
            if main_socket:
                main_socket.close()
            main_socket = find_new_conversation()

            if not main_socket:
                return

            # restart the receive thread
            new_client_receive_thread = Thread(target=client_receive, args=(client_app, message_history, history_label_text, available_servers))
            new_client_receive_thread.start()
            ended = False

        send_message = user_message

        if user_message.split(" ")[0] == "broadcast":
            send_message = "broadcast " + "Client [" + str(client_data[0]) + "]: " + " ".join(user_message.split(" ")[1:])
        send_message = encode_message(send_message.encode('utf-8'))
        main_socket.send(send_message)

        if user_message.split(" ")[0] == "broadcast":
            user_message = "You: " + " ".join(user_message.split(" ")[1:])
        else:
            user_message = "You: " + user_message

        message_history.insert(message_num, user_message)  # insert message to listbox
        message_num = message_num + 1

        type_message.delete(0, END)

    def refresh_available_servers():
        global servers
        av_servers = client_setup()[1]
        servers = av_servers

        reset_details(available_servers, history_label_text)

    def clear_history():
        message_history.delete(1, END)
        type_message.delete(0, END)

    def get_last_message(event):
        global last_message
        global messages

        if event.keysym == "Up" and last_message > 0:
            type_message.delete(0, END)
            last_message = last_message - 1
            type_message.insert(0, messages[last_message])
        elif event.keysym == "Down" and last_message < len(messages) - 1:
            type_message.delete(0, END)
            last_message = last_message + 1
            type_message.insert(0, messages[last_message])
        elif event.keysym == "Down" and last_message == len(messages) - 1:
            type_message.delete(0, END)
            last_message = last_message + 1

    def broadcast_mode():
        """
        switch to or out of broadcast mode
        in broadcast mode, all client messages are broadcast, regardless of whether they used the command
        """
        global always_broadcast
        if broadcast_mode_text.get() == "Broadcast Mode":
            broadcast_mode_text.set("Exit Broadcast")
            always_broadcast = True
        else:
            broadcast_mode_text.set("Broadcast Mode")
            always_broadcast = False

    def switch_server():
        """
        cut connection with current server
        switch to the server the client selected in the available server list
        update conversation details accordingly
        """
        global main_socket
        global server_details
        global sym_key
        global ended
        global conversation_num
        global message_num
        global server_to_connected
        global servers

        if not servers:
            return

        index = available_servers.curselection()  # get selected server
        if not index:  # if none was selected, return
            return
        wanted_server = servers[index[0]]  # get selected server details
        new_main_socket = socket(AF_INET, SOCK_STREAM)
        try:
            new_main_socket.connect(wanted_server)  # connect to server
        except:  # if unable to connect, remove server from available servers
            available_servers.delete(index[0], index[0])
            return

        ended = True  # ended previous conversation

        if main_socket:
            main_socket.close()  # close previous connection

        main_socket = new_main_socket  # update main socket

        data = (new_main_socket.recv(BUFF).decode('utf-8')).split(" ")

        sym_key, server_password = data[0].encode('utf-8'), data[1]  # receive new key and password

        server_details = wanted_server  # update server details

        conversation_num = conversation_num + 1  # update conversation num

        message_history.delete(0, END)  # restart message history
        message_num = 2  # reset message num

        message_history.insert(0, "Conversation Number [" + str(
            conversation_num) + "] With a Server")  # update conversation num in display

        message_history.insert(1, "Server Admin Password is " + server_password)

        ended = False  # new conversation started

        # restart the receive thread
        new_client_receive_thread = Thread(target=client_receive, args=(client_app, message_history, history_label_text, available_servers))
        new_client_receive_thread.start()

    # define type_message entry box
    type_message = Entry(client_app, width=80)
    type_message.grid(row=2, column=0)
    type_message.get()
    type_message.bind('<Return>', client_send)
    type_message.bind('<Key>', get_last_message)

    commands_text = StringVar()

    commands_label = Label(client_app, fg="#FFFFFF", bg='#1C1C21', width=62, height=28, textvariable=commands_text, font=('Helvetica', 8))
    commands_label.grid(row=1, column=2, columnspan=2)

    commands_text.set("""
    USER GUIDE\n\n\n
    TIME: server returns the current time\n
    EXIT: shuts down client connection\n
    QUIT (followed by a password): shuts down server and client connection\n
    clear: clears message history\n
    Use UP and DOWN arrows for navigating message history\n
    'broadcast' followed by any message will send\n
    the message to all clients connected to the server\n
    ANY OTHER MESSAGE WILL BE RESPONDED TO WITH AN ECHO\n
    You will be disconnected after 2 minutes of no communication
    """)

    # define available servers listbox
    available_servers = Listbox(client_app, width=96, height=5, fg="#FFFFFF")
    available_servers['background'] = '#1C1C21'
    available_servers.grid(row=3, column=0, columnspan=2)

    if servers:
        count = 0
        for server in servers:
            connected_arrow = ""
            if server is server_details:
                connected_arrow = " <-"  # indicates that this is the server the client is connected to
                server_to_connected[server] = str(int(server_to_connected[server]) + 1)  # add the client to the connected_num
            available_servers.insert(count, "Server [" + server[0] + ", " + str(server[1]) + "] is available for communication " + "(" + str(server_to_connected[server]) + " Connected)" + connected_arrow)
            count = count + 1
    else:
        available_servers.insert(0, "No available servers in your area")

    # make it so user cant resize window
    client_app.resizable(False, False)

    # switch server button calls switch_server
    switch_server_button = Button(text="Switch To Selected Server", command=switch_server, fg="#FFFFFF", bg="#1C1C21")
    switch_server_button.grid(row=2, column=2, rowspan=2)

    # refresh available servers button calls refresh_available_servers
    refresh_available_servers_button = Button(text="Refresh Available Servers", command=refresh_available_servers, fg="#FFFFFF", bg="#1C1C21")
    refresh_available_servers_button.grid(row=2, column=3, rowspan=2)

    # refresh available servers button calls refresh_available_servers
    broadcast_mode_text = StringVar()
    broadcast_mode_button = Button(textvariable=broadcast_mode_text, command=broadcast_mode,
                                              fg="#FFFFFF", bg="#202125", width=12, padx=3)
    broadcast_mode_text.set("Broadcast Mode")
    broadcast_mode_button.grid(row=2, column=1)

    # start a separate thread to display server's responses to client messages
    client_receive_thread = Thread(target=client_receive, args=(client_app, message_history, history_label_text, available_servers), daemon=True)
    client_receive_thread.start()

    # start a separate thread to always keep the
    keep_updated_thread = Thread(target=keep_updated, args=(available_servers, history_label_text), daemon=True)
    keep_updated_thread.start()

    client_app.mainloop()


def main_communication():
    """
    start communicating
    """

    global sym_key
    global ended
    global main_socket
    ended = False if server_details else True

    server_password = None

    if server_details:
        # this is the symmetric key used for encrypting the communication
        try:
            data = (main_socket.recv(BUFF).decode('utf-8')).split(" ")
            sym_key, server_password = data[0].encode('utf-8'), data[1]
        except:
            sym_key, server_password = None, None

    client_window(server_password)


def main():
    # set up the main communication socket
    global main_socket
    global server_details
    global servers
    global server_to_connected

    server_to_connected = {  # dictionary that holds for every server the amount of clients that are connected to the server

    }

    main_socket = socket(AF_INET, SOCK_STREAM)

    search_for_server()

    print(server_details)
    if server_details:
        main_socket.connect(server_details)

    # initiate communication with server
    main_communication()

    if main_socket:
        # finally, end communication
        main_socket.close()

    os._exit(0)


if __name__ == "__main__":
    main()
