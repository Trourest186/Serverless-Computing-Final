import yaml
import os
import subprocess
import time


DEFAULT_DIRECTORY = os.getcwd()
DEPLOYMENT_PATH = DEFAULT_DIRECTORY + "/deploy.yaml"
TEMPLATE_PATH2 = DEFAULT_DIRECTORY + "/template2.yaml"
TEMPLATE_PATH3 = DEFAULT_DIRECTORY + "/template3.yaml"
from variables import *
import csv

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
import numpy as np

# def update_deployment(target_pods_scale: int, image: str,  host: str, path_file_deploy: str = TEMPLATE_PATH):
# #opens the capture file and updates the replica values
#     try:
#         new_deployment = []
#         for target_pod in range(0, target_pods_scale, 1):
#             docs = list(yaml.load_all(open(path_file_deploy, "r"), Loader=yaml.SafeLoader))
#             for doc in docs:
#                 for key, value in doc.items():
#                     if value == "serving.knative.dev/v1":
#                         doc["metadata"]["name"] = "detection"+str(target_pod+1)
#                         doc["spec"]["template"]["spec"]["nodeSelector"]["kubernetes.io/hostname"] = str(host)
#                         doc["spec"]["template"]["spec"]["containers"][0]["image"] = str(image)
#                         break
#                 new_deployment.insert(target_pod,doc)

#         with open(DEPLOYMENT_PATH, 'w') as yaml_file:
#             yaml.dump_all(new_deployment, yaml_file, default_flow_style=False)
#     except yaml.YAMLError as exc:
#         print(exc)

# Multiple container
# def update_multi_container_deployment(target_containers_scale: int, image: str, host: str, path_file_deploy: str = TEMPLATE_PATH2):
#     try:
#         new_deployment = []
#         docs = list(yaml.load_all(open(path_file_deploy, "r"), Loader=yaml.SafeLoader))
#         for doc in docs:
#             if doc.get("apiVersion") == "serving.knative.dev/v1" and doc.get("kind") == "Service":
#                 doc["metadata"]["name"] = "detection1"
#                 doc["spec"]["template"]["metadata"]["annotations"]["autoscaling.knative.dev/window"] = "60s"
#                 doc["spec"]["template"]["spec"]["containers"][0]["image"] = image
#                 doc["spec"]["template"]["spec"]["nodeSelector"]["kubernetes.io/hostname"] = str(host)
#                 # doc["spec"]["template"]["spec"]["containers"][0]["env"][0]["value"] = str(target_pods_scale)

#                 if target_containers_scale > 1:
#                     for i in range(1, target_containers_scale):
#                         additional_container = {
#                             "name": f"application{i + 1}",
#                             "image": "trourest186/multiple_container",
#                             "resources": {
#                                 "requests": {
#                                     "cpu": "1000m"
#                                 }
#                             },
#                             "env": [
#                                 {
#                                     "name": "PORT",
#                                     "value": str(8881 + i)
#                                 }
#                             ]
#                         }
#                         doc["spec"]["template"]["spec"]["containers"].append(additional_container)

#                 new_deployment.append(doc)
#                 break

#         with open(DEPLOYMENT_PATH, 'w') as yaml_file:
#             yaml.dump_all(new_deployment, yaml_file, default_flow_style=False, sort_keys=False)
#     except yaml.YAMLError as exc:
#         print(exc)

