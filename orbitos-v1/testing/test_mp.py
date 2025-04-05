import asyncio
import time
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from multiprocessing.managers import SharedMemoryManager

import numpy as np


class MotorControl:
    def __init__(self, pipe: Connection, sl: SharedMemoryManager.ShareableList):
        self.pipe = pipe
        self.rotating = False
        self.collected_data: list[int] = []
        self.sl = sl
        # here i would also initialize and connect to the motor

        asyncio.run(self.listen_for_commands())

    async def listen_for_commands(self):
        print("waiting for command...")
        while True:
            # Receive command from the main process
            command = self.pipe.recv()
            # Execute command
            if command == "execute_command":
                self.execute_command()
            elif command == "another_command":
                self.another_command()
            elif command == "do_rotation":
                await self.do_rotation()
            elif command == "exit":
                break
            else:
                print("Unknown command")

    def execute_command(self):
        print("executed command")

    def another_command(self):
        print("executed another command")

    async def rotate(self):
        print("rotating")
        self.rotating = True
        start = time.time()
        await asyncio.sleep(2)
        end = time.time()
        print(f"rotated for {end - start} seconds")
        self.rotating = False
        print("rotated")

    async def acquire_data(self):
        await asyncio.sleep(0.5)
        i = 0
        while self.rotating:
            i += 1
            self.collected_data.append(i)
            self.sl[i] = 0
            # self.collected_data.append(self.motor.get_actual_position())
            await asyncio.sleep(0.0001)

            if len(self.collected_data) % 10 == 0:
                print("sending data...", end="\r")
                self.pipe.send(self.collected_data)

        self.pipe.send(self.collected_data)

    async def do_rotation(self):
        await asyncio.gather(self.rotate(), self.acquire_data())


def init_class(class_pipe, sl):
    MotorControl(class_pipe, sl)


# this simulates a repetitive gui task that updates the plot
async def update_plot(my_pipe: Connection):
    times_to_poll_empty_pipe = 5
    times_polled = 0
    while True:
        print("updating plot")
        await asyncio.sleep(0.5)  # update plot every 0.5 seconds
        if my_pipe.poll():
            while my_pipe.poll():
                data = my_pipe.recv()
            times_polled = 0
            print(f"data: {data}")  # simulate updating plot
            print("length of data:", len(data))
        else:
            if times_polled < times_to_poll_empty_pipe:
                times_polled += 1
                print("polling empty pipe")
                await asyncio.sleep(0.1)
            else:
                break
        print("plot updated")


if __name__ in "__main__":

    with SharedMemoryManager() as smm:

        sl = smm.ShareableList(range(40000))

        my_pipe, class_pipe = Pipe()

        class_process = Process(target=init_class, args=(class_pipe, sl))
        class_process.start()

        time.sleep(2)  # waiting before sending command

        my_pipe.send("do_rotation")

        # print out the data from the pipe as long as new data is being sent
        asyncio.run(update_plot(my_pipe))

        # print(sl)

        time.sleep(10)
        print("sending exit command...")
        my_pipe.send("exit")
