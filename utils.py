import io
import json
import os
import time

import aiohttp

CHUNK_SIZE = 8 * 1024  # 8 KB

def filesizeformat(size):

    #def filesize_number_format(value):
    #    return formats.number_format(round(value, 1), 1)

    KB = 1 << 10
    MB = 1 << 20

    if size < KB:
        value = size
    elif size < MB:
        value = "%s KB" % (size / KB)
    elif size < GB:
        value = "%s MB" % (size / MB)
    return value

async def write_content(path,response):
    f = io.BytesIO()
    try:
        while True: # known-issue: empty response
            chunk = await response.content.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)
        nbytes = f.getbuffer().nbytes
        size = filesizeformat(f.getbuffer().nbytes)
        print('WRITE CONTENT %s -> %s (%s)' % (response.url,path,size))
        if nbytes:
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(str(path), "wb") as fd:
                fd.write(f.getbuffer())
        else:
            if os.path.exists(path):
                os.unlink(path)
    finally:
        f.close()

async def make_request(session,data):
    started_at = time.monotonic()
    kwargs = {
        'method':data['method'],
        'url':data['url'],
        'headers':data['headers'],
        'allow_redirects':data.get('allow_redirects',True)
    }
    if data.get('data',''):
        request_kwargs.update(data=data['data'])
    print('%s %s' % (data['method'].upper(),data['url']))
    async with session.request(**kwargs) as response:
        duration = round(time.monotonic() - started_at,3)
        print('%s status %s, %ss' % (data['url'],response.status,duration))
        if data['method'].upper()!='HEAD' and response.status not in [404,429]:
            await write_content(data['disk_path'],response)
        return response