# Multiple mix
def update_multi_container_deployment(target_pods_scale: int, image: str, host: str, path_file_deploy: str = TEMPLATE_PATH2):
    # target_pods_scale = 2 # Fixed
    try:
        new_deployment = []
        docs = list(yaml.load_all(open(path_file_deploy, "r"), Loader=yaml.SafeLoader))
        for doc in docs:
            if doc.get("apiVersion") == "serving.knative.dev/v1" and doc.get("kind") == "Service":
                doc["metadata"]["name"] = "detection1"
                doc["spec"]["template"]["metadata"]["annotations"]["autoscaling.knative.dev/window"] = "60s"
                doc["spec"]["template"]["spec"]["containers"][0]["image"] = image
                doc["spec"]["template"]["spec"]["nodeSelector"]["kubernetes.io/hostname"] = str(host)
                # doc["spec"]["template"]["spec"]["containers"][0]["env"][0]["value"] = str(target_pods_scale)
                
                if CONTAINER_COUNT > 1:
                    for i in range(1, CONTAINER_COUNT):
                        additional_container = {
                            "name": f"application{i + 1}",
                            "image": MULTIPLE_MIX_IMAGE_NAME_x86,
                            "resources": {
                                "limits": {
                                    "cpu": "1000m"
                                }
                            },
                            "env": [
                                {
                                    "name": "PORT",
                                    "value": str(8881 + i)
                                }
                            ]
                        }
                        doc["spec"]["template"]["spec"]["containers"].append(additional_container)
                
                new_deployment.append(doc)
                break

        with open(DEPLOYMENT_PATH, 'w') as yaml_file:
            yaml.dump_all(new_deployment, yaml_file, default_flow_style=False, sort_keys=False)
    except yaml.YAMLError as exc:
        print(exc)

def update_deployment(target_pods_scale: int, image: str,  host: str, path_file_deploy: str = TEMPLATE_PATH):
#opens the capture file and updates the replica values
    try:  
        new_deployment = []
        for target_pod in range(0, target_pods_scale, 1):
            docs = list(yaml.load_all(open(path_file_deploy, "r"), Loader=yaml.SafeLoader))
            for doc in docs:
                for key, value in doc.items():
                    if value == "serving.knative.dev/v1":
                        doc["metadata"]["name"] = "detection"+str(target_pod+1)
                        doc["spec"]["template"]["spec"]["nodeSelector"]["kubernetes.io/hostname"] = str(host)
                        doc["spec"]["template"]["spec"]["containers"][0]["image"] = str(image)
                        break
                new_deployment.insert(target_pod,doc)

        with open(DEPLOYMENT_PATH, 'w') as yaml_file:
            yaml.dump_all(new_deployment, yaml_file, default_flow_style=False)
    except yaml.YAMLError as exc:
        print(exc)
# def update_multi_mix_deployment(numPods: int, numContainers: int, numProcesses: int, image: str, host: str, path_file_deploy: str = TEMPLATE_PATH2):
#     try:
#         new_deployment = []
#         for index in range(0, numPods, 1 ):
#             docs = list(yaml.load_all(open(path_file_deploy, "r"), Loader=yaml.SafeLoader))
#             for doc in docs:
#                 if doc.get("apiVersion") == "serving.knative.dev/v1" and doc.get("kind") == "Service":
#                     cpu_request = str(1000*numProcesses) + 'm'

#                     doc["metadata"]["name"] = "detection" + str(index + 1)
#                     doc["spec"]["template"]["metadata"]["annotations"]["autoscaling.knative.dev/window"] = "60s"
#                     doc["spec"]["template"]["spec"]["containers"][0]["image"] = image
#                     doc["spec"]["template"]["spec"]["nodeSelector"]["kubernetes.io/hostname"] = str(host)
#                     doc["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"] = cpu_request

#                     # doc["spec"]["template"]["spec"]["containers"][0]["env"][0]["value"] = str(target_pods_scale)
#                     if numContainers > 1:
#                         for i in range(1, numContainers):
#                             additional_container = {
#                                 "name": f"application{i + 1}",
#                                 "image": image,
#                                 "resources": {
#                                     "requests": {
#                                         "cpu": cpu_request
#                                     }
#                                 },
#                                 "env": [
#                                     {
#                                         "name": "PORT",
#                                         "value": str(8881 + i)
#                                     }
#                                 ]
#                             }
#                             doc["spec"]["template"]["spec"]["containers"].append(additional_container)
#                     new_deployment.append(doc)
#                     break


