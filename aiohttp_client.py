import asyncio
import json
import os
import sys
import time

import aiohttp
import redis

from utils import make_request

REDIS_HOST = os.getenv('REDIS_HOST','localhost')
REDIS_PORT = os.getenv('REDIS_PORT',6379)
REDIS_DB = os.getenv('REDIS_DB',0)
REQUEST_QUEUE = os.getenv('REDIS_REQUEST_QUEUE','request')
RESPONSE_QUEUE = os.getenv('REDIS_RESPONSE_QUEUE','response')
ERROR_QUEUE = os.getenv('REDIS_ERROR_QUEUE','error')

CONNECTOR_LIMIT = int(os.getenv('AIOHTTP_CONNECTOR_LIMIT',100))
CONNECTOR_LIMIT_PER_HOST = int(os.getenv('AIOHTTP_CONNECTOR_LIMIT_PER_HOST',100))
RESTART = int(os.getenv('AIOHTTP_RESTART',600))
RESTART_AT = int(time.time())+RESTART

REDIS_CLIENT = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

async def worker(session):
    print('WORKER TEST1')
    try:
        while time.time()<RESTART_AT:
            s = REDIS_CLIENT.lpop(REQUEST_QUEUE)
            if s:
                data = json.loads(s.decode('utf-8'))
                print('data: %s' % data)
                print('worker test1')
                url = data['url']
                kwargs = {
                    'url':data['url'],
                    'method':data['method'],
                    'headers':data['headers'],
                    'data':data['data'],
                    'allow_redirects':data['allow_redirects'],
                    'disk_path':data['disk_path']
                }
                print('worker test2')
                task = make_request(session, **kwargs)
                result = await asyncio.gather(task,return_exceptions=True)
                print('result: %s' % result)
                timestamp = int(time.time())
                if isinstance(result,Exception):
                    e = result
                    q_element = json.dumps(dict(
                        url=url,
                        exc_type=type(e),
                        exc_message=str(e),
                        timestamp = timestamp
                    ))
                    REDIS_CLIENT.rpush(ERROR_QUEUE,q_element)
                else:
                    data['status'] = result
                    REDIS_CLIENT.rpush(RESPONSE_QUEUE,json.loads(data))
            else:
                await asyncio.sleep(0.1)
    except Exception as e:
        print('%s: %s' % (type(e),str(e)))

async def main(loop,workers_count):
    connector=aiohttp.TCPConnector(
        limit=CONNECTOR_LIMIT, # default 100
        limit_per_host=CONNECTOR_LIMIT_PER_HOST, # default 0
        ttl_dns_cache=300, # default 10
        enable_cleanup_closed=True
    )
    timeout = aiohttp.ClientTimeout(
        # total=60, # timeout for the whole request
        # connect=30, # timeout for acquiring a connection from pool
        sock_connect=10, # timeout for connecting to a peer for a new connection
        sock_read=10 # timeout for reading a portion of data from a peer
    )
    session_kwargs = dict(connector=connector,timeout=timeout)
    async with aiohttp.ClientSession(**session_kwargs) as session:
        task_list = []
        for i in range(1,workers_count+1):
            task_list.append(worker(session))
        await asyncio.gather(*task_list, return_exceptions=True)

if __name__=="__main__":
    if len(sys.argv)!=2:
        sys.exit('usage: %s workers_count' % sys.argv[0])

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(main(loop,int(sys.argv[-1])))
