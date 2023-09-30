### Environment variables

Variable|default
-|-
`REDIS_HOST`|`localhost`
`REDIS_PORT`|`6379`
`REDIS_DB`|`0`
`REQUEST_QUEUE`|`request`
`RESPONSE_QUEUE`|`response`
`ERROR_QUEUE`|`error`


### Redis
```python
import redis

REDIS_CLIENT = redis.Redis(host='localhost', port=6379, db=0)
```

### Request

push to redis queue
```python
REQUEST_QUEUE ='request'

values = []
for request in request_list:
    request_data = json.dumps(request.data) if request.data else None
    data = dict(
        url=request.url,
        method=request.method,
        headers=request.headers,
        data=request.data,
        allow_redirects=request.allow_redirects,
        disk_path=get_disk_path(request.disk_relpath),
        priority=request.priority,
    )
    values+=[json.dumps(data)]
REDIS_CLIENT.rpush(REQUEST_QUEUE,*values)
```

### Response

pull from redis queue
```python
RESPONSE_QUEUE ='response'

q_element_list = REDIS_CLIENT.lrange(RESPONSE_QUEUE,0,-1)
for q_element in q_element_list:
    data = json.loads(q_element.encode('utf-8'))
```

### Error

pull from redis queue
```python
ERROR_QUEUE ='error'

q_element_list = REDIS_CLIENT.lrange(ERROR_QUEUE,0,-1)
for q_element in q_element_list:
    data = json.loads(q_element.encode('utf-8'))
```

### Docker

`entrypoint.sh`
```bash
python3 aiohttp_client.py 100 # 100 workers
```
