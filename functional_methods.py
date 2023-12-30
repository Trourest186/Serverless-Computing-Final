from collections import defaultdict
from datetime import datetime
import queue
import requests
import variables
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
from power import pw, em
from variables import *
import k8s_API
from time import sleep
import re
import psutil


def get_bytes():
    return psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

# def get_mbits():
#     return (psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv)/1024./1024.*8


# def thread_remote(cmd: str):
#     thread = threading.Thread(target=remote_worker_call, args=(cmd, )).start()
#     return thread


def remote_worker_call(command: str, host_username: str, host_ip: str, host_pass: str, event=None):
    print("Trying to connect to remote host {}, IP: {}".format(
        host_username, host_ip))
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ip, username=host_username,
                       password=host_pass)
    except paramiko.AuthenticationException:
        print("Authentication failed when connecting to %s" % host_ip)
        sys.exit(1)
    except:
        print("Could not SSH to %s, waiting for it to start" % host_ip)
    print(command)
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    stdin.write(JETSON_PASSWORD + '\n')
    stdin.flush()
    for line in stdout:
        print(line.strip('\n'))
    client.close()
    if event is not None:
        event.set()


def get_data_from_api(query: str):
    url_data = PROMETHEUS_DOMAIN + query
    try:
        contents = urllib.request.urlopen(url_data).read().decode('utf-8')
        values = json.loads(contents)["data"]["result"][0]['value']
    except:
        values = -1
    return values

# def get_power():
#     # print(pw.get_power()/1000.0)
#     return pw.get_power()/1000.0

# def is_pod_terminating(): # check pod is terminating? consider replacing this function with Py-python
#     status = str(subprocess.run(['deployments/get_pod_status.sh', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')).strip()
#     return status == TERMINATING_STATUS


def get_curl_values_and_update_job(cmd: str, host: str, image: str, target_pods: int, job: str, quality: str, repetition: int):
    # Run the command and capture its output
    status, results = exec_pod(cmd, target_pods, "curl_time")
    # print("Size of results: {}".format(len(results)))
    for i, output in enumerate(results, start=1):
        # output_t = output.decode("utf-8")
        # print("Type of output: {}".format(type(output)))
        # print(output)
        if b"OK" in output or b"Active" in output:
            print("'OK' request {}".format(i))
        else:
            print("Error in request {}".format(i))
            try:
                writer = csv.writer(open(DATA_CURL_FILE_DIRECTORY.format(
                    str(host), str(image), str(target_pods), str(repetition), generate_file_time), 'a'))
                writer.writerow([job, quality, "error"])
            except Exception as ex:
                print(ex)
            continue
        output = output.replace(b",", b".")

        time_namelookup = float((output.split(
            b"time_namelookup:  ")[1].split(b" ")[0]).split(b"s")[0])
        
        time_connect = float((output.split(b"time_connect:  ")[1].split(b" ")[0]).split(b"s")[0])

        time_appconnect = float((output.split(
            b"time_appconnect:  ")[1].split(b" ")[0]).split(b"s")[0])
        
        time_pretransfer = float((output.split(
            b"time_pretransfer:  ")[1].split(b" ")[0]).split(b"s")[0].split(b"s")[0])
        
        time_redirect = float((output.split(b"time_redirect:  ")[1].split(b" ")[0]).split(b"s")[0])

        time_starttransfer = float((output.split(
            b"time_starttransfer:  ")[1].split(b" ")[0]).split(b"s")[0])
        
        time_total = float((output.split(b"time_total:  ")[1].split(b" ")[0]).split(b"s")[0].split(b"s")[0])

        # Store the values in a dictionary
        # time_dict = {"time_namelookup": time_namelookup, "time_connect": time_connect, "time_appconnect": time_appconnect, "time_pretransfer": time_pretransfer,
        #           "time_redirect": time_redirect, "time_starttransfer": time_starttransfer, "time_total": time_total}

        # Write value to data file
        try:
            writer = csv.writer(open(DATA_CURL_FILE_DIRECTORY.format(
                str(host), str(image), str(target_pods), str(repetition), generate_file_time), 'a'))
            writer.writerow([time_namelookup, time_connect, time_appconnect,
                            time_pretransfer, time_redirect, time_starttransfer, time_total, job, quality])
        except Exception as ex:
            print(ex)


