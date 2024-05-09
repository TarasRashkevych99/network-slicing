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

if __name__ == "__main__":
    topology = get_topology() 
    n_switches = topology["number_of_switches"]
    switches_ports = topology["out_port_to_switch"]

    slices = get_slices()
    slices_defined = slices["slice_details"]
    
    queues_definition = []

    for i in range(n_switches): # for every switch
        switch_id = str(i + 1)
        switch_ports = switches_ports[switch_id].keys()

        for port in switch_ports: # for every port of the switch
            dest_switch = switches_ports[switch_id][port]
            
            queue_definition = f"""sudo ovs-vsctl set port s{switch_id}-eth{port} qos=@newqos -- \\
--id=@qos-s{switch_id}-eth{port} create QoS type=linux-htb \\
other-config:max-rate=10000000000 \\ \n"""

            queue_counter = 1
            queues_id = []
            queues_rate = []

            for slice_key in slices_defined.keys():
                slice_switches = slices_defined[slice_key]["switches"]

                queue_capacity = get_queue_capacity(slice_switches, int(switch_id), dest_switch, slices_defined[slice_key]["capacity"])

                if queue_capacity != 0 :
                    queues_id.append(f" queues:{queue_counter}=@{queue_counter}q-s{switch_id}-eth{port}")
                    queues_rate.append(f" --id=@{queue_counter}q-s{switch_id}-eth{port} create queue other-config:min-rate=1000 other-config:max-rate={queue_capacity*8*1024*1024}")
                    # queues_rate.append(f" --id=@{queue_counter}q-s{switch_id}-eth{port} create queue other-config:min-rate=1000 other-config:max-rate={queue_capacity}")


                    queue_counter = queue_counter + 1
            
            for queue in queues_id:
                queue_definition = queue_definition + queue + "\n"

            for rate in queues_rate:
                queue_definition = queue_definition + rate + "\n"

            queues_definition.append(queue_definition)

    f = open("queues.sh", "w")
    f.write('\n'.join(queues_definition))
    f.close()