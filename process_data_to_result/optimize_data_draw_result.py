from cProfile import label
from cmath import sin
from collections import defaultdict
import csv
import math
from tkinter.font import names
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import re

TARGET_PODS = "target_pods"
REPEAT_TIME = "repeat_time"
MEAN = "mean"
TIME_SECONDS = "time_seconds"
DATE_TIME = "date_time"
POD_NUM = "pod_num"
CPU_PER = "cpu_%"
RAM_PER = "ram_%"
POD_STATE = "pod_state"

folder = "pi4"
CALCULATION_TYPE = "revert_lifecircle"
data_by_day_folder = "20_7_2022"
data_directory = "D:\FIL\DATN\Data\\"+folder
output_data_dir = "D:\FIL\DATN\DataOptimize\\"+folder+"\\"
data_optimize_file = output_data_dir+"data_{}_{}_optimize_tmp.csv"

def remove_optimize_file(file_directory:str):
    if os.path.exists(file_directory):
      os.remove(file_directory)
    else:
        print("The file does not exist")

def get_dic_data(file_directory:str, data_type:str):
    data_pd = pd.read_csv(file_directory, sep=',', names=[TIME_SECONDS, DATE_TIME, POD_NUM, CPU_PER, RAM_PER, POD_STATE])
    data_arr = np.transpose(np.array([data_pd[POD_STATE], data_pd[data_type]]))
    dict_data = defaultdict(list)
    for key, value in data_arr:
        dict_data[key].append(value)
    data_mean_dic = defaultdict(list)
    for key, value in dict_data.items():
        data_mean_dic[key].append(sum(value)/len(value))
    return data_mean_dic

def get_state_mean_dic_data(file_directory:str):
    df = pd.read_csv(file_directory, sep=',', names=[TARGET_PODS, REPEAT_TIME, POD_STATE, MEAN])
    data_arr = df.to_numpy()
    state_dic = defaultdict(list)
    for target_pod, repeat_time, pod_state, mean in data_arr:
        state_dic[pod_state].append([target_pod, repeat_time, mean])
    state_mean_dic = defaultdict(list)
    for key, value in state_dic.items():
        repeat_mean_dic = defaultdict(list)
        for target_pod, rep, mean in value:
            repeat_mean_dic[target_pod].append(mean)
        mean_dic = defaultdict(list)
        for k, v in repeat_mean_dic.items():
            mean_dic[k].append(sum(v)/len(v))
        state_mean_dic[key].append(mean_dic)
    return state_mean_dic

def write_to_file(calculation_type:str ,data_type:str, target_pod:str, repeat_time:str, key:str, value:float):
    write = csv.writer(open(data_optimize_file.format(data_type,calculation_type), 'a', newline=''))
    write.writerow([target_pod,repeat_time,key,value])

def generate_optimize_data_files(data_directory:str, calculation_type:str):
    for filename in os.listdir(data_directory+"\\"+calculation_type):
        file_directory = os.path.join(data_directory+"\\"+calculation_type, filename)
        print(file_directory)
        # checking if it is a file
        if os.path.isfile(file_directory):
            target_pod = re.search('target_pod_(.*)_repeat',file_directory).group(1)
            repeat_time = re.search('repeat_time_(.*)_video',file_directory).group(1)[0]
            print("file_directory: ", file_directory, "target_pod: ", target_pod, "repeat_time: ", repeat_time)
            for key, value in get_dic_data(file_directory, CPU_PER).items():
                write_to_file(calculation_type, CPU_PER,target_pod,repeat_time,key,float(value[0]))
                # data_cpu_optimize.append([target_pod,repeat_time,key,str(value[0])])
            for key, value in get_dic_data(file_directory, RAM_PER).items():
                write_to_file(calculation_type, RAM_PER,target_pod,repeat_time,key,float(value[0]))
                # data_ram_optimize.append([target_pod,repeat_time,key,str(value[0])])