def get_prometheus_values_and_update_job(host: str, image: str, target_pods: int, state: str, repetition: int):
    ip = ""
    gpu_query = ""
    values_power = 0
    values_energy = 0
    if host == 'jetson':
        ip = JETSON_IP
        # gpu_query = VALUES_GPU_QUERY_JETSON
        values_power = pw.get_power()/1000.0
        values_energy = 0 # Jetson power board has now energy value, so pls ignore it
    else:
        ip = MEC_IP
        gpu_query = VALUES_GPU_QUERY_MEC
        voltage, current, energy, real_power, apparent_power, reactive_power, power_factor, frequency = em.get_energy_data()
        # real_power = 100000
        values_power = real_power/100.0
        values_energy = energy*36 #Convert from Wh --> J
    values_nw = get_bytes()
    values_per_cpu_in_use = get_data_from_api(VALUES_CPU_QUERY.format(ip))
    # values_per_gpu_in_use = get_data_from_api(gpu_query.format(ip))
    values_per_gpu_in_use = [0,0]
    # values_network_receive = get_data_from_api(VALUES_NETWORK_RECEIVE_QUERY)
    values_memory = get_data_from_api(
        VALUES_MEMORY_QUERY.format(ip, ip, ip))
    # print(values_memory)
    values_running_pods = k8s_API.get_number_pod()
    # print(values_running_pods)

    # write values to file
    try:
        writer = csv.writer(open(DATA_PROMETHEUS_FILE_DIRECTORY.format(
            str(host), str(image), str(target_pods), str(repetition), generate_file_time), 'a'))
        writer.writerow([values_memory[0], datetime.utcfromtimestamp(values_memory[0]).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], values_running_pods,
                         values_power, values_energy, values_per_cpu_in_use[1], values_per_gpu_in_use[1], values_memory[1], values_nw, state])
    except Exception as ex:
        print(ex)
    # if TEST_MODE: print("Current pods: %s, target: %d" % (curr_pods, (int(target_pods)+POD_EXSISTED)))


# def update_job_status(state:str, values_running_pods, target_pods:int):
#     #+2 on target pods for the default pods
#     curr_running_pods = int(values_running_pods[1])
#     # print(state, values_running_pods, target_pods, POD_EXISTED)
#     if WARM_DISK_2_WARM_CPU_PROCESS == state or "cold_start:curl" == state:
#         if curr_running_pods == POD_EXISTED + target_pods:
#             jobs_status[WARM_DISK_TO_WARM_CPU_PROCESS] = False
#     elif WARM_CPU_STATE == state:
#         if curr_running_pods == POD_EXISTED: # it means pods have been deleted
#             jobs_status[WARM_CPU_STATE] = False
#     elif DELETE_JOB == state:
#         if curr_running_pods == POD_EXISTED:
#             jobs_status[DELETE_PROCESSING] = False

# NOTE: Tung will handle this function
# def create_request(url:str): # Here change to kubectl exec command by k8s python
#     #rs_response = requests.get(url)
#     rs_response = kubectl exec -it ubuntu -- "url"
#     print(rs_response.content)

def bash_cmd(cmd: str):
    result = subprocess.run([cmd], stderr=subprocess.PIPE, text=True)
    print("Bash output: {}".format(result.stderr))

# def create_request_thread(target_pods: int, request_type: str):
#     for i in range(target_pods):
#         print("Start thread :", i + 1)
#         if request_type == "start":
#             threading.Thread(target=create_request, args=("http://detection"+str(i+1)+".default.svc.cluster.local/{}/api/stream/{}/{}".format(STREAMING_IP, DETECTION_TIME))).start()
#         else if request_type == "stop":
#             threading.Thread(target=create_request, args=("http://detection"+str(i+1)+".default.svc.cluster.local/api/terminate")).start()
#         else:
#             break


def timestamps_to_file(host: str, image: str, timestamps: dict, target_pods: int, repetition: int):
    # print(timestamps)
    with open(DATA_TIMESTAMP_FILE_DIRECTORY.format(
            str(host), str(image), str(target_pods), str(repetition), generate_file_time), 'w') as f:
        # for key, value in terminate_state.items():
        #     timestamps[key+"_start"]=min(value)
        #     timestamps[key+"_end"]=max(value)
        for key in timestamps.keys():
            if "_start" in key:
                job_key = re.search('(.*)_start', key).group(1)
            if "_end" in key:
                job_key = re.search('(.*)_end', key).group(1)
            f.write("%s,%s,%s\n" % (key, timestamps[key], job_key))

# NOTE: the following function auto terminate pods


