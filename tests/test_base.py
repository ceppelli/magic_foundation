from unittest import TestCase

import asyncio
import concurrent
import logging
import sys
import traceback                     
import threading


from time import sleep
from magic_foundation import Container, Service, ServiceStatus, ServiceContext

log = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
logging.getLogger("magic_foundation").setLevel(logging.WARNING)


class Main:

    def __init__(self):
      self.loop = None
      self.service_pools:dict = {}

    def start(self):
        self.loop = asyncio.new_event_loop()
        self.threads = [Container(k, self.service_pools[k]) for k in self.service_pools]
        [t.start() for t in self.threads]

        def compare_all_status(status:ServiceStatus):
            for k in self.service_pools:
              for s in self.service_pools[k]:
                if status != s.status:
                  return False                  
            return True

        while not compare_all_status(status=ServiceStatus.running):
          sleep(0.5)

    def stop(self):
        [self.loop.run_until_complete(t.terminate()) for t in self.threads]
        self.loop.close()


class TestService(Service):

  def __init__(self, name:str):
      self.name = name
      self.q_inbound = asyncio.Queue()

  async def initialize(self, ctx:ServiceContext):
    log.info(f"[{self.name}] initialize")
    await asyncio.sleep(0)
    
  async def run(self, ctx:ServiceContext):
    log.info(f"[{self.name}] run")

    async def handler(data:map):
      self.q_inbound.put_nowait(data)
        
    self.handler = handler

    await ctx.subscribe(queue_name="q://test", handler=self.handler)

  async def terminate(self, ctx:ServiceContext):
    log.info(f"[{self.name}] terminate")

    await ctx.unsubscribe(queue_name="q://test", handler=self.handler)


class ProducerService(Service):

  def __init__(self, name:str, num_messages=0):
      self.name = name
      self.num_messages = num_messages

  async def initialize(self, ctx:ServiceContext):
    log.info(f"[{self.name}] initialize")    
    
  async def run(self, ctx:ServiceContext):
    log.info(f"[{self.name}] run")

    await asyncio.sleep(0.5)

    for i in range(self.num_messages):
      await ctx.publish(queue_name="q://test", data={"index": i})
      await asyncio.sleep(0)

  async def terminate(self, ctx:ServiceContext):
    log.info(f"[{self.name}] terminate")


class TestBase(TestCase):

    def test_service_lifecycle_single_runloop(self):
        log.info("\n")
        
        main = Main()
        
        service_1 = TestService(name="Service_1")
        service_2 = TestService(name="Service_2")
        
        main.service_pools = {
          'main': [
              service_1,
              service_2,
            ]
        }

        self.assertEqual(service_1.status, ServiceStatus.uninitialized)
        self.assertEqual(service_2.status, ServiceStatus.uninitialized)
  
        main.start()

        self.assertEqual(service_1.status, ServiceStatus.running)
        self.assertEqual(service_2.status, ServiceStatus.running)

        main.stop()

        self.assertEqual(service_1.status, ServiceStatus.terminated)
        self.assertEqual(service_2.status, ServiceStatus.terminated)

    def test_service_lifecycle_multi_runloop(self):
        log.info("\n")
        
        main = Main()

        service_1 = TestService(name="Service_1")
        service_2 = TestService(name="Service_2")
        
        main.service_pools = {
          'main': [
              service_1,            
          ],
          'second': [
              service_2,
          ]
        }

        self.assertEqual(service_1.status, ServiceStatus.uninitialized)
        self.assertEqual(service_2.status, ServiceStatus.uninitialized)
        
        main.start()

        self.assertEqual(service_1.status, ServiceStatus.running)
        self.assertEqual(service_2.status, ServiceStatus.running)

        main.stop()

        self.assertEqual(service_1.status, ServiceStatus.terminated)
        self.assertEqual(service_2.status, ServiceStatus.terminated)

    def test_message_single_runloop(self):
        log.info("\n")
        
        main = Main()

        consumer = TestService(name="Consumer")
        producer = ProducerService(name="Producer", num_messages=3)

        main.service_pools = {
          'main': [
              consumer,
              producer
          ]
        }

        self.assertEqual(consumer.q_inbound.qsize(), 0)

        main.start()

        sleep(1.0) 

        self.assertEqual(consumer.q_inbound.qsize(), 3)

        main.stop()

    def test_message_multi_runloop(self):
        log.info("\n")
        
        main = Main()

        consumer = TestService(name="Consumer")
        producer = ProducerService(name="Producer", num_messages=3)

        main.service_pools = {
          'main': [
              consumer,              
          ],
          'second': [
              producer,
          ]
        }

        self.assertEqual(consumer.q_inbound.qsize(), 0)

        main.start()

        sleep(1.0) 

        self.assertEqual(consumer.q_inbound.qsize(), 3)

        main.stop()
