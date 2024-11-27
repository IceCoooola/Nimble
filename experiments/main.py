from create_vm import create_vms
from set_up_baseline import set_up_hadoop_baseline
from set_up_baseline import run_hadoop_baseline
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # create vms
    create_vms()
    # set up hadoop baseline. comment this line if do not need to set up baseline.
    set_up_hadoop_baseline()
    # uncomment this line if need to run hadoop baseline.
    # run_hadoop_baseline()




