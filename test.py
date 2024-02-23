# from time import sleep
# # from main import *
# from datetime import datetime
# from subprocess import call  
# import requests  
# import threading
# import re
# import string
# # import multiservice_pods

# pwd='1'
# cmd='kubectl apply -f /home/controller/knative-caculation/deployments/nginx-pod.yaml'
# video_path = "/test_video/highway.mp4"
# HELLO = "hello = {{'{}'}}"

# timestamps = {}
# terminate_state = defaultdict(list)

# def create_request(url: str):
#     print(url)
#     rs_response = requests.get(url)
#     print(rs_response.content)
#     # subprocess.call(['sh','./deployments/curl.sh'])

# def create_request_thread(target_pods: int):
#     video_path = "test_video/" + "highway.mp4"
#     for i in range(target_pods):
#         print("Start thread :", i + 1)
#         threading.Thread(target=create_request, args=("http://detection"+str(i+1)+".default.svc.cluster.local/{}".format(video_path),)).start()

# def exec(command:str):
#     subprocess.call('echo {} | sudo -S {}'.format(pwd, command), shell=True)

# def get_pod_status():
#     return str(subprocess.run(['deployments/get_pod_status.sh', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')).strip()
    
#     # print(re.search('\n(.*)\n', str(result)))
#     # return re.search('(.*)', str(result))

# def get_pods_existed():
#     timestamps["start"]=time.time()
#     url_server_running_pod = PROMETHEUS_DOMAIN + RUNNING_PODS_QUERY.format(CALCULATING_HOSTNAME)
#     timestamps["end"]=time.time()
#     # values_running_pods=json.loads(urllib.request.urlopen(url_server_running_pod).read())["data"]["result"][0]['value'][1]
#     # return int(values_running_pods)

# def is_pod_terminating():
#     status = str(subprocess.run(['deployments/get_pod_status.sh', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')).strip()
#     return status == TERMINATING_STATUS 

# def curl_time():
#     # Define the command to run
#     # cmd = "./myscript.sh https://www.google.com"

#     # Run the command and capture its output
#     output = subprocess.check_output(['curltime.sh', 'google.com'])

#     # Extract the values you're interested in from the output
#     time_pretransfer = float(output.split(b"time_pretransfer: ")[1].split(b" ")[0])
#     time_redirect = float(output.split(b"time_redirect: ")[1].split(b" ")[0])

#     # Store the values in a dictionary
#     times = {"time_pretransfer": time_pretransfer, "time_redirect": time_redirect}

#     # Print the dictionary
#     print(times)
from kubernetes import client, config
import subprocess
import random
import datetime
from time import sleep
import yaml
import re
from variables import *

def update_benchmark_deployment(numPods: int, numContainers: int, numProcesses: int, image: str, host: str, path_file_deploy: str = TEMPLATE_PATH2):
    try:
        new_deployment = []
        for index in range(0, numPods, 1 ):
            docs = list(yaml.load_all(open(path_file_deploy, "r"), Loader=yaml.SafeLoader))
            for doc in docs:
                if doc.get("apiVersion") == "serving.knative.dev/v1" and doc.get("kind") == "Service":
                    cpu_request = str(1000*numProcesses) + 'm'

                    doc["metadata"]["name"] = "detection" + str(index + 1)
                    doc["spec"]["template"]["metadata"]["annotations"]["autoscaling.knative.dev/window"] = "60s"
                    doc["spec"]["template"]["spec"]["containers"][0]["image"] = image
                    doc["spec"]["template"]["spec"]["nodeSelector"]["kubernetes.io/hostname"] = str(host)
                    doc["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["cpu"] = cpu_request
                    
                    # doc["spec"]["template"]["spec"]["containers"][0]["env"][0]["value"] = str(target_pods_scale)
                    if numContainers > 1:
                        for i in range(1, numContainers):
                            additional_container = {
                                "name": f"application{i + 1}",
                                "image": MULTIPLE_MIX_IMAGE_NAME_x86,
                                "resources": {
                                    "limits": {
                                        "cpu": cpu_request
                                    }
                                },
                                "env": [
                                    {
                                        "name": "PORT",
                                        "value": str(8881 + i)
                                    }
                                ],
                                "command": ["/bin/bash", "-c"],
                                "args": [
                                    f"FORCE_TIMES_TO_RUN=5 MONITOR=cpu.power,cpu.temp,cpu.usage TEST_RESULTS_NAME=TESTTEST{i+1} ./phoronix-test-suite/phoronix-test-suite batch-run encode-flac-1.7.0; sshpass -p 'kienlu123' scp -r /var/lib/phoronix-test-suite/test-results/ kien@172.16.42.11:~/storage/"
                                ]
                            }
                            doc["spec"]["template"]["spec"]["containers"].append(additional_container)
                    new_deployment.append(doc)
                    break

        with open(DEPLOYMENT_PATH, 'w') as yaml_file:
            yaml.dump_all(new_deployment, yaml_file, default_flow_style=False, sort_keys=False)
    except yaml.YAMLError as exc:
        print(exc)


import xml.etree.ElementTree as ET

def reach_benmarkscore(file_name: str):
# Đọc tệp XML
    tree = ET.parse(file_name)
    root = tree.getroot()

    # Tìm tất cả các mục có thẻ 'Value'
    values = root.findall(".//Value")

    # In giá trị của mục đầu tiên
    if values:
        return values[0].text
    else:
        print("Don't have results")


if __name__=="__main__":
    file_name =  '/home/kien/storage/test-results/testtest/composite.xml'
    giang = reach_benmarkscore(file_name)
    print(giang)