def auto_delete(target_pod, event):
    token = True
    while not event.is_set():
        if k8s_API.is_pod_terminated() and not k8s_API.is_all_con_not_ready() and token:
            print("Detect terminating pod, it'll be deleted shortly")
            if exec_pod(CURL_TERM, target_pod, "auto_delete"):
                token = False
            else:
                print("Try to terminate pod, but IP returns None, will try again!")
                token = True
        elif not k8s_API.is_pod_terminated():
            # print("Status is: {}, token is: {}".format(k8s_API.is_pod_terminated(), token))
            token = True
        else:
            # print("Status is: {}, token is: {}".format(k8s_API.is_pod_terminated(), token))
            sleep(1)
        # print("In terminating while loop")
    print("Overwatch for termination finished!")

#
def exec_pod(cmd: str, type: str = "normal"):
    results = []
    threads = []
    IPs = []
    result_queue = queue.Queue()
    output_lock = threading.Lock()
    status = True

    if type == "auto_delete":
        list_pod = k8s_API.get_list_term_pod(NAMESPACE)
    else:
        list_pod = k8s_API.list_namespaced_pod_status(NAMESPACE)
    
    for i in list_pod:
        IP = i.pod_ip
        if (IP is None):
            return False, results
        else:
            IPs.append(IP)
    for ip in IPs:
        t = threading.Thread(target=connect_pod_exec, args=(cmd.format(ip), result_queue, output_lock, ))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    while not result_queue.empty():
        result = result_queue.get()
        results.append(result)
    status = True
    return status, results
    
# Giang
def execute_kubectl_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode(), error.decode()

def reach_ip_pod(detection_number, index=0):
    # Construct the kubectl command to get the pods
    command = f"kubectl get pods -n serverless -o wide | awk '/detection{detection_number}/ && $3 == \"Running\" {{print $6}}'"
    
    # Execute the command
    output, error = execute_kubectl_command(command)

    if error:
        print(f"Command error: {error}")
    
    # Split the output into lines and get the IP based on the provided index
    lines = output.split('\n')
    filtered_pods = [line.strip() for line in lines if line.strip()]
    
    if filtered_pods:
        return filtered_pods[index] if 0 <= index < len(filtered_pods) else filtered_pods[0]
    else:
        return f"No running pod found for detection{detection_number}"

def reach_pod_name(detection_number, index=0):
    # Construct the kubectl command to get the pods
    command = f"kubectl get pods -n serverless | awk '/detection{detection_number}/ && $3 == \"Running\" {{print $1}}'"
    
    # Execute the command
    output, error = execute_kubectl_command(command)
    
    # Return the pod name
    return output.split('\n')[index] if output else None

def reach_pod_log(detection_number, container_number, measurement_type: str):
    pod_name = reach_pod_name(detection_number)

    if measurement_type == "multiple_pod":
        command = f"kubectl logs {pod_name} -n serverless | tail -n 1"
    elif measurement_type == "multiple_container":
        command = f"kubectl logs {pod_name} -n serverless -c application{container_number} | tail -n 1"
    else:
        pass
    
    output, error = execute_kubectl_command(command)

    return output

def check_all_elements(array):
    for element in array:
        if 'No more frames.' not in element:
            return False
    return True

def case_set(budget: int):
    cases = []

    for a in range (1, budget + 1):
        for b in range(1, budget + 1):
            c = budget // (a * b)
            if a * b * c == budget:
                cases.append([a, b, c])
    
    return cases

## Using for multiple pod
def exec_pod(cmd: str, target_pod: int, type: str = "normal"):
    results = []
    threads = []
    IPs = []
    result_queue = queue.Queue()
    output_lock = threading.Lock()
    status = True

    if type == "auto_delete":
        list_pod = []
        while len(list_pod) < target_pod: # when multiple pods are deployed, sometimes the code can't query the number of term pod correctly
            list_pod = k8s_API.get_list_term_pod(NAMESPACE)
            print("Query of list_term_pod is {}, while target_pod is {}".format(len(list_pod), target_pod))
        for i in list_pod:
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(i.pod_ip), result_queue, output_lock, ))
            threads.append(t)
    elif type == "fps":
        for i in range(1, target_pod + 1, 1):
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(i, i), result_queue, output_lock, ))
            threads.append(t)
    else:
        for i in range(1, target_pod + 1, 1):
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(i), result_queue, output_lock, ))
            threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    while not result_queue.empty():
        result = result_queue.get()
        results.append(result)
    status = True
    return status, results

