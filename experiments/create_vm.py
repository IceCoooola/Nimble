import os

resource_group = "nimble"
location = "WestUS"
number_of_endorsers = 3
username = "cola"
number_of_endpoints = 2
address_prefix = "22.22.22.0/24"
subnet_prefix = "22.22.22.0/24"
lb_port = "8080"

# this function will create resource group, vnet, load balancer, and all the vms it need.
# called once then all the vms will be created.
def create_vms():
    create_resource_group()
    create_vnet()
    create_load_balancer()
    create_edorsers()
    create_coordinator()
    create_endpoint()
    create_namenode_nimble()
    create_datanode_nimble()

    create_namenode_baseline()
    create_datanode_baseline()


def create_resource_group():
    cmd_create_group = f"az group create --name {resource_group} --location {location}"
    # create resource group
    print(cmd_create_group)
    os.system(cmd_create_group)


def create_vnet():
    cmd = cmd_create_vnet(resource_group, location, address_prefix, subnet_prefix)
    print(cmd)
    os.system(cmd)
    cmd = cmd_create_NSG(resource_group)
    print(cmd)
    os.system(cmd)


def create_edorsers():
    # create endorsers
    for i in range(number_of_endorsers):
        cmd = cmd_create_endorser(i + 1, resource_group, location, username)
        print(cmd)
        os.system(cmd)


def create_coordinator():
    cmd = cmd_create_coordinator(resource_group, location, username)
    print(cmd)
    os.system(cmd)


def create_load_balancer():
    # create load balancer ip
    cmd = cmd_create_load_balancer_ip(resource_group)
    print(cmd)
    os.system(cmd)
    # create load balancer
    cmd = cmd_create_load_balancer(resource_group)
    print(cmd)
    os.system(cmd)
    # create load balancer health probe
    cmd = cmd_create_lb_health_probe(resource_group, lb_port)
    print(cmd)
    os.system(cmd)
    # create load balancer rule
    cmd = cmd_create_lb_rule(resource_group, lb_port)
    print(cmd)
    os.system(cmd)


def create_endpoint():
    for i in range(number_of_endpoints):
        cmd = cmd_create_nic(resource_group, i+1)
        print(cmd)
        os.system(cmd)
        cmd = cmd_create_endpoints(resource_group, i + 1, location, username)
        print(cmd)
        os.system(cmd)
        # add endpoint to load balancer backend address pool
        cmd = cmd_lb_add_vm_pool(resource_group, i + 1)
        print(cmd)
        os.system(cmd)


def create_namenode_baseline():
    cmd = cmd_create_namenode_baseline(resource_group, location, username)
    print(cmd)
    os.system(cmd)


def create_datanode_baseline():
    cmd = cmd_create_datanode_baseline(resource_group, location, username)
    print(cmd)
    os.system(cmd)


def create_namenode_nimble():
    cmd = cmd_create_namenode_nimble(resource_group, location, username)
    print(cmd)
    os.system(cmd)


def create_datanode_nimble():
    cmd = cmd_create_datanode_nimble(resource_group, location, username)
    print(cmd)
    os.system(cmd)


def cmd_create_vnet(resource_group: str, location: str, address_prefix: str, subnet_prefix: str) -> str:
    return f"az network vnet create \
      --resource-group {resource_group} \
      --location {location} \
      --name {resource_group}-vnet \
      --address-prefix {address_prefix} \
      --subnet-name {resource_group}-subnet \
      --subnet-prefix {subnet_prefix}"


def cmd_create_NSG(resource_group: str) -> str:
    return f"az network nsg create --resource-group {resource_group} --name {resource_group}-NSG"


def cmd_create_endorser(n: int, resource_group: str, location: str, username: str) -> str:
    # create endorser n.
    return f"az vm create \
            --resource-group {resource_group} \
            --name endorser{n} \
            --image Canonical:ubuntu-24_04-lts:cvm:latest \
            --size Standard_DC16as_v5 \
            --location {location} \
            --vnet-name {resource_group}-vnet \
            --subnet {resource_group}-subnet \
            --admin-username {username} \
            --security-type ConfidentialVM \
            --os-disk-delete-option Delete \
            --os-disk-security-encryption-type VMGuestStateOnly \
            --generate-ssh-keys | tee endorser{n}_output.json"


def cmd_create_coordinator(resource_group: str, location: str, username: str) -> str:
    # create coordinator
    return f"az vm create  \
             --resource-group {resource_group} \
            --name coordinator \
            --image Ubuntu2204 \
            --size Standard_D16as_v5 \
            --location {location} \
            --vnet-name {resource_group}-vnet \
            --subnet {resource_group}-subnet \
            --admin-username {username} \
            --os-disk-delete-option Delete \
            --generate-ssh-keys | tee -a coordinator_output.json"


