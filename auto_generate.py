import time
import main
import variables
from multiprocessing import Event, Process
from k8s_API import update_deployment, update_multi_container_deployment, update_multi_mix_deployment, update_benchmark_deployment
import functional_methods
# import merge
import sys
from variables import *
from functional_methods import *

if __name__ == "__main__":
    ## General
    measurement_type = MULTIPLE_POD # Change

    repeat_time = 5
    current_time = 1

    node = 'mec'
    image = 'x86'

    list_quality = []   

    # ========================================================
    
    ## The parameters for testcase 1
    target_pods_scale = [6] # For multiple mix and multiple pod
    target_container_scale = 1 # For multiple_container

    # STREAMING_COUNT, COUNTAINER_COUNT

    ## The parameters for testcase 2
    budget_CPU = 4
    cases = case_set(budget_CPU)


    for target_pod in target_pods_scale:
        update_deployment(target_pod, "null", node)
        # update_multi_container_deployment(target_pod, "null", node)

        # 1-1-4, 1-2-2, 1-4-1, 2-1-2, 2-2-1, 4-1-1
        index_case = 2# Start 0 - 1th 
        # update_multi_mix_deployment(int(cases[index_case][0]), int(cases[index_case][1]), int(cases[index_case][2]), "null", node)
        # update_benchmark_deployment(int(cases[index_case][0]), int(cases[index_case][1]), int(cases[index_case][2]), image, node)

        print("Deployment has been updated to {} pods".format(target_pod))
        # print("Measurement for the case: {} pods - {} containers - {} processes".format(int(cases[index_case][0]), int(cases[index_case][1]), int(cases[index_case][2])))   

        for rep in range(current_time, repeat_time + 1, 1):
            print("Target pod: {}, Repeat time: {}/{}, Instance: {}".format(target_pod,
                  rep, repeat_time, node))
            variables.reload()  # reset all variables
            event = Event()  # the event is unset when created

            #======================================= For testcase 1 ============================================
            p0 = Process(target=functional_methods.auto_delete, args=(target_pod, event, ))
            p0.start()
            # main.collect_life_cycle(node, image, int(target_pod), int(rep), event)
            # main.curl_latency(node, image, list_quality, int(target_pod), int(rep), event)
            # main.curl_complete_task(int(target_pod), int(target_container_scale), measurement_type, event)
            main.collect_cold_warm_disk(node, image, int(target_pod), int(rep), event)

            #======================================= For testcase 2 ============================================
            # Revising for only a case in testcase2's cases

            # p0 = Process(target=functional_methods.auto_delete, args=(cases[index_case][0], event, ))
            # p0.start()
            # # main.collect_life_cycle(node, image, int(cases[index_case][0]), int(rep), event)
            # # main.curl_complete_task(int(cases[index_case][0]), int(cases[index_case][1]), int(cases[index_case][2]), measurement_type, event)
            # # main.collect_cold_warm_disk(node, image, int(cases[index_case][0]), int(rep), event)
            # main.curl_latency(node, image, list_quality, int(cases[index_case][0]), int(rep), event)

            #======================================= For testcase 3 ============================================
            # Revising for only a case in testcase2's cases

            # p0 = Process(target=functional_methods.auto_delete, args=(cases[index_case][0], event, ))
            # p0.start()
            # # main.collect_life_cycle(node, image, int(cases[index_case][0]), int(rep), event)
            # # main.curl_complete_task(int(cases[index_case][0]), int(cases[index_case][1]), int(cases[index_case][2]), measurement_type, event)
            # # main.collect_cold_warm_disk(node, image, int(cases[index_case][0]), int(rep), event)
            # main.curl_latency(node, image, list_quality, int(cases[index_case][0]), int(rep), event)
            # main.collect_benchmark_score(int(cases[index_case][0]), int(cases[index_case][1]))
            # =========================================END======================================================
            p0.join()
            time.sleep(20)
            # p1 = Process(target=collect_life_cycle, args=(event, int(target_pods_scale), repeat_time, ), daemon = True)
            # print("Start calculate")
            # p1.start()

            # cmd = '/usr/bin/python3 ' + DEFAULT_DIRECTORY +'/main_rebuild.py {} {} {}'.format(str(target_pod),  str(rep), str(instance))
            # process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
