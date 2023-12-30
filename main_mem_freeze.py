from collections import defaultdict
from datetime import datetime

import requests
import re
import urllib.request
import json
import time
import csv
import paramiko
import sys
import threading
from multiprocessing import Event, Process
from multiprocessing.pool import ThreadPool
import subprocess
import os
import signal
from functional_methods import *
from collect_data import *
from variables import *




# INSTANCE = ""
# TARGET_VIDEO = ""
# DETECTION_IMAGE = ""
# CALCULATING_HOSTNAME = SERVER_USER
# CALCULATING_INSTANCE = SERVER_IP
# POD_EXISTED = 0
# CALCULATION_TYPE = ""

# finished = False
timestamps = {}
# terminate_state = defaultdict(list)


def collect_life_cycle(target_pods: int, repetition: int):
    #NOTE: Null process 
    timestamps["warm_state_start"]=time.time()
    collect_state(target_pods, repetition, WARM_MEM_STATE)
    timestamps["warm_state_end"]=time.time()
    
   
    print("Measurement finished.")
    print("Saving timestamps..")
    timestamps_to_file(timestamps, target_pods, repetition)
    # event.set()
    print("Finished!")

if __name__ == "__main__":
    
    target_pods_scale = sys.argv[1] # number of scaling pod
    repeat_time = sys.argv[2]
    INSTANCE = sys.argv[3] # jetson
    # this P0 process runs infintely, detect and manual terminate "terminating" pods 
    # event = Event() # the event is unset when created
    # p0 = Process(target=auto_delete, args=(event, ))
    # p0.start()
    collect_life_cycle(int(target_pods_scale), int(repeat_time))
    # p1 = Process(target=collect_life_cycle, args=(event, int(target_pods_scale), repeat_time, ), daemon = True)
    # print("Start calculate job on {}".format(INSTANCE))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
    # p1.start()
    # p0.join()
    # p1.join()    

