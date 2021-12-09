# before running this program, find out the bluetooth address of your Wave ring by running discover_wave.py

import numpy as np
import ctypes
from pythonosc import dispatcher
from pythonosc import osc_server
from typing import List, Any
from pythonosc.udp_client import SimpleUDPClient
import pdb 

import argparse
import time
from typing import Union

from genki_wave.data.organization import ButtonEvent, DataPackage, Euler3d
from genki_wave.discover import run_discover_bluetooth
from genki_wave.threading_runner import ReaderThreadBluetooth, ReaderThreadSerial
from genki_wave.asyncio_runner import run_asyncio_bluetooth, run_asyncio_serial

ble_address = "" # <-- enter bluetooth address here


class Sleeper:
    """A simple class to sleep for an amount of time that makes sure each loop runs for `sleep_for_x_seconds` seconds"""

    def __init__(self, sleep_for_x_seconds: float):
        self._last_time = None
        self._sleep_for_x_seconds = sleep_for_x_seconds

    def sleep(self):
        curr_time = time.time()
        sleep_time = max(0.0, self._sleep_for_x_seconds - (self.last_time - curr_time))
        time.sleep(sleep_time)
        self._last_time = time.time()

    @property
    def last_time(self):
        if self._last_time is None:
            self._last_time = time.time()
        return self._last_time


# FEATURE SELECTION & OSC SETUP:
def euler_func(gyro_x, gyro_y, gyro_z, acc_x, acc_y, acc_z, mag_x, mag_y, mag_z, raw_pose_w, raw_pose_x, raw_pose_y, raw_pose_z, current_pose_w, current_pose_x, current_pose_y, current_pose_z, euler_roll, euler_pitch, euler_yaw, linacc_x, linacc_y, linacc_z, peak, peak_norm_velocity, timestamp_us, grav_x, grav_y, grav_z):

    genki_list = gyro_x, gyro_y, gyro_z, linacc_x, linacc_y, linacc_z # <-- features to send out through osc
    print(gyro_x, gyro_y, gyro_z, linacc_x, linacc_y, linacc_z) # <-- features to print to console
    client = SimpleUDPClient("127.0.0.1", 7000) # <-- osc IP address & port number. Choose 127.0.0.1 for localhost.
    client.send_message("/max/inputs", genki_list) # <-- osc argument followed by features listed in line 46
   

def main(reader_thread: Union[ReaderThreadBluetooth, ReaderThreadSerial], fetch_data_every_x_seconds: float):
    """A simple function to showcase reading from a thread.
    Fetches data every `fetch_data_every_x_seconds` and prints out all button presses in that timespan and the
    last value (usually a data package)
    """
    s = Sleeper(fetch_data_every_x_seconds)
    with reader_thread as wave:
        while True:
            val = wave.queue.pop_all()
            if val:
                for v in val:
                    if isinstance(v, DataPackage):
                        genki_data_dict = v.as_flat_dict()
                euler_func(**genki_data_dict)
            s.sleep()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-serial", action="store_true")
    parser.add_argument("--fetch-data-every-x-seconds", type=float, default=0.1) # <-- 'default' determines how often data is fetched
    args = parser.parse_args()

    if args.use_serial:
        main(ReaderThreadSerial.from_port(), args.fetch_data_every_x_seconds)
    else:
        print("Turn off using Ctrl + C (`KeyboardInterrupt`)")
        main(ReaderThreadBluetooth.from_address(ble_address), args.fetch_data_every_x_seconds)