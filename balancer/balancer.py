
import socket
import os
import sys
import argparse
from urllib.parse import urlparse
import datetime
import signal
import random

# Define a constant for our buffer size
BUFFER_SIZE = 1024

# initialize timeResponse list that stores the server and it's performance
timeResponse = []


# A function for creating HTTP GET messages.

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n'
    return request


# Python code to sort the tuples using second element
# of sublist Inplace way to sort using sort()

def Sort(timeResponse):
    # reverse = True (Sorts in Descending order)
    # key is set to sort using second element of
    # sublist lambda has been used
    timeResponse.sort(reverse=True, key=lambda x: x[1])
    return timeResponse


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):
    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line


# Read a file from the socket and print it out.  (For errors primarily.)

def print_file_from_socket(sock, bytes_to_read):
    bytes_read = 0
    while (bytes_read < bytes_to_read):
        chunk = sock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        print(chunk.decode())


# Read a file from the socket and save it out.

def save_file_from_socket(sock, bytes_to_read, file_name):
    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)


# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)


# Create an HTTP response

def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '301':
        message = message + value + ' Permanently Moved\r\n' + date_string + '\r\n'
    return message


# Send the given response and file back to the client.

def send_response_to_client(sock, code, file_name, server_request):
    # Determine content type of file

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif (file_name.endswith('.gif')):
        type = 'image/gif'
    elif (file_name.endswith('.png')):
        type = 'image/jpegpng'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    else:
        type = 'application/octet-stream'

    # Get size of file
    file_size = os.path.getsize(file_name)

    # Construct header and send it

    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(
        file_size) + '\r\nLocation: ' + server_request + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.
# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):
    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line


# randomly selects a server
# higher the server performance, higher the odds being selected
# implemented example from assignment outline
def balancer(numServers):
    # arithmetic series to calculate the sum of the number of servers
    sumServers = (numServers * (numServers + 1)) / 2
    temp = random.randint(1, sumServers)
    b = numServers
    tempSumServers = sumServers

    # loop through number of servers
    while (b >= 1):
        c = 0
        while (c < b):
            # checks if random int (temp) = current value of tempSumServers
            if temp == tempSumServers:
                # returns the server number
                return b
            else:
                # decrease c by 1
                c = c + 1
                # decrease tempSumServer by 1
                tempSumServers = tempSumServers - 1
        # decrease b by 1
        b = b - 1