## Using for multiple_container
# def exec_pod(cmd: str, target_pod: int, type: str = "normal"):
    results = []
    threads = []
    IPs = []
    result_queue = queue.Queue()
    output_lock = threading.Lock()
    status = True
    target_command = reach_ip_pod(target_pod)
    target_port = 8881

    # container_count = 2 # Need change
    if type == "auto_delete":
        list_pod = []
        while len(list_pod) < target_pod: # when multiple pods are deployed, sometimes the code can't query the number of term pod correctly
            list_pod = k8s_API.get_list_term_pod(NAMESPACE)
            print("Query of list_term_pod is {}, while target_pod is {}".format(len(list_pod), target_pod))
        for i in list_pod:
            for count in range(0, CONTAINER_COUNT):
                t = threading.Thread(target=connect_pod_exec, args=(cmd.format(i.pod_ip, target_port + int(count)), result_queue, output_lock, ))
                threads.append(t)
    elif type == "fps":
        for i in range(0, CONTAINER_COUNT):
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(target_command, target_port + int(i), i), result_queue, output_lock, ))
            threads.append(t)
    elif type == "trigger":
        for i in range(1, target_pod + 1, 1):
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(i), result_queue, output_lock, ))
            threads.append(t)
    else:
        for i in range(0, CONTAINER_COUNT):
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(target_command, target_port + int(i) ), result_queue, output_lock, )) # Need fix
            threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    while not result_queue.empty():
        result = result_queue.get()
        results.append(result)
    status = True
    return status, results

# Using for multiple_mix
# def exec_pod(cmd: str, target_pod: int, type: str = "normal"):
    numPods = 2
    numContainers = 1
    numProcesses = 2

    results = []
    threads = []
    IPs = []
    result_queue = queue.Queue()
    output_lock = threading.Lock()
    status = True
    # target_command = reach_ip_pod()
    target_port = 8881

    if type == "auto_delete":
        list_pod = []
        while len(list_pod) < numPods: # when multiple pods are deployed, sometimes the code can't query the number of term pod correctly
            list_pod = k8s_API.get_list_term_pod(NAMESPACE)
            print("Query of list_term_pod is {}, while target_pod is {}".format(len(list_pod), numPods))
        for i in list_pod:
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(i.pod_ip), result_queue, output_lock, ))
            threads.append(t)
    elif type == "fps":
        for pod_index in range(1, numPods + 1, 1):
            target_command = reach_ip_pod(pod_index)
            for container_index in range(0, numContainers):
                for i in range(0, numProcesses):
                    t = threading.Thread(target=connect_pod_exec, args=(cmd.format(target_command, target_port + int(container_index), pod_index, ), result_queue, output_lock, )) # Need fix
                    threads.append(t)
    elif type == "trigger":
        for i in range(1, numPods + 1, 1):
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(i), result_queue, output_lock, ))
            threads.append(t)
    else:
        for pod_index in range(1, numPods + 1, 1):
            target_command = reach_ip_pod(pod_index)
            for container_index in range(0, numContainers):
                for i in range(0, numProcesses):
                    t = threading.Thread(target=connect_pod_exec, args=(cmd.format(target_command, target_port + int(container_index) ), result_queue, output_lock, )) # Need fix
                    threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    while not result_queue.empty():
        result = result_queue.get()
        results.append(result)
    status = True
    return status, results

## Using for multiple processing
# def exec_pod(cmd: str, target_pod: int, type: str = "normal"):
    results = []
    threads = []
    streaming_count = 2
    IPs = []
    result_queue = queue.Queue()
    output_lock = threading.Lock()
    status = True
    if type == "auto_delete":
        list_pod = []
        while len(list_pod) < target_pod: # when multiple pods are deployed, sometimes the code can't query the number of term pod correctly
            list_pod = k8s_API.get_list_term_pod(NAMESPACE)
            print("Query of list_term_pod is {}, while target_pod is {}".format(len(list_pod), target_pod))
        for i in list_pod:
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(i.pod_ip), result_queue, output_lock, ))
            threads.append(t)
    elif type == "fps":
        for i in range(1, streaming_count + 1, 1):
            index_app = 1 # Default for a only application
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(index_app, index_app), result_queue, output_lock, ))
            threads.append(t)
    elif type == "trigger":
        for i in range(1, streaming_count + 1, 1):
            index_app = 1 # Default for a only application
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(index_app), result_queue, output_lock, ))
            threads.append(t)
    else:
        for i in range(1, streaming_count + 1, 1):
            # i reprensent DNS app
            index_app = 1 # Default for a only application

            # index_port: for multiple streaming
            index_port = int(STREAMING_PORT) + i - 1
            # t = threading.Thread(target=connect_pod_exec, args=(cmd.format(index_app, str(index_port)), result_queue, output_lock, ))
            t = threading.Thread(target=connect_pod_exec, args=(cmd.format(index_app), result_queue, output_lock, ))
            threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    while not result_queue.empty():
        result = result_queue.get()
        results.append(result)
    status = True
    return status, results