#         with open(DEPLOYMENT_PATH, 'w') as yaml_file:
#             yaml.dump_all(new_deployment, yaml_file, default_flow_style=False, sort_keys=False)
#     except yaml.YAMLError as exc:
#         print(exc)
# def config_image(image: str, path_file_deploy: str = DEPLOYMENT_PATH): #, detection_image: s
def execute_kubectl_command(command):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
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
    lines = output.split("\n")
    filtered_pods = [line.strip() for line in lines if line.strip()]

    if filtered_pods:
        return (
            filtered_pods[index]
            if 0 <= index < len(filtered_pods)
            else filtered_pods[0]
        )
    else:
        return f"No running pod found for detection{detection_number}"


def reach_pod_name(detection_number, index=0):
    # Construct the kubectl command to get the pods
    command = f"kubectl get pods -n serverless | awk '/detection{detection_number}/ && $3 == \"Running\" {{print $1}}'"

    # Execute the command
    output, error = execute_kubectl_command(command)

    # Return the pod name
    return output.split("\n")[index] if output else None


# def reach_pod_log(detection_number):
#     pod_name = reach_pod_name(detection_number)

#     command = f""
#     output, error = execute_kubectl_command(command)
#     return output


def reach_pod_log(detection_number, container_number, measurement_type: str):
    pod_name = reach_pod_name(detection_number)

    if measurement_type == "multiple_pod":
        command = f"kubectl logs {pod_name} -n serverless | tail -n 1"
    elif measurement_type == "multiple_container":
        command = f"kubectl logs {pod_name} -n serverless -c application{container_number} | tail -n 1"
    else:
        command = f"kubectl logs {pod_name} -n serverless | grep -c 'No more'"

    output, error = execute_kubectl_command(command)

    return output


# def check_log_for_message(detection_number):
#     pod_name = reach_pod_name(detection_number)
#     # Construct the kubectl command to get the logs
#     command = f"kubectl logs -n serverless {pod_name} -c application1"

#     # Execute the command
#     output, error = execute_kubectl_command(command)

#     # Check if the log contains 'No more frames.'
#     return 'No more frames.' in output
CONTAINER_COUNT = 4


def check_all_elements(array, measurement_type: str):
    count = STREAMING_COUNT
    if measurement_type == "multiple_pod" or measurement_type == "multiple_container":
        for element in array:
            if "No more frames." not in element:
                return False
    else:
        for element in array:
            if int(element) != count:
                return False

    return True


# main.py
def test(variable_name: str, new_value: int):
    variable_name = "STREAMING_COUNT"
    new_value = "5"

    with open("variables.py", "r") as config_file:
        lines = config_file.readlines()

    for i, line in enumerate(lines):
        if line.startswith(variable_name):
            lines[i] = f"{variable_name} = {new_value}\n"
            break

    with open("variables.py", "w") as config_file:
        config_file.writelines(lines)


def case_set(budget: int):
    cases = []

    for a in range(1, budget + 1):
        for b in range(1, budget + 1):
            c = budget // (a * b)
            if a * b * c == budget:
                cases.append([a, b, c])

    return cases


DEFAULT_DIRECTORY = os.getcwd()
DATA_COMPLETE_TIME_DIRECTORY = (
    DEFAULT_DIRECTORY + "/data/complete_time/{}/{}/storage_{}.csv"
)


def config_image(
    image: str, path_file_deploy: str = DEPLOYMENT_PATH
):  # , detection_image: str
    # opens the capture file and updates the replica values
    try:
        docs = list(yaml.load_all(open(path_file_deploy, "r"), Loader=yaml.SafeLoader))
        for doc in docs:
            for key, value in doc.items():
                if value == "serving.knative.dev/v1":
                    doc["spec"]["template"]["spec"]["containers"][0]["image"] = str(
                        image
                    )
                    break
        with open(DEPLOYMENT_PATH, "w") as yaml_file:
            yaml.dump_all(docs, yaml_file, default_flow_style=False, sort_keys=False)
    except yaml.YAMLError as exc:
        print(exc)
    print("Image name has been changed")

