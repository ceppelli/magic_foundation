## magic_foundation

[![Build Status](https://travis-ci.com/ceppelli/magic_foundation.svg?branch=master)](https://travis-ci.com/ceppelli/magic_foundation)
[![codecov](https://codecov.io/gh/ceppelli/magic_foundation/branch/master/graph/badge.svg)](https://codecov.io/gh/ceppelli/magic_foundation)
[![pypi](https://badge.fury.io/py/magic-foundation.svg)](https://pypi.org/project/magic_foundation/)


Minimalistic library that simplifies the adoption of **async/await** (asyncio) programming style in a multithreaded application.


Define 2 services and run in the same runloop (single thread)

```python
import logging

from magic_foundation import Service, ServiceStatus, ServiceContext, Main


class TestService(Service):

  def __init__(self, name:str):
      self.name = name

  async def initialize(self, ctx:ServiceContext):
    log.info(f"[{self.name}] initialize")
    
  async def run(self, ctx:ServiceContext):
    index = 0

    while self.status is ServiceStatus.running:
      log.info(f"[{self.name}] run {index}")
      index += 1
      await asyncio.sleep(1.0)

  async def terminate(self, ctx:ServiceContext):
    log.info(f"[{self.name}] terminate")


if __name__ == "__main__":
  log = logging.getLogger(__name__)
  logging.basicConfig(level=logging.INFO)
  logging.getLogger("magic_foundation").setLevel(logging.DEBUG)

  main = Main.instance()
  main.service_pools = {
    'main': [
      TestService(name="Service_1"),
      TestService(name="Service_2")
    ],
  }
  main.run()

```

If you want running the 2 services in different threads just define the service_pools as following:

```python

  ...
  main = Main.instance()
  main.service_pools = {
    'th1': [
      TestService(name="Service_1")
    ],
    'th2': [
      TestService(name="Service_2")
    ],
  }
  main.run()

```


## Communication

The communication between Services mimics the **publish/subscribe paradigm**

**Subscribe**

```python

  async def coro(data):
    log.info(f"[{self.name}] coro data:{data}")

  await ctx.subscribe(queue_name="q://my_queue", handler=coro)

```


**Pubblish**


```python

  data = {
    "a": "A",
    "b": 1234 
  }
  
  await ctx.publish(queue_name="q://my_queue", data=data) 

```

It is possible to subscribe to the same queue from different services and each service will receive the message


