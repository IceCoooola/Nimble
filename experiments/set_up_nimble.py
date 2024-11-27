import paramiko
import time

# Import IP addresses and SSH user from config
from config import *

ips = [
    SSH_IP_ENDORSER_1,
    SSH_IP_ENDORSER_2,
    SSH_IP_ENDORSER_3,
    SSH_IP_COORDINATOR,
    SSH_IP_ENDPOINT_1,
    SSH_IP_ENDPOINT_2,
]

# Commands to execute on each machine
commands = [
    "sudo apt update",
    "sudo apt install -y make gcc libssl-dev pkg-config perl protobuf-compiler",
    "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",  # Install Rust
    "source $HOME/.cargo/env",  # Source Rust environment
    "git clone https://github.com/Microsoft/Nimble",  # Clone Nimble repo
    "cd Nimble && cargo build --release",  # Build Nimble
]

def run_ssh_commands(ip, user, commands):
    """SSH into a server and run commands."""
    print(f"Connecting to {ip}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=ip, username=user)
        for cmd in commands:
            print(f"Running command on {ip}: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.channel.recv_exit_status()  # Wait for command to complete
            output = stdout.read().decode()
            error = stderr.read().decode()
            print(f"Output:\n{output}")
            if error:
                print(f"Error:\n{error}")
    except Exception as e:
        print(f"Failed to connect to {ip}: {e}")
    finally:
        ssh.close()

def set_up_nimble():
    for ip in ips:
        run_ssh_commands(ip, SSH_USER, commands)
        print(f"Finished execution on {ip}")
        time.sleep(5)  # wait 5 sec between switching the machines.
