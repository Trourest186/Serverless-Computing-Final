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
import shutil


# def collect_life_cycle_mem(host: str, image: str, target_pods: int, repetition: int, event):  # Freeze MEM only
#     timestamps = {}
#     sleep(10)
#     timestamps["null_state_start"] = time.time()
#     collect_state(host, image, target_pods, repetition, NULL_STATE)
#     timestamps["null_state_end"] = time.time()
#     print("Proxy image is going to be deleted ...")
#     remote_worker_call(DELETE_PROXY_IMAGE_CMD)
#     print("Default gateway will be removed ...")
#     remote_worker_call(DELETE_GW)
#     sleep(5)
#     remote_worker_call(DELETE_GW)  # a bug may cause the before cmd not working
#     sleep(10)
#     config_deploy("deploy")
#     print("Waiting for 40s before turning on network ...")
#     sleep(40)
#     remote_worker_call(ADD_GW)
#     sleep(5)
#     remote_worker_call(ADD_GW)  # a bug may cause the before cmd not working
#     while not k8s_API.is_all_con_ready():
#         print("Waiting for all containers ready...")
#         sleep(10)
#     print("2/2 containers are ready, start measuring ...")
#     sleep(10)  # to stablize the system
#     timestamps["warm_mem_state_start"] = time.time()
#     collect_state(host, image, target_pods, repetition, WARM_MEM_STATE)
#     timestamps["warm_mem_state_end"] = time.time()
#     sleep(10)
#     timestamps["warm_mem_to_warm_disk_start"] = time.time()
#     config_deploy("delete")
#     collect_warm_CPU_to_warm_disk_process(host, image, target_pods, repetition, WARM_MEM_TO_WARM_DISK_PROCESS)
#     timestamps["warm_mem_to_warm_disk_end"] = time.time()
#     timestamps_to_file(host, image, timestamps, target_pods, repetition)
#     sleep(20)
#     event.set()
#     print("Measurement finished.")
#     print("Saving timestamps..")
#     print("Finished!")

############################################################################
############################################################################

def collect_cold_warm_disk(host: str, image: str, target_pods: int, repetition: int, event):  # Normal lifecycle
    timestamps = {}
    # k8s_API.config_image(WRONG_IMAGE_NAME)
    # k8s_API.update_deployment(target_pods, "null", "mec", DEFAULT_DIRECTORY + "/template1.yaml")
    # remote_worker_call(DELETE_IMAGE_CMD, JETSON_USERNAME, JETSON_IP, JETSON_PASSWORD)
    remote_worker_call(DELETE_IMAGE_CMD, MEC_USERNAME, MEC_IP, MEC_PASSWORD)
    sleep(10)
    k8s_API.config_image(IMAGE_NAME)
    k8s_API.config_live_time(100)
    config_deploy("deploy")
    timestamps["cold_to_warm_disk_start"] = time.time()
    collect_null_to_warm_disk_process(host, image, target_pods, repetition, COLD_TO_WARM_DISK_PROCESS)
    timestamps["cold_to_warm_disk_end"] = time.time()
    timestamps_to_file(host, image, timestamps, target_pods, repetition)
    config_deploy("delete")
    # sleep(5)
    while (k8s_API.get_number_pod(NAMESPACE) != 0):
        print("Waiting for pod to be terminated")
        sleep(5)

    # while (k8s_API.get_number_pod(NAMESPACE) != 0):
    #     print("Waiting for pod to be terminated")
    #     command = "kubectl delete pod --all -n serverless --force --grace-period 0"
    #     output, error = execute_kubectl_command(command)
    #     sleep(5)
    print("There is no pod in the system.")
    sleep(10)
    event.set()
    print("Measurement finished.")
    print("Saving timestamps..")
    print("Finished!")
    
############################################################################
############################################################################