def mean_plot(data_type:str):
    dic = get_state_mean_dic_data(output_data_dir+"data_{}_optimize_tmp.csv".format(data_type))
    # state
    null_state = dic.get("begin")[0]
    warm_state = dic.get("warm")[0]
    cold_state = dic.get("cold")[0]
    active_state = dic.get("active")[0]

    state_arr = [[null_state.keys(), null_state.values()], [warm_state.keys(), warm_state.values()], [cold_state.keys(), cold_state.values()], [active_state.keys(), active_state.values()]]
    color = ["red", "orange", "green", "blue"]
    marker = ["v", ">", "s", "v",]
    labels = ["State:Null", "State:Warm", "State:Cold", "State:Active", ]

    x = np.arange(1,11,1)

    for i in range(len(state_arr)):
        x = np.array(list(state_arr[i][0]))
        y = np.array(list(state_arr[i][1]))
        print(x, y)
        a,b=np.polyfit(x,y,1)

        plt.scatter(x, y, color=color[i], marker=marker[i], label = labels[i])
        plt.plot(x,a*x+b, color=color[i])
        plt.yscale("log", base=2)
        plt.xticks(x)
        plt.xlabel("Number of Pods")
        plt.ylabel("{} state {} usage (log2)".format(folder,data_type))
    # plt.scatter(dic.keys()[0],dic.values())
    # plt.scatter(null_state.keys(), null_state.values(), label="State:Null")
    # plt.scatter(warm_state.keys(), warm_state.values(), label="State:Warm")
    # plt.scatter(cold_state.keys(), cold_state.values(), label="State:Cold")
    # plt.scatter(active_state.keys(), active_state.values(), label="State:Active")

    plt.legend()
    plt.show()


def boxplot_state(data_type:str, calculation_type:str):
    df = pd.read_csv(output_data_dir+"data_{}_{}_optimize_tmp.csv".format(data_type, calculation_type), sep=',', names=[TARGET_PODS, REPEAT_TIME, POD_STATE, MEAN])
    # df = pd.DataFrame(arr_data,columns=[TARGET_PODS, REPEAT_TIME, POD_STATE, MEAN])
    df = df.sort_values(by=TARGET_PODS)

    df_null = df[df[POD_STATE]=="begin"]
    df_null = df_null.sort_values(by=TARGET_PODS)

    df_cold = df[df[POD_STATE]=="cold"]
    df_cold = df_cold.sort_values(by=TARGET_PODS)

    df_warm = df[df[POD_STATE]=="warm"]
    df_warm = df_warm.sort_values(by=TARGET_PODS)

    df_active = df[df[POD_STATE]=="active"]
    df_active = df_active.sort_values(by=TARGET_PODS)

    plt.figure()

    arr = [df_null, df_warm, df_cold, df_active]
    # print(arr)
    i=0
    color = ["red", "orange", "green", "blue"]

    marker = ["v", ">", "s", "v",]

    labels = ["State:Null", "State:Warm", "State:Cold", "State:Active", ]

    # color = ["red", "orange", "yellow", "green", "blue", "violet", "black"]

    # marker = ["v", ">", "s", "v", ">", "s", "v"]

    # labels = ["Cold", "Cold to Warm", "Cold to Warm Ter", "Warm", "Active", "Active Ter" ,"Terminate"]

    for scenario in arr:
        # plt.subplot(1, 1, i+1)
        plt.subplot(1, 1, 1)

        draw_box = scenario[[TARGET_PODS, MEAN]]
        
        list_pods = np.unique(df[TARGET_PODS])
        ticks= [str(e) for e in list_pods]
        x_positions = list(range(0, len(ticks)))

        # for pod in list_pods:
        #     draw_i = draw_box[draw_box[TARGET_PODS] == pod]

        #     if(len(draw_i) != 0):
        #         plt.boxplot(draw_i[MEAN], positions=[ticks.index(str(pod))], widths=0.5, patch_artist=True, boxprops=dict(facecolor='white'))
                
        plt.xticks(x_positions, ticks)

        plt.xlabel("Number of Pods")
        plt.yscale("log",base=2)
        plt.ylabel("{} state {} usage".format(folder,data_type))
        
        if i==0:xx=1
        elif i==1: xx=1
        elif i==2: xx=2
        elif i==3: xx=3
        # elif i==4: xx=4
        
        my_fitting = np.polyfit(scenario[TARGET_PODS], scenario[MEAN], xx, full=True)
        poly = np.poly1d(my_fitting[0])
        plt.plot(scenario[TARGET_PODS].astype(str), poly(scenario[TARGET_PODS]), color=color[i],  marker=marker[i], label = labels[i])

        print(my_fitting[0])
        i = i + 1

    # legend
    # handles, labels = plt.gca().get_legend_handles_labels()
    # red_patch = mpatches.Patch(color='red', label='The red data')
    plt.legend()
    result_image_dir = "result\{}\{}\{} state {}_{}.jpg"
    plt.savefig(result_image_dir.format(data_by_day_folder,folder,calculation_type,data_type,data_by_day_folder))
    plt.show()
    # remove_optimize_file(data_optimize_file.format(data_type))

