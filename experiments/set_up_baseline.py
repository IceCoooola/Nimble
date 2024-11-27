import json
import os
import time


def set_up_node(ssh_base: str):
    commands = [
        # Download Hadoop
        f"{ssh_base} 'wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.3/hadoop-3.3.3.tar.gz -P /opt/'",

        # Extract and move Hadoop
        f"{ssh_base} 'sudo tar -xzvf /opt/hadoop-3.3.3.tar.gz -C /opt/'",
        f"{ssh_base} 'sudo mv /opt/hadoop-3.3.3 /opt/hadoop-upstream'",

        # Update and install OpenJDK 8
        f"{ssh_base} 'sudo apt update'",
        f"{ssh_base} 'sudo apt install -y openjdk-8-jdk'",

        # Set JAVA_HOME for current user and root
        f"{ssh_base} \"echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' | tee -a ~/.bashrc | sudo tee -a /root/.bashrc\"",
        f"{ssh_base} 'source ~/.bashrc'",

        # Change ownership of Hadoop installation
        f"{ssh_base} 'sudo chown -R `whoami` /opt/hadoop-upstream'",

        # Add Hadoop binaries to PATH
        f"{ssh_base} \"echo 'export PATH=$PATH:/opt/hadoop-upstream/bin' | tee -a ~/.bashrc | sudo tee -a /root/.bashrc\"",
        f"{ssh_base} 'source ~/.bashrc'",

        # Create and configure /mnt/store
        f"{ssh_base} 'sudo mkdir /mnt/store'",
        f"{ssh_base} 'sudo chown -R `whoami` /mnt/store'",

        # Create hdfs-site.xml
        f"""{ssh_base} "echo '\
    <?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?>\
    <?xml-stylesheet type=\\"text/xsl\\" href=\\"configuration.xsl\\"?>\
    <configuration>\
        <property>\
            <name>dfs.name.dir</name>\
            <value>/mnt/store/namenode</value>\
        </property>\
        <property>\
            <name>dfs.data.dir</name>\
            <value>/mnt/store/datanode</value>\
        </property>\
    </configuration>\
    ' | sudo tee /opt/hadoop-upstream/etc/hadoop/hdfs-site.xml\"""",

        # Create core-site.xml
        f"""{ssh_base} "echo '\
    <?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?>\
    <?xml-stylesheet type=\\"text/xsl\\" href=\\"configuration.xsl\\"?>\
    <configuration>\
        <property>\
            <name>fs.defaultFS</name>\
            <value>hdfs://<namenodeip>:9000</value>\
        </property>\
    </configuration>\
    ' | sudo tee /opt/hadoop-upstream/etc/hadoop/core-site.xml\""""
    ]

    # Execute each command
    for cmd in commands:
        print(cmd)
        os.system(cmd)


def set_up_hadoop_baseline():
    # set up namenode
    with open("namenode_baseline_output.json", "r") as file:
        vm_output = json.load(file)
        namenode_ip = vm_output.get("publicIpAddress")

    if not namenode_ip:
        raise ValueError("Public IP address not found in namenode_output.json")

    ssh_user = "cola"
    ssh_namenode = f"ssh {ssh_user}@{namenode_ip}"
    set_up_node(ssh_namenode)

    # set up datanode
    with open("datanode_baseline_output.json", "r") as file:
        vm_output = json.load(file)
        datanode_ip = vm_output.get("publicIpAddress")

    if not datanode_ip:
        raise ValueError("Public IP address not found in namenode_output.json")

    ssh_datanode = f"ssh {ssh_user}@{datanode_ip}"
    set_up_node(ssh_datanode)
    print("Setup completed.")


def run_hadoop_baseline():
    with open("namenode_baseline_output.json", "r") as file:
        vm_output = json.load(file)
        namenode_ip = vm_output.get("publicIpAddress")

    if not namenode_ip:
        raise ValueError("Public IP address not found in namenode_output.json")

    with open("datanode_baseline_output.json", "r") as file:
        vm_output = json.load(file)
        datanode_ip = vm_output.get("publicIpAddress")

    ssh_user = "cola"
    if not datanode_ip:
        raise ValueError("Public IP address not found in namenode_output.json")
    ssh_namenode = f"ssh {ssh_user}@{namenode_ip}"
    ssh_datanode = f"ssh {ssh_user}@{datanode_ip}"

    # format the namenode
    cmd = f"{ssh_namenode} 'sudo hdfs namenode -format'"
    print(cmd)
    os.system(cmd)
    # start namenode
    cmd = f"{ssh_namenode} 'sudo hdfs --daemon start namenode'"
    print(cmd)
    os.system(cmd)

    # start datanode
    cmd = f"{ssh_datanode} 'sudo hdfs --daemon start datanode'"
    print(cmd)
    os.system(cmd)
    # sleep 10 seconds to wait for namenode & datanode connection.
    time.sleep(10)

    THREADS = 64
    FILES = 500000
    DIRS = 500000
    operations = [
        ("create", f"-threads {THREADS} -files {FILES}"),
        ("mkdirs", f"-threads {THREADS} -dirs {DIRS}"),
        ("open", f"-threads {THREADS} -files {FILES}"),
        ("delete", f"-threads {THREADS} -files {FILES}"),
        ("fileStatus", f"-threads {THREADS} -files {FILES}"),
        ("rename", f"-threads {THREADS} -files {FILES}"),
        ("clean", ""),
    ]

    for op, params in operations:
        cmd = f"{ssh_namenode} 'hadoop org.apache.hadoop.hdfs.server.namenode.NNThroughputBenchmark -op {op} {params}'"
        print(f"Executing bench: {cmd}")
        os.system(cmd)
