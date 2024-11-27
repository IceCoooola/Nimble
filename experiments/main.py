import os
from create_vm import create_vms
from set_up_baseline import set_up_hadoop_baseline
from set_up_nimble import set_up_nimble
from set_up_hadoop_nimble import set_up_hadoop_nimble, run_hadoop_nimble

from set_up_baseline import run_hadoop_baseline
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # create vms
    create_vms()

    # set up hadoop baseline. comment this line if you do not need to set up baseline.
    set_up_hadoop_baseline()
    # set up nimble. comment this line if you do not need to set up baseline.
    set_up_nimble()
    # set up hadoop-nimble. comment this line if you do not need to set up baseline.
    set_up_hadoop_nimble()

    # uncomment these line to run hadoop-nimble.
    # # start nimble memory.
    # os.system("python3 start_nimble_memory.py")
    # # run hadoop-nimble
    # run_hadoop_nimble()


    # uncomment this line if need to run hadoop baseline.
    # run_hadoop_baseline()




