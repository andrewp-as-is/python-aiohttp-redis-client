import io
import json
import os
import time

import aiohttp

CHUNK_SIZE = 8 * 1024  # 8 KB

def filesizeformat(size):

    def filesize_number_format(value):
        return formats.number_format(round(value, 1), 1)

    KB = 1 << 10
    MB = 1 << 20
    GB = 1 << 30
    TB = 1 << 40
    PB = 1 << 50

    negative = size < 0
    if negative:
        size = -size  # Allow formatting of negative numbers.

    if size < KB:
        value = size
    elif size < MB:
        value = gettext("%s KB") % filesize_number_format(size / KB)
    elif size < GB:
        value = gettext("%s MB") % filesize_number_format(size / MB)
    elif size < TB:
        value = gettext("%s GB") % filesize_number_format(size / GB)
    elif size < PB:
        value = gettext("%s TB") % filesize_number_format(size / TB)
    else:
        value = gettext("%s PB") % filesize_number_format(size / PB)

    if negative:
        value = "-%s" % value
    return value

async def write_content(path,response):
    f = io.BytesIO()
    if os.path.exists(str(path)):
        os.unlink(path)
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
            with open(path, "wb") as fd:
                fd.write(f.getbuffer())
            touch(os.path.dirname(path))
    finally:
        f.close()

def write_headers(path,response):
    text = "\n".join(map(
        lambda i:'%s: %s' % (i[0],i[1]),
        response.headers.items()
    ))
    # print('WRITE HEADERS %s -> %s (%s)' % (response.url,path,len(text)))
    open(path,'w').write(text)

async def make_request(session,**kwargs):
    started_at = time.monotonic()
    request_kwargs = {
        'method':kwargs['method'],
        'url':kwargs['url'],
        'headers':kwargs['headers'],
        'allow_redirects':kwargs['allow_redirects']
    }
    if kwargs['data']:
        request_kwargs.update(data=kwargs['data'])
    content_path = os.path.join(kwargs['disk_path'],'content')
    headers_path = os.path.join(kwargs['disk_path'],'headers')
    print('%s %s' % (kwargs['method'].upper(),kwargs['url']))
    async with session.request(**request_kwargs) as response:
        duration = round(time.monotonic() - started_at,3)
        print('%s status %s, %ss' % (kwargs['url'],response.status,duration))
        if response.status in [429]:
            print("RETRY-AFTER: %s" % url)
        else:
            if not os.path.exists(disk_path):
                os.makedirs(disk_path)
            write_headers(headers_path,response)
            if method!='HEAD' and response.status not in [404]:
                await write_content(content_path,response)
        return response.status
