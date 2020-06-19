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
      self.__module__loop = None
      self.service_pools:dict = {}

    def start(self):
        self.loop = asyncio.get_event_loop()
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

  async def initialize(self, ctx:ServiceContext):
    log.info(f"[{self.name}] initialize")
    await asyncio.sleep(0.5)
    
  async def run(self, ctx:ServiceContext):
    log.info(f"[{self.name}] run")

  async def terminate(self, ctx:ServiceContext):
    log.info(f"[{self.name}] terminate")


class TestBase(TestCase):

    def test_service_lifecycle_single_runloop(self):
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

      print(type(main.service_pools))

      self.assertEqual(service_1.status, ServiceStatus.uninitialized)
      self.assertEqual(service_2.status, ServiceStatus.uninitialized)
      
      main.start()

      self.assertEqual(service_1.status, ServiceStatus.running)
      self.assertEqual(service_2.status, ServiceStatus.running)

      main.stop()

      self.assertEqual(service_1.status, ServiceStatus.terminated)
      self.assertEqual(service_2.status, ServiceStatus.terminated)