def boxplot_action(data_type:str, calculation_type:str):
    df = pd.read_csv(output_data_dir+"data_{}_{}_optimize_tmp.csv".format(data_type, calculation_type), sep=',', names=[TARGET_PODS, REPEAT_TIME, POD_STATE, MEAN])
    # df = pd.DataFrame(arr_data,columns=[TARGET_PODS, REPEAT_TIME, POD_STATE, MEAN])
    df = df.sort_values(by=TARGET_PODS)

    df_deploy = df[df[POD_STATE]=="cold_start"]
    df_deploy = df_deploy.sort_values(by=TARGET_PODS)

    df_scale_down = df[df[POD_STATE]=="warm:terminating"]
    df_scale_down = df_scale_down.sort_values(by=TARGET_PODS)

    df_curl = df[df[POD_STATE]=="cold_start:curl"]
    df_curl = df_curl.sort_values(by=TARGET_PODS)

    df_delete = df[df[POD_STATE]=="delete:terminating"]
    df_delete = df_delete.sort_values(by=TARGET_PODS)

    # Revert Actions
    df_warm_curl = df[df[POD_STATE]=="cold_start:curl"]
    df_warm_curl = df_warm_curl.sort_values(by=TARGET_PODS)

    df_cooling = df[df[POD_STATE]=="active:terminating"]
    df_cooling = df_cooling.sort_values(by=TARGET_PODS)

    df_update = df[df[POD_STATE]=="cold_start:update_config"]
    df_update = df_update.sort_values(by=TARGET_PODS)

    df_warm_delete = df[df[POD_STATE]=="warm_delete:terminating"]
    df_warm_delete = df_warm_delete.sort_values(by=TARGET_PODS)

    df_cold_delete = df[df[POD_STATE]=="cold_delete"]
    df_cold_delete = df_cold_delete.sort_values(by=TARGET_PODS)

    plt.figure()

    arr = []
    labels = []
    if calculation_type == "life_circle":
        arr = [df_deploy, df_scale_down, df_curl, df_delete]
        labels = ["Action:Deploying", "Action:Scaling down", "Action:Curling", "Action:Force delete", ]
    else:
        arr = [df_warm_curl, df_cooling, df_update, df_warm_delete, df_cold_delete]
        labels = ["Action:WarmCurling", "Action:Cooling", "Action:Updating", "Action:Warm deleting", "Action:Cold deleting"]
    print(arr[1], arr[2])
    i=0
    color = ["red","violet", "green", "blue","orange" ,]

    marker = ["v", ">", "s", "v", ">", "s", "v"]

    # color = ["red", "orange", "yellow", "green", "blue", "violet", "black"]

    # marker = ["v", ">", "s", "v", ">", "s", "v"]

    # labels = ["Cold", "Cold to Warm", "Cold to Warm Ter", "Warm", "Active", "Active Ter" ,"Terminate"]

    for scenario in arr:
        # plt.subplot(1, 1, i+1)
        plt.subplot(1, 1, 1)

        draw_box = scenario[[TARGET_PODS, MEAN]]
        
        list_pods = np.unique(df[TARGET_PODS])
        ticks= [str(e) for e in list_pods]
        x_positions = list(range(0, len(ticks)))

        # for pod in list_pods:
        #     draw_i = draw_box[draw_box[TARGET_PODS] == pod]

        #     if(len(draw_i) != 0):
        #         plt.boxplot(draw_i[MEAN], positions=[ticks.index(str(pod))], widths=0.5, patch_artist=True, boxprops=dict(facecolor='white'))
                
        plt.xticks(x_positions, ticks)

        plt.xlabel("Number of Pods")
        plt.yscale("log",base=2)
        plt.ylabel("{} action {} usage".format(folder,data_type))
        
        if i==0:xx=1
        elif i==1: xx=1
        elif i==2: xx=2
        # elif i==3: xx=3
        # elif i==4: xx=4
        
        my_fitting = np.polyfit(scenario[TARGET_PODS], scenario[MEAN], 1, full=True)
        print(my_fitting)
        poly = np.poly1d(my_fitting[0])
        plt.plot(scenario[TARGET_PODS].astype(str), poly(scenario[TARGET_PODS]), color=color[i],  marker=marker[i], label = labels[i])

        print(my_fitting[0])
        i = i + 1

    plt.legend()
    result_image_dir = "result\{}\{}\{}_{}_action_{}_{}.jpg"
    plt.savefig(result_image_dir.format(data_by_day_folder,calculation_type,folder,calculation_type,data_type,data_by_day_folder))
    plt.show()
    remove_optimize_file(data_optimize_file.format(data_type, calculation_type))

if __name__=='__main__':
    generate_optimize_data_files(data_directory+"\\"+data_by_day_folder, CALCULATION_TYPE)
    # boxplot_state(CPU_PER)
    # boxplot_state(RAM_PER)
    boxplot_action(CPU_PER, CALCULATION_TYPE)
    boxplot_action(RAM_PER, CALCULATION_TYPE)
    # mean_plot(CPU_PER)