def get_fps_exec(host, target_pod, rep):
    try:
        for i in range(1,target_pod + 1, 1):
            cmd = "kubectl cp ubuntu:file{}.log".format(i) + " " + DATA_FPS_FILE_DIRECTORY.format(host, target_pod, rep, i, generate_file_time)
            print(cmd)
            output = subprocess.check_output(['/bin/bash', '-c', cmd]) # or check_output
    except subprocess.CalledProcessError as e:
        output = str(e.output)
    return output

def connect_pod_exec(target_command: str, result_queue, lock, target_name: str = "ubuntu"):
    print(target_command)
    command = "kubectl exec -it {} -- {} ".format(target_name, target_command) # Need fix
    trial = 0
    while trial < 20:
        try:
            output = subprocess.check_output(['/bin/bash', '-c', command]) # or check_output
            with lock:
                result_queue.put(output)
        except subprocess.CalledProcessError as e:
            output = str(e.output)
            # with output_lock:
            #     print("Subprocess output is: {}".format(output))
            if "52" in output or "200" in output:
                # with output_lock:
                #     print("Terminated successfully")
                return 
            else:
                # with output_lock:
                #     print("Terminated unsuccessfully, trial: {}".format(trial))
                sleep(1)
                trial = trial + 1
                continue
        # with output_lock:
        #     print("Seem like a good request, but we never know :)")
        return output
    # with output_lock:
    #     print("The system has sent {} times curl cmd, but none returns successfully.".format(trial))

def config_deploy(cmd: str):
    Process(target=k8s_API.config_deploy, args=(cmd, )).start()
    # threading.Thread(target= k8s_API.config_deploy, args=(cmd, )).start()


if __name__ == "__main__":
    # print(pw.get_power()/1000.0)
    # remote_worker_call("sudo ls -a")
    # sleep(100)
    # thread_event = threading.Event()
    # remote_worker_call(DELETE_IMAGE_CMD, thread_event)
    # get_prometheus_values_and_update_job('mec', 'image', 1, 1, '1')
    # sudo ctr images remove docker.io/kienkauko/nettools:latest@sha256:573c90a86216c26c02b27ce4105ea7cbf09016659fd30e8f8f61f67fab324620

    output = subprocess.check_output(['/bin/bash', '-c', 'curl -w \"@curl-time.txt\" google.com'])
        # print(output)

        # Extract the values you're interested in from the output
        # print(output.split(b"time_pretransfer:  ")[1].split(b" ")[0])

    time_namelookup = float(output.split(
        b"time_namelookup:  ")[1].split(b" ")[0])
    time_connect = float(output.split(b"time_connect:  ")[1].split(b" ")[0])
    time_appconnect = float(output.split(
        b"time_appconnect:  ")[1].split(b" ")[0])
    time_pretransfer = float(output.split(
        b"time_pretransfer:  ")[1].split(b" ")[0])
    time_redirect = float(output.split(b"time_redirect:  ")[1].split(b" ")[0])
    time_starttransfer = float(output.split(
        b"time_starttransfer:  ")[1].split(b" ")[0])
    time_total = float(output.split(b"time_total:  ")[1].split(b" ")[0])
    # Store the values in a dictionary
    time_dict = {"time_namelookup": time_namelookup, "time_connect": time_connect, "time_appconnect": time_appconnect, "time_pretransfer": time_pretransfer,
                "time_redirect": time_redirect, "time_starttransfer": time_starttransfer, "time_total": time_total}
    print(time_dict)
    # Write value to data file
    # try:
    #     writer = csv.writer(open(DATA_CURL_FILE_DIRECTORY.format(
    #         str(host), str(image), str(target_pods), str(repetition), generate_file_time), 'a'))
    #     writer.writerow([time_namelookup, time_connect, time_appconnect,
    #                     time_pretransfer, time_redirect, time_starttransfer, time_total, job])
    # except Exception as ex:
    #     print(ex)
