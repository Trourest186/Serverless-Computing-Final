import time
import main
import variables
from multiprocessing import Event, Process
from k8s_API import update_deployment, update_multi_container_deployment
import functional_methods
# import merge
import sys

if __name__ == "__main__":
    
    target_pods_scale = [2]
    target_container_scale = 1
    repeat_time = 1
    current_time = 1

    # streaming_count = 3
    # node = 'jetson'
    node = 'mec'
    # image = 'arm';
    image = 'x86'

    # list_quality = ["360P", "480P", "HD", "2K", "4K"]
    list_quality = []

    # list video: highway.mp4, 4K_video_59s.webm, traffic_34s.webm, video.mp4
    # target_video = "highway.mp4"
    # detection_image = ""

    for target_pod in target_pods_scale:
        update_deployment(target_pod, "null", node) # Update number of deployment according to target_pod, Giang fix
        # update_multi_container_deployment(target_pod, "null", node)
        print("Deployment has been updated to {} pods".format(target_pod))
        for rep in range(current_time, repeat_time + 1, 1):
            print("Target pod: {}, Repeat time: {}/{}, Instance: {}".format(target_pod,
                  rep, repeat_time, node))
            variables.reload()  # reset all variables
            event = Event()  # the event is unset when created
            p0 = Process(target=functional_methods.auto_delete, args=(target_pod, event, ))
            p0.start()
            # main.curl_latency(node, image, list_quality, int(target_pod), int(rep), event)
            # time.sleep(20)
            # main.collect_life_cycle(node, image, int(target_pod), int(rep), event)
            # main.collect_cold_warm_disk(node, image, int(target_pod), int(rep), event)

            main.curl_complete_task(int(target_pod), int(target_container_scale), event)

            p0.join()
            time.sleep(20)
            # p1 = Process(target=collect_life_cycle, args=(event, int(target_pods_scale), repeat_time, ), daemon = True)
            # print("Start calculate")
            # p1.start()

            # cmd = '/usr/bin/python3 ' + DEFAULT_DIRECTORY +'/main_rebuild.py {} {} {}'.format(str(target_pod),  str(rep), str(instance))
            # process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    # event.set()
