import paramiko
import os
import time
from config import SSH_USER, SSH_IP_NAMENODE_NIMBLE, PRIVATE_IP_NAMENODE_NIMBLE, PRIVATE_IP_DATANODE_NIMBLE, SSH_IP_DATANODE_NIMBLE, LISTEN_IP_LOAD_BALANCER


# Commands to execute
commands = [
    "git clone https://github.com/IceCoooola/hadoop-nimble",
    "chmod +x ~/hadoop-nimble/install_deps.sh",
    "sudo ~/hadoop-nimble/install_deps.sh",
    "cd ~/hadoop-nimble && sudo mvn package -Pdist -DskipTests -Dtar -Dmaven.javadoc.skip=true",
    "sudo apt install -y openjdk-8-jdk",
    "echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' | tee -a ~/.bashrc | sudo tee -a /root/.bashrc",
    "source ~/.bashrc",
    "sudo tar -xvf ~/hadoop-nimble/hadoop-dist/target/hadoop-3.3.3.tar.gz -C /opt",
    "sudo mv /opt/hadoop-3.3.3 /opt/hadoop-nimble",
    "sudo chown -R $(whoami) /opt/hadoop-nimble",
    "echo 'export PATH=$PATH:/opt/hadoop-nimble/bin' | tee -a ~/.bashrc | sudo tee -a /root/.bashrc",
    "source ~/.bashrc",
    "sudo mkdir /mnt/store",
    "sudo chown -R $(whoami) /mnt/store",
    "echo '\
<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
<?xml-stylesheet type=\"text/xsl\" href=\"configuration.xsl\"?>\n\
<configuration>\n\
    <property>\n\
        <name>dfs.name.dir</name>\n\
        <value>/mnt/store/namenode</value>\n\
    </property>\n\
    <property>\n\
        <name>dfs.data.dir</name>\n\
        <value>/mnt/store/datanode</value>\n\
    </property>\n\
</configuration>\n' | sudo tee /opt/hadoop-nimble/etc/hadoop/hdfs-site.xml",
    f"echo '\
<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
<?xml-stylesheet type=\"text/xsl\" href=\"configuration.xsl\"?>\n\
<configuration>\n\
    <property>\n\
        <name>fs.defaultFS</name>\n\
        <value>hdfs://{PRIVATE_IP_NAMENODE_NIMBLE}:9000</value>\n\
    </property>\n\
    <property>\n\
        <name>fs.nimbleURI</name>\n\
        <value>http://{LISTEN_IP_LOAD_BALANCER}:8082/</value>\n\
    </property>\n\
    <property>\n\
        <name>fs.nimble.batchSize</name>\n\
        <value>100</value>\n\
    </property>\n\
</configuration>\n' | sudo tee /opt/hadoop-nimble/etc/hadoop/core-site.xml",
]

def config_hadoop_nimble_vm(host, user, commands) -> (str, str):
    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host, username=user)

        for cmd in commands:
            print(f"Running command: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.channel.recv_exit_status()  # Wait for the command to complete
            output = stdout.read().decode()
            error = stderr.read().decode()
            print(f"Output:\n{output}")
            if error:
                print(f"Error:\n{error}")

        # get the hostname and hostname_f
        print("Running: hostname")
        stdin, stdout, stderr = ssh.exec_command("hostname")
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        hostname = stdout.read().decode().strip()
        print("Running: hostname -f")
        stdin, stdout, stderr = ssh.exec_command("hostname -f")
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        hostname_f = stdout.read().decode().strip()
        return (hostname, hostname_f)
    except Exception as e:
        print(f"Failed to execute commands on {host}: {e}")
    finally:
        ssh.close()


def update_hosts_file(sshnode_ip, user, host_private_ip, hostname, hostname_f):
    # Format the new line to be added to /etc/hosts
    hosts_entry = f"{host_private_ip} {hostname} {hostname_f}"

    # SSH command to append the line to /etc/hosts
    command = f"echo '{hosts_entry}' | sudo tee -a /etc/hosts"

    # SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to Node at {sshnode_ip}")
        ssh.connect(hostname=sshnode_ip, username=user)

        print(f"Updating /etc/hosts on DataNode...")
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Wait for the command to complete

        # Capture output and errors
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if output:
            print(f"Output:\n{output}")
        if error:
            print(f"Error:\n{error}")

        print("Update complete.")
    except Exception as e:
        print(f"Failed to update /etc/hosts on {sshnode_ip}: {e}")
    finally:
        ssh.close()

def set_up_hadoop_nimble():
    (namenode_hostname, namenode_hostname_f) = config_hadoop_nimble_vm(SSH_IP_NAMENODE_NIMBLE, SSH_USER, commands)
    (datanode_hostname, datanode_hostname_f) = config_hadoop_nimble_vm(SSH_IP_DATANODE_NIMBLE, SSH_USER, commands)
    update_hosts_file(SSH_IP_NAMENODE_NIMBLE, SSH_USER, PRIVATE_IP_DATANODE_NIMBLE, datanode_hostname, datanode_hostname_f)
    update_hosts_file(SSH_IP_DATANODE_NIMBLE, SSH_USER, PRIVATE_IP_NAMENODE_NIMBLE, namenode_hostname, namenode_hostname_f)

def run_hadoop_nimble():
    ssh_namenode = f"ssh {SSH_USER}@{SSH_IP_NAMENODE_NIMBLE}"
    ssh_datanode = f"ssh {SSH_USER}@{SSH_IP_DATANODE_NIMBLE}"

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