def collect_life_cycle(host: str, image: str, target_pods: int, repetition: int, event):  # Normal lifecycle

    timestamps = {}
    # NOTE: Null process
    timestamps["null_state_start"] = time.time()
    collect_state(host, image, target_pods, repetition, NULL_STATE)
    timestamps["null_state_end"] = time.time()

   # NOTE: Warm disk process: here we'll apply deployment and wait until pod is deleted
   # UPDATE: Now NUll --> Cold --> warm disk
   # To measure the Null --> Cold process we do the following
   # Turn off network by remote call (or the entire process of turning on/off network can be
   # replace by typing a non-existed image, then we fix file deployment later)
   # Deploy file and start measuring
   # Detect Pulling/DNS existance then stop measuring
   # Turn on network by remote call
   # Continue other jobs as below
    k8s_API.config_image(IMAGE_NAME+"wrong!!")
    timestamps["null_to_cold_process_start"] = time.time()
    config_deploy("deploy")
    collect_null_to_cold_process(
        host, image, target_pods, repetition, NULL_TO_COLD_PROCESS)
    timestamps["null_to_cold_process_end"] = time.time()
    sleep(5)

    # NOTE: Cold state for 30 seconds
    sleep(10)
    timestamps["cold_state_start"] = time.time()
    collect_state(host, image, target_pods, repetition, COLD_STATE)
    timestamps["cold_state_end"] = time.time()

    # NOTE: Cold to null
    timestamps["cold_to_null_process_start"] = time.time()
    config_deploy("delete")
    # print("New deployment has been created.")
    collect_cold_to_null_process(
        host, image, target_pods, repetition, COLD_TO_NULL_PROCESS)
    timestamps["cold_to_null_process_end"] = time.time()
    print("Pod number is: {}, Waiting for pod to be terminated".format(
            k8s_API.get_number_pod(NAMESPACE)))
    while (k8s_API.get_number_pod(NAMESPACE) != 0):
        sleep(10)
    print("There is no pod in the syste'm")
    # NOTE: Warm disk state
    k8s_API.config_image(IMAGE_NAME)
    # change live-time to minimum value = 20s
    k8s_API.config_live_time(20)
    config_deploy("deploy")
    sleep(30)  # sometimes after deployment pod doesn't show up right away, which jeopardizes the below code
    print("Pod number is: {}, Waiting for pod to be terminated".format(
            k8s_API.get_number_pod(NAMESPACE)))
    while (k8s_API.get_number_pod(NAMESPACE) != 0):
        sleep(10)
    print("There is no pod in the system. Stablizing ...")
    sleep(10)  # to stablize the system
    timestamps["warm_disk_state_start"] = time.time()
    # during warm-disk, service is already deployed, so we'll see how much resource the system consumes
    collect_state(host, image, target_pods, repetition, WARM_DISK_STATE)
    timestamps["warm_disk_state_end"] = time.time()

    # NOTE: Warm CPU process: we'll trigger warm CPU by editing the deployment file
    # change live-time to maximum = 240s
    k8s_API.config_live_time(LIVE_TIME)
    config_deploy("deploy")
    timestamps["warm_disk_to_warm_CPU_process_start"] = time.time()
    collect_warm_disk_to_warm_CPU_process(
        host, image, target_pods, repetition, WARM_DISK_TO_WARM_CPU_PROCESS)
    timestamps["warm_disk_to_warm_CPU_process_end"] = time.time()
    sleep(20)
    # NOTE: Warm CPU state, must measure time < live time
    timestamps["warm_CPU_state_start"] = time.time()
    collect_state(host, image, target_pods, repetition, WARM_CPU_STATE)
    timestamps["warm_CPU_state_end"] = time.time()

    # NOTE: this process may happen within ms, so consider ignoring it
    # in that case, comment the following block + let the code sleep for a few seconds
    # timestamps["warm_CPU_to_active_start"]=time.time()
    # jobs_status[COLD_START_PROCESSING] = True
    # calculate_warm_CPU_2_active(target_pods, repetition, WARM_CPU_2_ACTIVE)
    # timestamps["warm_CPU_to_active_end"]=time.time()

    # NOTE: Here we create a curl request towards the running pod
    exec_pod(CURL_ACTIVE_INST, target_pods, "normal")
    print("Detection requests have arrived. Stablizing for at least 30 seconds ...")
    time.sleep(30)  # Here sleeping to stablize the pod for active measurement
    timestamps["active_state_start"] = time.time()
    # 30 seconds, this time must be lower than requested time
    collect_state(host, image, target_pods, repetition, ACTIVE_STATE)
    timestamps["active_state_end"] = time.time()

    # NOTE: Here we take log file out:
    exec_pod(CURL_FPS, target_pods, "fps")
    get_fps_exec(host, target_pods, repetition)

    # NOTE: Here we'll force terminate a pod after its time_window runs out.
    # Pre-condition: processing time of task must > time_window
    # force_terminate(target_pods)
    # timestamps["active_to_warm_disk_start"]=time.time()
    # calculate_active_2_warm_disk(target_pods, repetition)
    # timestamps["active_to_warm_disk_end"]=time.time()

    # NOTE: Warm CPU to warm disk: How to detect the pod is staying at warm CPU or active?: Check status terminating
    print("Waiting for pod to be terminated")
    while not k8s_API.is_pod_terminated():
        sleep(0.3)
    print("Pod has been terminated")

    timestamps["warm_CPU_to_warm_disk_process_start"] = time.time()
    collect_warm_CPU_to_warm_disk_process(
        host, image, target_pods, repetition, WARM_CPU_TO_WARM_DISK_PROCESS)
    timestamps["warm_CPU_to_warm_disk_process_end"] = time.time()
    print("There is no pod in the system.")

    # NOTE: active to warm disk
    # Test to see have trigger other container in a pod !!!!
    exec_pod(CURL_TRIGGER, target_pods, "trigger")
    print("Detection requests have arrived. Wait for containers in pod are ready ...")
    while not k8s_API.is_all_con_ready():
        print("Still waiting ...")
        sleep(2)
    exec_pod(CURL_ACTIVE_INST, target_pods, "normal")
    print("Detection requests have arrived. Stablizing for at least 30 seconds ...")
    time.sleep(20)  # Here sleeping to stablize the pod for active measurement
    timestamps["active_to_warm_disk_process_start"] = time.time()
    config_deploy("delete")
    # we can use the same function here :)
    collect_warm_CPU_to_warm_disk_process(
        host, image, target_pods, repetition, ACTIVE_TO_WARM_DISK_PROCESS)
    timestamps["active_to_warm_disk_process_end"] = time.time()

    # NOTE: Here we calculate the process warm disk to active, maybe change
    # to the older image (one that returns immediately after code is ready)
    # timestamps["warm_disk_to_active_start"]=time.time()
    # cal_warm_disk_to_active(target_pods, repetition, WARM_DISK_TO_ACTIVE_PROCESS)
    # timestamps["warm_disk_to_active_end"]=time.time()
    # wait until deployment scales down to zero
    while (k8s_API.get_number_pod(NAMESPACE) != 0):
        print("Waiting for pod to be terminated")
        sleep(10)
    print("There is no pod in the system.")

    # NOTE: warm disk to cold by deleting image
    # NOTE: this block is temporarily unused due to heavy image takes too long to be downloaded
    # print("Deleting image ...")
    # thread_event = threading.Event()
    # timestamps["warm_disk_to_cold_start"] = time.time()
    # threading.Thread(target=remote_worker_call, args=(
    #     DELETE_IMAGE_CMD, thread_event,)).start()
    # collect_warm_disk_to_cold_process(
    #     host, image, target_pods, repetition, WARM_DISK_TO_COLD_PROCESS, thread_event)
    # timestamps["warm_disk_to_cold_end"] = time.time()


    # NOTE: Cold state to warm disk by downloading image
    # NOTE: this block is temporarily unused due to heavy image takes too long to be downloaded
    # k8s_API.config_live_time(6)
    # config_deploy("deploy")
    # timestamps["cold_to_warm_disk_start"] = time.time()
    # collect_null_to_warm_disk_process(
    #     host, image, target_pods, repetition, COLD_TO_WARM_DISK_PROCESS)
    # timestamps["cold_to_warm_disk_end"] = time.time()

    timestamps_to_file(host, image, timestamps, target_pods, repetition)

    sleep(10)
    # NOTE: Now we consider from warm_disk/CPU to NULL state
    config_deploy("delete")
    sleep(30)
    # NOTE: this block is temporarily unused due to heavy image takes too long to be downloaded
    # remote_worker_call(DELETE_IMAGE_CMD)
    # sleep(10)

    # Maybe multiprocessing should be considered here
    # timestamps["warm_disk_to_null_start"]=time.time()
    # p0=Process(target=remote_worker_call, args=(DELETE_IMAGE.format(image), ))
    # p0.start()
    # multiservice_pods.delete_pods()
    # calculate_warm_disk_2_null_process(target_pods, repetition)
    # timestamps["warm_disk_to_null_end"]=time.time()

    event.set()
    print("Measurement finished.")
    print("Saving timestamps..")
    print("Finished!")

