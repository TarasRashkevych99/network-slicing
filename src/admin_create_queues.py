import json 
def get_queue_capacity(switch_list, switch1, switch2, capacity_list):
    try:
        index1 = switch_list.index(switch1)
        index2 = switch_list.index(switch2)
        if abs(index1 - index2) == 1:
            if index1 < index2:
                return capacity_list[index1]
            else:
                return capacity_list[index2]
        else:
            return 0
    except ValueError:
        return 0

def get_slices():
    try:
        with open("slices.json") as f:
            slices = json.load(f)
            return slices[0]
    except FileNotFoundError:
        print("The slices file was not found, you have to generate it first")
        exit()

def get_topology():
    try:
        with open("topology.json") as f:
            topology = json.load(f)
            return topology[0]
    except FileNotFoundError:
        print("The topology file was not found, you have to generate it first")
        exit()

def get_port_from_slice(my_dict, target_value):
    for key, value in my_dict.items():
        if value == target_value:
            return key
    return None 

def convert_int_to_ip(n):
    part1 = n // (256 * 256)
    part2 = (n // 256) % 256
    part3 = n % 256

    ip_address = f"10.{part1}.{part2}.{part3}"
    return ip_address

if __name__ == "__main__":
    topology = get_topology() 
    n_switches = topology["number_of_switches"]
    switches_ports = topology["out_port_to_switch"]

    slices = get_slices()
    slices_defined = slices["slice_details"]
    port_to_slice = slices["port_to_slice"]

    queues_definition = []
    queues_usage = []

    queue_counter = 1

    for i in range(n_switches): # for every switch
        switch_id = str(i + 1)
        switch_ports = switches_ports[switch_id].keys()

        for port in switch_ports: # for every port of the switch
            dest_switch = switches_ports[switch_id][port]

            link_capacity = topology["links"][topology["links_among_switches"][switch_id][str(switches_ports[switch_id][port])]]

            queue_definition = f"""sudo ovs-vsctl set port s{switch_id}-eth{port} qos=@newqos -- \\\n"""
            queue_definition = queue_definition + f"""--id=@newqos create QoS type=linux-htb other-config:max-rate={link_capacity * 1000 * 1000}"""

            queues_id = []
            queues_rate = []

            for slice_key in slices_defined.keys():
                slice_switches = slices_defined[slice_key]["switches"]

                queue_capacity = get_queue_capacity(slice_switches, int(switch_id), dest_switch, slices_defined[slice_key]["capacity"])

                if queue_capacity != 0 :
                    # define queue
                    queue_id = f"{queue_counter}q-s{switch_id}-eth{port}"
                    queues_id.append(f" queues:{queue_counter}=@{queue_id}")
                    queues_rate.append(f"--id=@{queue_id} create queue other-config:min-rate=1000 other-config:max-rate={queue_capacity*1000*1000}")

                    # define queue usage
                    slice_application_port = get_port_from_slice(port_to_slice, int(slice_key))

                    queue_usage = ""

                    if slice_application_port == "ICMP": 
                        queue_usage = f"sudo ovs-ofctl add-flow s{switch_id} ip,priority=65500,nw_src={convert_int_to_ip(int(switch_id))},nw_dst={convert_int_to_ip(switches_ports[switch_id][port])},idle_timeout=0,actions=set_queue:{queue_counter},normal"
                    elif slice_application_port == "DEFAULT":
                        queue_usage = f"sudo ovs-ofctl add-flow s{switch_id} icmp,priority=65500,nw_src={convert_int_to_ip(int(switch_id))},nw_dst={convert_int_to_ip(switches_ports[switch_id][port])},idle_timeout=0,actions=set_queue:{queue_counter},normal"
                    else:
                        queue_usage = f"sudo ovs-ofctl add-flow s{switch_id} ip,priority=65500,nw_src={convert_int_to_ip(int(switch_id))},nw_dst={convert_int_to_ip(switches_ports[switch_id][port])},tp_dst={slice_application_port},idle_timeout=0,actions=set_queue:{queue_counter},normal"

                    queues_usage.append(queue_usage)

                    queue_counter = queue_counter + 1
            
            if len(queues_id)>0:
                queues_id[len(queues_id)-1] = queues_id[len(queues_id)-1]+" --"

                queue_definition = queue_definition + " ".join(queues_id) + " \\\n"

                queue_definition = queue_definition + " -- \\\n".join(queues_rate)

                queues_definition.append(queue_definition)
            

    f = open("queues.sh", "w")
    f.write('\n\n'.join(queues_definition) + '\n\n' + '\n\n'.join(queues_usage))
    f.close()
