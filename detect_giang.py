import subprocess
import threading
import time
from multiprocessing import Process, Pipe
import multiprocessing
def execute_kubectl_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output, error

def execute_curl_command(ip, port, time_detect, port_app):
    # curl_command = f"kubectl exec -it ubuntu -- curl http://detection1.serverless.svc.cluster.local/api/stream/active/{ip}:{port}/{time_detect}"
    # curl_command = f"kubectl exec -it ubuntu -- curl http://detection1.serverless.svc.cluster.local/api/stream/{ip}:{port}/{time_detect}/0"
    curl_command = f"kubectl exec -it ubuntu -- curl http://10.244.2.141:{port_app}/api/stream/active/{ip}:{port}/{time_detect}"
    output, error = execute_kubectl_command(curl_command)

    if output:
        print(f"Command output: {output.decode()}")
    if error:
        print(f"Command error: {error.decode()}")

def main():
    # Thông số của câu lệnh curl
    ip = "172.16.42.13"
    start_port = 1935
    # start_port = 12346
    num_threads = 3 # Số lượng luồng
    time_detect = 200
    port_app = 8880
    # port_app = 8080
    count = 0

    # Tạo và khởi chạy các luồng
    threads = []
    for i in range(num_threads):
        port = start_port
        # start_port = start_port + 2
        # port = start_port
        # count = count + i
        port_app = port_app + 1 # For multiple_container
        # thread = threading.Thread(target=execute_curl_command, args=(ip, port, time_detect, port_app, ))
        thread = multiprocessing.Process(target=execute_curl_command, args=(ip, port, time_detect, port_app, ))
        thread.start()

    # # Chờ tất cả các luồng hoàn thành
    # for thread in threads:
    #     thread.join()

if __name__ == "__main__":
    main()
