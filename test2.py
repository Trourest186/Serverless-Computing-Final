import yaml
import os
import subprocess
import time
DEFAULT_DIRECTORY = os.getcwd()
DEPLOYMENT_PATH = DEFAULT_DIRECTORY + "/deploy.yaml"
TEMPLATE_PATH2 = DEFAULT_DIRECTORY + "/template2.yaml"
from variables import *

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

# def reach_pod_log(detection_number):
#     pod_name = reach_pod_name(detection_number)

#     command = f""
#     output, error = execute_kubectl_command(command)
#     return output

def reach_pod_log(detection_number, container_number):
    pod_name = reach_pod_name(detection_number)

    command = f"kubectl logs {pod_name} -n serverless -c application{container_number} | tail -n 1"
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
def check_all_elements(array):
    for element in array:
        if 'No more frames.' not in element:
            return False
    return True

if __name__ == "__main__":
    target_pods_scale = 2
    # # image_error = "trourest186/httpserver_finalfix??"
    image = "trourest186/multiple_mix"
    host = "mec"
    
    # update_deployment(target_pods_scale, image, host)
    # # update_multi_mix_deployment(1, 1, 4, image, host)
    # update_multi_container_deployment(2, image, host)
    # # config_image(image)
    # output_name = "No more frames. Exiting..."
    # print()
    time.sleep(10)
    start_time = time.time()
    while True:
        output_func = lambda count: [reach_pod_log(1, i+1) for i in range(count)]
        if check_all_elements(output_func(CONTAINER_COUNT)):
            print("Correct")
            break
        else:
            continue
    end_time = time.time()
    print("=================================> Final result:" + str(end_time - start_time + 12))
    
