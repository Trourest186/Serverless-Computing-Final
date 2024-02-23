import subprocess as sb
import os

path = os.getcwd()

def switchOnOffContainerFreeze(turn=False, address='172.16.42.10'):
    if (turn == False):
        sb.run(['/bin/bash', path + '/warm_mem.sh','$HOST_IP'])

    else:
        print("Turn On")
        sb.run(['/bin/bash','warm_mem.sh',address])


switchOnOffContainerFreeze(True)