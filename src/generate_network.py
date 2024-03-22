def get_positive_integer(message):
    while True:
        user_input = input(message)
        try:
            user_input = int(user_input)
            if user_input < 1: 
                print("Error, the value specified must to be a positive integer")
                continue
            break
        except ValueError:
            print("Error, the value specified must to be a positive integer")  
    return user_input

def get_host_to_switch(n_host, n_switch):
    host_to_switch = {}
    for i in range(n_host):
        while True:
            switch_id = get_positive_integer(f"To which switch link the host h{i+1}: ")
            if switch_id <= n_switch:
                host_to_switch[i] = switch_id-1 #-1 to get right index
                break
            else:
                print(f"Error, the switch must to be between 1 and {n_switch}")
    print("\n")
    return host_to_switch

def get_mac_to_port(host_to_switch):
    mac_to_port = {}

    switches_used = set(host_to_switch.values())

    for switch in switches_used:
        host_attached = {}
        port_counter = 1

        for key, value in host_to_switch.items():
            if value == switch:
                hex_string = '{:X}'.format(key+1)

                padded_hex_string = hex_string.zfill(12)

                mac_address = ':'.join([padded_hex_string[i:i+2] for i in range(0, len(padded_hex_string), 2)])

                host_attached[mac_address] = port_counter
                port_counter = port_counter + 1
        
        mac_to_port[switch+1] = host_attached

    return mac_to_port

def get_links():
    link_dict = {}
    n_links = get_positive_integer("Insert the number of links' type that will be added between switches: ")

    for i in range(n_links):
        while True:
            link_name = input(f"Insert the name of the link {str(i)}: ")

            if link_name == "":
                print("Error, the name specified must to be non empty.")
            elif link_name  == "host":
                print("Error, the name couldn't be host.")
            elif link_name in link_dict:
                print("Error, the name specified already exists.")
            else:
                break

        link_bw = get_positive_integer(f"Insert the bandwidth of the link {link_name} (in Mbps): ")

        link_dict[link_name] = link_bw

        print("\n")

    return link_dict

def add_links(link_dict, n_switch):
    link_added = {}

    for i in range(n_switch):
        for j in range(i+1, n_switch):
            while True:
                link_used = input("Insert the link name between s"+str(i+1)+" and s"+str(j+1)+" (return if you don't want to add a link): ")

                if link_used in link_dict or link_used == "":
                    break
                else:
                    print("Error, the name specified does not exists.")

            if not link_used == "":
                link_added[(i,j)] = link_used
    
    return link_added

def generate_source_code(n_host, n_switch, host_to_switch, link_dict, link_added):
    source_code = """#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink


class NetworkSlicingTopo(Topo):
    def __init__(self):
        # Initialize topology
        Topo.__init__(self)

        # Create template host, switch, and link
        host_config = dict(inNamespace=True)
        host_link_config = dict() \n"""

    for link in link_dict:
        source_code = source_code + f"""        {link}_link_config =  dict(bw={str(link_dict[link])})\n"""
    
    source_code = source_code + f"""
        for i in range({n_switch}):
            sconfig = {{"dpid": "%016x" % (i + 1)}}
            self.addSwitch("s%d" % (i + 1), **sconfig)
        """

    source_code = source_code + f"""
        for i in range({n_host}):
            self.addHost("h%d" % (i + 1), **host_config) \n \n"""

    for key, value in link_added.items():
        i, j = key
        link_used = value
        source_code = source_code +f"""        self.addLink("s{i+1}", "s{j+1}", **{link_used}_link_config) \n"""

    source_code = source_code + "\n"

    for host in host_to_switch:
        source_code = source_code + f"""        self.addLink("h{host+1}", "s{host_to_switch[host]+1}", **host_link_config)\n"""

    source_code = source_code + f"""
topos = {{"networkslicingtopo": (lambda: NetworkSlicingTopo())}}

if __name__ == "__main__":
    topo = NetworkSlicingTopo()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)
    net.build()
    net.start()
    CLI(net)
    net.stop()
        """
    return source_code


if __name__ == "__main__":
    n_host = get_positive_integer("Insert the number of hosts: ")
    if n_host == 1:
        print("There will be added 1 host, named h1\n")
    else:
        print(f"There will be added {str(n_host)} hosts, from h1 to h{str(n_host)}\n")


    n_switch = get_positive_integer("Insert the number of switches: ")
    if n_switch == 1:
        print("There will be added 1 switch, named s1\n")
    else:
        print(f"There will be added {str(n_switch)} switches, from s1 to s{str(n_switch)}\n")

    host_to_switch = get_host_to_switch(n_host, n_switch)

    link_dict = get_links()

    link_added = add_links(link_dict, n_switch)

    source_code = generate_source_code(n_host, n_switch, host_to_switch, link_dict, link_added)

    with open("network.py", "w") as file:
        file.write(source_code)

    mac_to_port = get_mac_to_port(host_to_switch)

    with open("mac_to_port.py", "w") as file:
        file.write(f"mac_to_port = {mac_to_port}\n")
