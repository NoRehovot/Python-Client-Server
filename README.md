# Readme for Client-Server Applications
  This app allows clients to connect to nearby servers in their Local Area Network, and server operators to set up their own servers in the LAN.

# Features

  - Using the client_side.py application, users can find a server and communicate with it using TCP/IP. 
  - Clients automatically connect to a server in their LAN when opening the application (if there is a running server).
  - Clients can communicate with the server in a message-echo format (client sends ‘hello’, server responds with ‘hello’).
  - Clients can communicate with all other clients connected to their server via the ‘broadcast’ command or broadcast mode.
  - Clients can view all the available servers in their LAN, and the number of clients connected to each server.
  - Clients can choose to switch between servers in their LAN with a simple click of a button.
  - The application includes comfortable GUI and design to help the client interact with servers and other clients easily.
  - CLIENTS WILL BE DISCONNECTED AFTER TWO MINUTES OF NO COMMUNICATION.
 
# Usage

  - Set up a server by running server_side.py.
  - Run client_side.py to open the client application.
  ### Using the client app:

  ![image](https://github.com/NoRehovot/client-server/blob/main/example.png)

  - On the top left side, see which server you are currently connected to.
  - Under the server’s name, you can see the chat. This will fill with the messages the user sends.
  - Underneath is the message box. Use this to communicate with the server and receive an echo response (or send a command).
  - To the right of the message box is the Broadcast Mode button. Use this button to communicate with the clients that are connected to the server in a group chat format. After clicking on the button, any message you send will be sent to the other clients, and the button will switch to ‘Exit Broadcast’
  - Beneath the message box is the available servers list, which shows the client all the running servers in the LAN. In parentheses is the number of clients that are connected to the available server. the arrow indicates the server that the user is connected to. This list updates in real-time every 5 seconds.
  - To the right is the user guide. This explains every command and practical feature the client can use.
  - Under the user guide is the ‘Switch To Selected Server’ and ‘Refresh Available Servers’ buttons. Click on a server from the available server list and then on the ‘Switch To Selected Server’ button to end communication with current server and switch to the selected one. Use ‘Refresh Available Servers’ to manually update the available servers list. 
  - Use enter button to send a message.
  - Use up and down arrows to navigate message history.


# Client-Server Commands

    TIME: server returns the current time of day
    EXIT: end communication with the current server. Connect to a new server by either manually using the ‘Switch To Selected Server’ button, or sending any message (the application will recognize you are not connected to a server and automatically find a server to send this message to).
    QUIT: end communication with the server and shut down the server itself. QUIT needs to be followed by a password the server sends in the beginning of the conversation (for example ‘QUIT 12345’).
    clear: clears the chat history.
    broadcast (followed by any message): sends the message to all other clients that are connected to the server (use this or the broadcast mode button for the same effect). 

# How does the client find a server?
    Client sends broadcast message to the LAN with a signature, and the client IP and port.
    Server spots the client’s signature and replies with the server IP and port.
    Client connects to the server using a TCP socket and starts communicating.

### Enjoy the app!