def cmd_create_nic(resource_group: str, n: int) -> str:
    return f"az network nic create \
        --resource-group {resource_group} \
        --name {resource_group}-nic-{n} \
        --vnet-name {resource_group}-vnet \
        --subnet {resource_group}-subnet \
        --network-security-group {resource_group}-NSG"


def cmd_create_endpoints(resource_group: str, n: int, location: str, username: str) -> str:
    return f"az vm create \
          --resource-group {resource_group} \
          --name endpoint{n} \
          --image Ubuntu2204 \
          --size Standard_D8as_v5 \
          --nics {resource_group}-nic-{n} \
          --location {location} \
          --admin-username {username} \
         --os-disk-delete-option Delete \
         --generate-ssh-keys | tee -a endpoint{n}_output.json"


def cmd_create_load_balancer_ip(resource_group: str) -> str:
    return f"az network public-ip create \
            --resource-group {resource_group} \
            --name {resource_group}_PublicIP_load_balancer \
            --sku Standard \
            --allocation-method Static | tee -a load_balancer_ip_output.json"


def cmd_create_load_balancer(resource_group: str) -> str:
    return f"az network lb create \
              --resource-group {resource_group} \
              --name {resource_group}_load_balancer \
              --sku Standard \
              --frontend-ip-name {resource_group}_frontend_ip \
              --backend-pool-name {resource_group}_load_balancer_back_end_pool \
              --public-ip-address {resource_group}_PublicIP_load_balancer"


def cmd_create_lb_health_probe(resource_group: str, port: str) -> str:
    return f"az network lb probe create \
            --resource-group {resource_group} \
            --lb-name {resource_group}_load_balancer \
            --name {resource_group}_probe \
            --protocol tcp \
            --port {port}"


def cmd_create_lb_rule(resource_group: str, port: str) -> str:
    return f"az network lb rule create \
        --resource-group {resource_group} \
        --lb-name {resource_group}_load_balancer \
        --name {resource_group}_rule \
        --protocol tcp \
        --frontend-port {port} \
        --backend-port {port} \
        --frontend-ip-name {resource_group}_frontend_ip \
        --backend-pool-name {resource_group}_load_balancer_back_end_pool \
        --probe-name {resource_group}_probe \
        --disable-outbound-snat true \
        --idle-timeout 15 \
        --enable-tcp-reset true"


def cmd_lb_add_vm_pool(resource_group: str, n: int) -> str:
    return f"az network nic ip-config address-pool add \
         --address-pool {resource_group}_load_balancer_back_end_pool \
         --ip-config-name ipconfig1 \
         --nic-name {resource_group}-nic-{n} \
         --resource-group {resource_group} \
         --lb-name {resource_group}_load_balancer"


def cmd_create_namenode_baseline(resource_group: str, location: str, username: str) -> str:
    # create coordinator
    return f"az vm create  \
             --resource-group {resource_group} \
            --name namenode_baseline \
            --image Ubuntu2204 \
            --size Standard_F16s_v2 \
            --location {location} \
            --vnet-name {resource_group}-vnet \
            --subnet {resource_group}-subnet \
            --admin-username {username} \
            --os-disk-delete-option Delete \
            --generate-ssh-keys | tee -a namenode_baseline_output.json"


def cmd_create_datanode_baseline(resource_group: str, location: str, username: str) -> str:
    # create coordinator
    return f"az vm create  \
             --resource-group {resource_group} \
            --name datanode_baseline \
            --image Ubuntu2204 \
            --size Standard_F16s_v2 \
            --location {location} \
            --vnet-name {resource_group}-vnet \
            --subnet {resource_group}-subnet \
            --admin-username {username} \
            --os-disk-delete-option Delete \
            --generate-ssh-keys | tee -a datanode_baseline_output.json"


def cmd_create_namenode_nimble(resource_group: str, location: str, username: str) -> str:
    # create coordinator
    return f"az vm create  \
             --resource-group {resource_group} \
            --name namenode_nimble \
            --image Ubuntu2204 \
            --size Standard_F16s_v2 \
            --location {location} \
            --vnet-name {resource_group}-vnet \
            --subnet {resource_group}-subnet \
            --admin-username {username} \
            --os-disk-delete-option Delete \
            --generate-ssh-keys | tee -a namenode_nimble_output.json"


def cmd_create_datanode_nimble(resource_group: str, location: str, username: str) -> str:
    # create coordinator
    return f"az vm create  \
             --resource-group {resource_group} \
            --name datanode_nimble \
            --image Ubuntu2204 \
            --size Standard_F16s_v2 \
            --location {location} \
            --vnet-name {resource_group}-vnet \
            --subnet {resource_group}-subnet \
            --admin-username {username} \
            --os-disk-delete-option Delete \
            --generate-ssh-keys | tee -a datanode_nimble_output.json"

