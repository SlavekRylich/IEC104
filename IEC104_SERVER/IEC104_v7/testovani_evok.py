import asyncio
import time

import requests


async def aget_evok_request(host: str, dev_type: str, circuit: str):
    url = f"http://{host}/rest/{dev_type}/{circuit}"
    # resp = await asyncio.gather(asyncio.to_thread(requests.get(url), ))
    loop = asyncio.get_event_loop()
    future1 = loop.run_in_executor(None, requests.get, url)
    # return requests.get(url=url)
    resp = await future1
    return resp


def send_evok_request(host: str, dev_type: str, circuit: str, value):
    url = f"http://{host}/rest/{dev_type}/{circuit}"
    data = {'value': str(int(value))}
    return requests.post(url=url, data=data)
    # loop = asyncio.get_event_loop()
    # future1 = loop.run_in_executor(None, requests.post, url, data)
    # resp = await future1
    # return resp


def get_evok_request(host: str, dev_type: str, circuit: str):
    url = f"http://{host}/rest/{dev_type}/{circuit}"
    return requests.get(url=url)


async def main():
    dev_type = "do"
    circuit = "1_01"
    start = time.time()
    # for i in range(0,1):
    # ret = get_evok_request(host="192.168.1.166", dev_type=dev_type, circuit=circuit)

    ret = send_evok_request(host="192.168.1.166", dev_type=dev_type, circuit=circuit, value=0)
    # asyncio.sleep(1)
    # ret = get_evok_request(host="192.168.1.166", dev_type=dev_type, circuit=circuit)
    print(ret)
    print(time.time() - start)
    #
    print(ret.json())
    val = ret.json()['result']['value']
    print(val)
    # res = (20 * val) / 1077.9
    # print(res)
    print("--------------------------------")
    # print(res)
    # print(res.json())
    # print(res.json()['value'])


if __name__ == "__main__":
    asyncio.run(main())