############################################################################
# ############################################################################

def curl_latency(host: str, image: str, list_quality: list, target_pods: int, repetition: int, event):
    # this function measure the curltime at each 
    # lifecycle state of a serverless function
    # It has been tested that we can not curl from
    # Cold state, so everything starts at Warm Disk
    # RESPONSE_URL = CURL_RESPONSE_HEAVY.format(quality)
    # print("current URL is: {}".format(RESPONSE_URL))
    k8s_API.config_image(IMAGE_NAME)
    k8s_API.config_live_time(2000) 
    config_deploy("deploy") 

    while not k8s_API.is_all_con_ready():
        print("Waiting for pod to be ready ...")
        sleep(2)
    print("Pod is ready!")
    sleep(10)
    # Warm CPU to Active
    print("Start collecting {}!".format(WARM_CPU_TO_ACTIVE_PROCESS))
    collect_curl(CURL_TRIGGER_TIME, host, image, target_pods, repetition, WARM_CPU_TO_ACTIVE_PROCESS, "NONE")
    print("Finish collecting {}!".format(WARM_CPU_TO_ACTIVE_PROCESS))
    # for quality in list_quality:
    #     # Response time from Warm CPU
    #     print("Start collecting {} with image quality is {} !".format(RESPOND_TIME_WARM_CPU, quality))
    #     jobs_status[RESPOND_TIME_WARM_CPU] = True
    #     collect_curl(CURL_RESPONSE_TIME.format(quality, "{}"), host, image, target_pods, repetition, RESPOND_TIME_WARM_CPU, quality)
    #     print("Finish collecting {} with image quality is {} !".format(RESPOND_TIME_WARM_CPU, quality))
    #     sleep(10)
    print("Finish everything!")
    config_deploy("delete") 
    sleep(30)
    # Warm Disk to Active
    # Response time from Warm Disk
    # while (k8s_API.get_number_pod(NAMESPACE) != 0):
    #     print("Waiting for pod to be terminated")
    #     sleep(10)
    # print("There is no pod in the system.")
    # print("Start collecting {}!".format(WARM_DISK_TO_ACTIVE_PROCESS))
    # collect_curl(CURL_INSTANT_HEAVY, host, image, target_pods, repetition, WARM_DISK_TO_ACTIVE_PROCESS)
    # print("Finish collecting {}!".format(WARM_DISK_TO_ACTIVE_PROCESS))
    
    # Response time from Warm Disk
    # while (k8s_API.get_number_pod(NAMESPACE) != 0):
    #     print("Waiting for pod to be terminated")
    #     sleep(10)
    # print("There is no pod in the system.")
    # print("Start collecting {}!".format(RESPOND_TIME_WARM_DISK))
    # collect_curl(RESPONSE_URL, host, image, target_pods, repetition, RESPOND_TIME_WARM_DISK)
    # print("Finish collecting {}!".format(RESPOND_TIME_WARM_DISK))
    
    event.set()
    print("Measurement finished.")
    # Warm Mem to Active - TBD
    # From Null/Cold to Active - is sum of normal measurement + curl measurement
    # For ex: Null --> Active = Null --> WarmDisk (normal measurement) + WarmDisk --> Active (curl measurement)