def update_benchmark_deployment(numPods: int, numContainers: int, numProcesses: int, image: str, host: str, path_file_deploy: str = TEMPLATE_PATH3):
    try:
        new_deployment = []
        for index in range(0, numPods, 1):
            docs = list(yaml.load_all(open(path_file_deploy, "r"), Loader=yaml.SafeLoader))
            for doc in docs:
                if doc.get("apiVersion") == "serving.knative.dev/v1" and doc.get("kind") == "Service":
                    cpu_request = str(1000 * numProcesses) + 'm'

                    doc["metadata"]["name"] = "detection" + str(index + 1)
                    doc["spec"]["template"]["metadata"]["annotations"]["autoscaling.knative.dev/window"] = "60s"
                    doc["spec"]["template"]["spec"]["containers"][0]["image"] = image
                    doc["spec"]["template"]["spec"]["nodeSelector"]["kubernetes.io/hostname"] = str(host)
                    doc["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["cpu"] = cpu_request
                    doc["spec"]["template"]["spec"]["containers"][0]["env"][0]["value"] = "{}_{}_{}".format(index + 1, 1, numProcesses)
                    if numContainers > 1:
                        for i in range(1, numContainers):
                            commad_add = f"FORCE_TIMES_TO_RUN=1 MONITOR=cpu.power,cpu.temp,cpu.usage TEST_RESULTS_NAME=TESTTEST{index + 1}_{i} ./phoronix-test-suite/phoronix-test-suite batch-run encode-flac-1.7.0; sshpass -p 'kienlu123' scp -r /var/lib/phoronix-test-suite/test-results/ kien@172.16.42.11:~/storage/"
                            name_file = f"{index + 1}_{i + 1}_{numProcesses}"
                            additional_container = {
                                "name": f"application{i + 1}",
                                "image": BENMARKING_IMAGE_NAME_x86,
                                "resources": {
                                    "limits": {
                                        "cpu": cpu_request
                                    }
                                },
                                "env": [
                                    {
                                        "name": "PORT",
                                        "value": str(8881 + i)
                                    },
                                    {
                                        "name": "FILE_NAME",
                                        "value": name_file
                                    }
                                ],
                                "command": ["python3"],
                                "args": [
                                    "main.py"
                                ]
                            }
                            doc["spec"]["template"]["spec"]["containers"].append(additional_container)
                    new_deployment.append(doc)
                    break

        with open(DEPLOYMENT_PATH, 'w') as yaml_file:
            yaml.dump_all(new_deployment, yaml_file, default_flow_style=False, sort_keys=False)
    except yaml.YAMLError as exc:
        print(exc)


import k8s_API
import os
import xml.etree.ElementTree as ET
import shutil

import os
import xml.etree.ElementTree as ET
import functional_methods
import json

def reach_benchmark_score(file_name: str):
    # Check the existence of the file
    if not os.path.exists(file_name):
        print(f"File '{file_name}' does not exist.")
        return False
    try:
        # Parse the XML file
        tree = ET.parse(file_name)
        root = tree.getroot()

        # Find all elements with the tag 'Value'
        values = root.findall(".//Value")

    # Print the value of the first element
        if values:
            return values[0].text
        else:
            print(f"File '{file_name}' does not have results.")
            return False
    except ET.ParseError as e:
        # Handle XML parsing errors
        print(f"Error parsing XML file '{file_name}': {e}")
        return False
    except Exception as e:
        # Handle other unexpected errors
        print(f"An error occurred while processing file '{file_name}': {e}")
        return False

def collect_benchmark_score(target_pods: int, target_containers: int, target_processes: int, measurement_type: str, event):
    host = "mec"
    remote_worker_call(DELETE_IMAGE_CMD, MEC_USERNAME, MEC_IP, MEC_PASSWORD)
    sleep(10)
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
    sleep(3)
    result_score = [float(reach_benchmark_score(file)) for file in file_benchmark_list]
    print(result_score)
    print("Measurement finished.")


    config_deploy("delete")
    command = "kubectl delete pod --all -n serverless --force --grace-period 0"
    output, error = functional_methods.execute_kubectl_command(command)

    while (k8s_API.get_number_pod(NAMESPACE) != 0):
        print("Waiting for pod to be terminated")
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

    event.set()
    print("Finished!")

def measure_response_time(architecture_type: str):
    """Measure the response time based on the type of architecture."""

    # Get the pod name
    pod_name = reach_pod_name(1)

    if architecture_type == "multiple_process":
        print("Measuring for MULTIPLE_PROCESS")

        # Execute the start command
        start_command = f"kubectl exec -it {pod_name} -n serverless -- curl http://127.0.0.1:8080/api/start"
        execute_kubectl_command(start_command)

        # Execute the response time command and parse the result
        response_time_command = f"kubectl exec -it {pod_name} -n serverless -- curl http://127.0.0.1:8080/api/response_time"
        result = execute_kubectl_command(response_time_command)
        response_time = json.loads(result[0].strip())['response_time']

    elif architecture_type == "multiple_container":
        print("Measuring for MULTIPLE_CONTAINER")

        # Get the IP of the pod
        pod_ip = reach_pod_ip(1)

        # Execute the active command and measure the response time
        active_command = f"kubectl exec -it {pod_name} -c application1 -n serverless -- curl http://{pod_ip}:8882/api/active"
        start_time = time.time()
        execute_kubectl_command(active_command)
        response_time = time.time() - start_time

    else:  # process_type == "multiple_pod"
        print("Measuring for MULTIPLE_POD")

        # Execute the active command and measure the response time
        active_command = f"kubectl exec -it {pod_name} -n serverless -- curl http://detection2.serverless.svc.cluster.local/api/active"
        start_time = time.time()
        execute_kubectl_command(active_command)
        response_time = time.time() - start_time

    return response_time


if __name__ == "__main__":
    measurement_type = MULTIPLE_PROCESS
     # Change
    MULTIPLE_PROCESS_IMAGE_NAME_X86 = "trourest186/multiple_process@sha256:70c4a7d9fd23a17e3e261f1c7ab727ee061db9547692e8bc4e6349fc10c6ac2e"
    # MULTIPLE_POD_IMAGE_NAME_X86 = "trourest186/multiple_pod"
    MULTIPLE_MIX_IMAGE_NAME_x86 = "trourest186/multiple_mix@sha256:8a09aac578fefd60887c1b5a5c5dcbd2ee359330e4a8e6f425d2570fe72655a8"
    IMAGE_NAME = MULTIPLE_PROCESS_IMAGE_NAME_X86

    repeat_time = 10
    current_time = 1

    node = 'mec'
    image = 'x86'

    list_quality = []   

    # ========================================================
    
    ## The parameters for testcase 1
    target_pods_scale = [1] # For multiple mix and multiple pod
    target_container_scale = 1 # For multiple_container

    # STREAMING_COUNT, COUNTAINER_COUNT

    ## The parameters for testcase 2
    budget_CPU = 4
    cases = case_set(budget_CPU)
    target_pod = 2
    # update_deployment(target_pod, IMAGE_NAME , node)
    # update_multi_container_deployment(target_pod, IMAGE_NAME, node)
    result = []
    for i in range(5):
        result.append(curl_type_processing(measurement_type))

    print(np.average(result))



    test = ('{"response_time":0.001497030258178711}\r\n', 'Defaulted container "user-container" out of: user-container, queue-proxy\n')




    # ar = [0.0, 17.088, 16.914, 17.021]
    # print(max(ar))
    # target_pods_scale = 2
    # # # image_error = "trourest186/httpserver_finalfix??"
    # image = "trourest186/multiple_mix"
    # host = "mec"
    # target_pods = 1
    # target_containers = 1
    # # update_deployment(target_pods_scale, image, host)
    # # # update_multi_mix_deployment(1, 1, 4, image, host)
    # # update_multi_container_deployment(2, image, host)
    # # # config_image(image)
    # # output_name = "No more frames. Exiting..."
    # # print()
    # # time.sleep(10)
    # start_time = time.time()
    # # while True:
    # #     # Change 3 parameters
    # #     output_func = lambda target_pod, count: [reach_pod_log(i+1, j+1, MULTIPLE_PROCESS) for i in range(target_pod) for j in range(count)]
    # #     if check_all_elements(output_func(target_pods, target_containers), MULTIPLE_PROCESS):
    # #         print("Correct")
    # #         break
    # #     else:
    # #         continue

    # print("=================================> Final result:" + str(end_time - start_time + 12))
