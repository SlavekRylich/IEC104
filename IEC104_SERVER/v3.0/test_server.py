import asyncio
import time

async def main():
    loop = asyncio.get_event_loop_policy().get_event_loop()
    
    server = await asyncio.start_server(
            handle_client, '127.0.0.1', 2404
            )
    async with server:
        print(f"Naslouchám na {'127.0.0.1'}:{2404}")
        await server.serve_forever()
        

async def handle_client(reader,writer):
    client_address, client_port = writer.get_extra_info('peername')
    
    try:
        while True:
            data = await reader.read(256)
            if not data:
                
                break
            
            print(f"{time.ctime()} - Přijat rámec: {data}")
            
            
    except Exception as e:
        print(f"Chyba při komunikaci s klientem {client_address}: {e}")
    
    

try:
    asyncio.run(main())

except KeyboardInterrupt:
    pass
finally:
    pass