# # # ############################################################################
# # # ############################################################################
  
    
# # #     event.set()
# # #     print("Measurement finished.")

# # Using measure for testcase 1
def curl_complete_task(target_pods: int, target_containers: int, measurement_type: str, event):
    # Using for multipe_container, multipe_pod
    # Finishing time
    host = "mec"

    k8s_API.config_image(IMAGE_NAME)
    k8s_API.config_live_time(500) 
    config_deploy("deploy") 

    while not k8s_API.is_all_con_ready():
        print("Waiting for pod to be ready ...")
        sleep(2)
    print("Pod is ready!")
    sleep(10)
    # Warm CPU to Active
    exec_pod(CURL_ACTIVE_INST, target_pods, "normal")

    time.sleep(10)

    print("Start collecting {}!".format(COMPLETE_TASK_TIME))
    start_time = time.time()
    while True:
        # Change 3 parameters
        output_func = lambda target_pod, count: [reach_pod_log(i+1, j+1, measurement_type, 0) for i in range(target_pod) for j in range(count)]
        if check_all_elements(output_func(target_pods, target_containers), measurement_type, 0):
            print("Correct")
            break
        else:
            continue
    end_time = time.time()
    print("=================================> Final result:" + str(end_time - start_time + 12))

    # Write into file
    try:
        with open(DATA_COMPLETE_TIME_DIRECTORY.format(str(host), measurement_type, measurement_type), 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([float(end_time - start_time + 12)])
    except Exception as ex:
        print(ex)

    print("Finish collecting {}!".format(COMPLETE_TASK_TIME))

    print("Finish everything!")
    config_deploy("delete") 
    sleep(30)
    
    
    event.set()
    print("Measurement finished.")

# Using measure testcase 2
# def curl_complete_task(target_pods: int, target_containers: int, tartget_processes: int, measurement_type: str, event):
#     # Using for multipe_container, multipe_pod
#     # Finishing time

#     # 2-1-2
#     # 1-2-2
#     # 1-1-4
#     host = "mec"

#     k8s_API.config_image(IMAGE_NAME)
#     k8s_API.config_live_time(500) 
#     config_deploy("deploy") 

#     while not k8s_API.is_all_con_ready():
#         print("Waiting for pod to be ready ...")
#         sleep(2)
#     print("Pod is ready!")
#     sleep(10)
#     # Warm CPU to Active
#     exec_pod(CURL_ACTIVE_INST, target_pods, "normal")

#     time.sleep(10)

#     print("Start collecting {}!".format(COMPLETE_TASK_TIME))
#     start_time = time.time()
#     while True:
#         # Change 3 parameters
#         output_func = lambda target_pod, count: [reach_pod_log(i+1, j+1, measurement_type, int(target_containers)) for i in range(target_pod) for j in range(count)]
#         # 1 1 
#         if check_all_elements(output_func(target_pods, target_containers), measurement_type, int(tartget_processes)):
#             print("Correct")
#             break
#         else:
#             continue
#     end_time = time.time()
#     print("=================================> Final result:" + str(end_time - start_time + 12))

#     # Write into file
#     try:
#         with open(DATA_COMPLETE_TIME_DIRECTORY.format(str(host), measurement_type, measurement_type), 'a', newline='') as file:
#             writer = csv.writer(file)
#             writer.writerow([float(end_time - start_time + 12)])
#     except Exception as ex:
#         print(ex)

#     print("Finish collecting {}!".format(COMPLETE_TASK_TIME))

#     print("Finish everything!")
#     config_deploy("delete") 
#     sleep(30)
    
    
#     event.set()
#     print("Measurement finished.")
#     sleep(30)

# Using measurement testcase 3
def collect_benchmark_score(target_pods: int, target_containers: int):
    host = "mec"
    remote_worker_call(DELETE_IMAGE_CMD, MEC_USERNAME, MEC_IP, MEC_PASSWORD)
    sleep(15)
    k8s_API.config_image(IMAGE_NAME)
    k8s_API.config_live_time(500)
    config_deploy("deploy")

    file_benchmark = "/home/kien/storage/test-results/testtest{}{}/composite.xml"
    file_benchmark_list = [(file_benchmark.format(i + 1, j)) for i in range(target_pods) for j in range(target_containers)]
    print(file_benchmark_list)

    while True:
        check_all_files = all(os.path.exists(file) for file in file_benchmark_list)
        if check_all_files:
            break
        else:
            continue
    sleep(5)
    result_score = [float(reach_benchmark_score(file)) for file in file_benchmark_list]
    print(result_score)
    print("Measurement finished.")


    config_deploy("delete")
    command = "kubectl delete pod --all -n serverless --force --grace-period 0"
    output, error = execute_kubectl_command(command)

    while (k8s_API.get_number_pod(NAMESPACE) != 0):
        print("Waiting for pod to be terminated")
        command = "kubectl delete pod --all -n serverless --force --grace-period 0"
        output, error = execute_kubectl_command(command)
        sleep(5)
    print("There is no pod in the system.")
    sleep(10)
    print("Measurement finished.")

    print("Saving benchmarking score...")
    try:
        with open(DATA_BENCHMARKING, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([max(result_score)])
    except Exception as ex:
        print(ex)

    print("Deleting file benchmarking score")
    try:
        # Attempt to remove the directory and its contents
        shutil.rmtree(BENCHMARKING_DIRECTORY)
        print(f"Directory '{BENCHMARKING_DIRECTORY}' and its contents have been successfully deleted.")
    except OSError as e:
        # Handle the case where directory deletion is unsuccessful
        print(f"Unable to delete directory '{BENCHMARKING_DIRECTORY}': {e}")

    print("Finished!")
    sleep(5)

############################################################################
############################################################################
if __name__ == "__main__": #For testing only


    target_pods_scale = sys.argv[1]  # number of scaling pod
    repeat_time = sys.argv[2]
    INSTANCE = sys.argv[3]  # jetson
    # this P0 process runs infintely, detect and manual terminate "terminating" pods
    event = Event()  # the event is unset when created
    p0 = Process(target=auto_delete, args=(event, ))
    p0.start()
    # collect_life_cycle(int(target_pods_scale), int(repeat_time), event)
    # p1 = Process(target=collect_life_cycle, args=(event, int(target_pods_scale), repeat_time, ), daemon = True)
    # print("Start calculate job on {}".format(INSTANCE))
    # p1.start()
    p0.join()
    # p1.join()
