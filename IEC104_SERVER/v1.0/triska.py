import asyncio
import socket

HOST = '127.0.0.1'
PORT = 1234
LISTENER_LIMIT = 5
active_clients = []

async def listen_for_messages(client, username):
    while True:
        try:
            message = await loop.sock_recv(client, 2048)
            if message:
                final_msg = f"{username}~{message.decode('utf-8')}"
                await send_messages_to_all(final_msg)
            else:
                print(f"The message from client {username} is empty")
                break
        except Exception as e:
            print(f"Error receiving message from client {username}: {e}")
            break

async def send_message_to_client(client, message):
    try:
        await loop.sock_sendall(client, message.encode())
    except Exception as e:
        print(f"Error sending message to client: {e}")

async def send_messages_to_all(message):
    for user in active_clients:
        await send_message_to_client(user[1], message)

async def client_handler(client):
    while True:
        try:
            username = await loop.sock_recv(client, 2048)
            if username:
                username = username.decode('utf-8')
                active_clients.append((username, client))
                prompt_message = f"SERVER~{username} added to the chat"
                await send_messages_to_all(prompt_message)
                await listen_for_messages(client, username)
                break
            else:
                print("Client username is empty")
                break
        except Exception as e:
            print(f"Error handling client: {e}")
            break

async def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    print(f"Running the server on {HOST} {PORT}")

    server.listen(LISTENER_LIMIT)

    while True:
        client, address = await loop.sock_accept(server)
        print(f"Successfully connected to client {address[0]} {address[1]}")
        await client_handler(client)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()