def main():
    i = 1
    while (1):
        # initialize FLAG to 0
        FLAG = 0

        try:
            a = 0
            # save input arguments into server_list
            server_list = sys.argv

            # number of servers load_balancer is storing

            numServers = len(server_list) -1

            # while loop iterates through list of servers given by command line arguements
            while i < len(server_list):
                # reset flag value
                FLAG = 0
                # split argument into serverName and serverPort
                server = server_list[i].split(':')
                serverName = server[0]
                serverPort = int(server[1])
                print('Server Name: ', serverName)
                print('Server Port: ', serverPort)
                # this is the name the file the load balancer sends to test servers performance
                file_name = 'test.png'

                # trying to connect to server
                print('Connecting to server ...')
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((serverName, serverPort))
                except ConnectionRefusedError:
                    print('Error:  That host or port is not accepting connections. Removed from servers list.\n')
                    # remove inactive server from list
                    server_list.remove(server_list[i])
                    # update number of active servers
                    numServers = len(server_list) -1
                    # set flag to prevent load balancer from trying to use bad connections
                    FLAG = 1

                if (FLAG == 0):
                    # The connection was successful, so we can prep and send our message.
                    print('Connection to server established. Sending message...\n')
                    # start time to test server performance
                    startTime = float(datetime.datetime.now().timestamp())
                    message = prepare_get_message(serverName, serverPort, file_name)
                    client_socket.send(message.encode())

                    # Receive the response from the server and start taking a look at it

                    response_line = get_line_from_socket(client_socket)
                    response_list = response_line.split(' ')
                    headers_done = False

                    # If an error is returned from the server, we dump everything sent and
                    # exit right away.

                    if response_list[1] != '200':
                        print('Error:  An error response was received from the server.  Details:\n')
                        print(response_line);
                        bytes_to_read = 0
                        while (not headers_done):
                            header_line = get_line_from_socket(client_socket)
                            print(header_line)
                            header_list = header_line.split(' ')
                            if (header_line == ''):
                                headers_done = True
                            elif (header_list[0] == 'Content-Length:'):
                                bytes_to_read = int(header_list[1])
                        print_file_from_socket(client_socket, bytes_to_read)
                        sys.exit(1)

                    # If it's OK, we retrieve and write the file out.

                    else:

                        print('Success:  Server is sending file.  Downloading it now.\n\n')

                        # If requested file begins with a / we strip it off.

                        while (file_name[0] == '/'):
                            file_name = file_name[1:]

                        # Go through headers and find the size of the file, then save it.

                        bytes_to_read = 0
                        while (not headers_done):
                            header_line = get_line_from_socket(client_socket)
                            header_list = header_line.split(' ')
                            if (header_line == ''):
                                headers_done = True
                            elif (header_list[0] == 'Content-Length:'):
                                bytes_to_read = int(header_list[1])
                        save_file_from_socket(client_socket, bytes_to_read, file_name)
                        # calculate performance of server
                        endTime = float(datetime.datetime.now().timestamp()) - startTime
                        #print("time: ", endTime)
                        # store server performance in timeResponse
                        timeResponse.append([serverPort, endTime])
                        a = a + 1
                        # sort timeResponse by server performance
                        Sort(timeResponse)
                        #print(timeResponse)
                    i = i + 1

            if (FLAG == 0):
                # Register our signal handler for shutting down.

                signal.signal(signal.SIGINT, signal_handler)

                # Create the socket.  We will ask this to work on any interface and to pick
                # a free port at random.  We'll print this out for clients to use.
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(('', 0))
                print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
                server_socket.listen(1)

                # Keep the server running forever.

                while (1):
                    # connection times out after 5 minutes of inactivity to redo server performance testing
                    server_socket.settimeout(300)

                    print('Waiting for incoming client connection ...')
                    conn, addr = server_socket.accept()
                    print('Accepted connection from client address:', addr)
                    print('Connection to client established, waiting to receive message...')

                    # We obtain our request from the socket.  We look at the request and
                    # figure out what to do based on the contents of things.

                    request = get_line_from_socket(conn)
                    print('Received request:  ' + request)
                    request_list = request.split()

                    # This server doesn't care about headers, so we just clean them up.

                    while (get_line_from_socket(conn) != ''):
                        pass

                    # If we did not get a GET command respond with a 501.

                    if request_list[0] != 'GET':
                        print('Invalid type of request received ... responding with error!')
                        send_response_to_client(conn, '501', '501.html')

                    # If we did not get the proper HTTP version respond with a 505.

                    elif request_list[2] != 'HTTP/1.1':
                        print('Invalid HTTP version received ... responding with error!')
                        send_response_to_client(conn, '505', '505.html')


                    else:
                        # balancer algorithm chooses server
                        assign_server = balancer(numServers)
                        # stores selected server address
                        serverADR = server_list[assign_server]
                        # gets the filename requested by client
                        file_name = request_list[1]
                        # combines the serverADR and file_name
                        server_request = serverADR + file_name
                        # send response to client
                        print('Sending client server information...')
                        send_response_to_client(conn, '301', '301.html', server_request)

                    # We are all done with this client, so close the connection and
                    # Go back to get another one!

                    conn.close()



        # catches the socket.timeout() error
        except socket.timeout:
            # reset i to 1
            i = 1
            # empty timeResponse table to store the new test performance results
            timeResponse.clear()
            print('Re-doing server performance test...')


if __name__ == '__main__':
    main()
