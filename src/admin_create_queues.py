import json 
# def get_queue_capacity(switch_list, switch1, switch2, capacity_list):
#     try:
#         index1 = switch_list.index(switch1)
#         index2 = switch_list.index(switch2)
#         if abs(index1 - index2) == 1:
#             if index1 < index2:
#                 return capacity_list[index1]
#             else:
#                 return capacity_list[index2]
#         else:
#             return 0
#     except ValueError:
#         return 0

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

# def get_ports_from_slice(my_dict, target_value):
#     keys = []
#     for key, value in my_dict.items():
#         if value == target_value:
#             keys.append(key)
#     return keys 

def convert_int_to_ip(n):
    part1 = n // (256 * 256)
    part2 = (n // 256) % 256
    part3 = n % 256

    ip_address = f"10.{part1}.{part2}.{part3}"
    return ip_address

def convert_mac_to_host_id(mac_str):
    mac_str = mac_str.replace(':', '')

    host_id = int(mac_str)
    return host_id

def get_port_to_mac(mac_to_port):
    inverted_dict = {}
    for outer_key, inner_dict in mac_to_port.items():
        inverted_dict[outer_key] = {str(value): key for key, value in inner_dict.items()}
    return inverted_dict

def is_link_used(path_between_hosts, adjacent_links):
    for outer_key, inner_dict in path_between_hosts.items():
        for inner_key, lst in inner_dict.items():
            for i in range(len(lst) - 1):
                if lst[i] == adjacent_links[0] and lst[i+1] == adjacent_links[1]:
                    return True
    return False

def create_queues_script():
    topology = get_topology() 
    n_hosts = topology["number_of_hosts"]
    n_switches = topology["number_of_switches"]
    mac_to_port = topology["hosts_macs_to_switches_ports"]
    switch_port_to_mac = get_port_to_mac(mac_to_port)
    switch_port_to_switch = topology["out_port_to_switch"]
    links_among_switches = topology["links_among_switches"]
    links_type_to_capacity = topology["links"]
    hosts_to_switches_map = topology["hosts_to_switches_map"]

    slices = get_slices() 
    slice_details = slices["slice_details"]
    slice_to_port = slices["slice_to_port"]
    is_slice_active = slices["active_slices"]

    # dump all
    dump_rules = []

    for switch in range(1,n_switches+1):
        rule = "sudo ovs-ofctl del-flows s"+str(switch)
        dump_rules.append(rule)

    queues_definition = []

    for i in range(n_switches): # for every switch
        switch = str(i+1)

        if switch in switch_port_to_mac:
            # host-switch ports
            for port in switch_port_to_mac[switch]:
                connected_host_id = convert_mac_to_host_id(switch_port_to_mac[switch][port])
                queues_list=[]
                queues_rate=[]

                q_def = ("sudo ovs-vsctl set port s"+switch+"-eth"+port+" qos=@newqos -- \\\n"+
                "--id=@newqos create QoS type=linux-htb \\\n"+
                "other-config:max-rate=10000000000 \\\n")

                for _slice in slice_details:
                    if connected_host_id in slice_details[_slice]["hosts"]:
                        queues_list.append("queues:"+_slice+"=@slice_"+_slice)
                        queues_rate.append("--id=@slice_"+_slice+" create queue other-config:min-rate=10000 other-config:max-rate="+str(slice_details[_slice]["link_capacity"]*1000*1000))

                if len(queues_list) > 0:
                    queues_definition.append(q_def+" \\\n".join(queues_list)+" -- \\\n"+" -- \\\n".join(queues_rate)+"\n")

        # switch-switch ports
        if switch in switch_port_to_switch:
          for port in switch_port_to_switch[switch]:
                connected_switch_id = switch_port_to_switch[switch][port]
                link_type = links_among_switches[str(switch)][str(connected_switch_id)]
                link_phy_capacity = links_type_to_capacity[link_type]
                queues_list=[]
                queues_rate=[]

                q_def = ("sudo ovs-vsctl set port s"+switch+"-eth"+port+" qos=@newqos -- \\\n"+
                "--id=@newqos create QoS type=linux-htb \\\n"+
                "other-config:max-rate="+str(link_phy_capacity*1000*1000)+" \\\n")
            
                for _slice in slice_details:
                    if is_link_used(slice_details[_slice]["path_between_host"], (int(switch),int(connected_switch_id))):
                        queues_list.append("queues:"+_slice+"=@slice_"+_slice)
                        queues_rate.append("--id=@slice_"+_slice+" create queue other-config:min-rate=10000 other-config:max-rate="+str(slice_details[_slice]["link_capacity"]*1000*1000))
                
                if len(queues_list) > 0:
                    queues_definition.append(q_def+" \\\n".join(queues_list)+" -- \\\n"+" -- \\\n".join(queues_rate)+"\n")

    # drop all
    rules_set = []
    # for switch in range(1,n_switches+1):
    #     for host_1 in range(1,n_hosts+1):
    #         for host_2 in range(1,n_hosts+1):
    #             if not host_1 == host_2:
    #                 rule = "sudo ovs-ofctl add-flow s"+str(switch)+" tcp,priority=65499,nw_src="+convert_int_to_ip(int(host_1))+",nw_dst="+convert_int_to_ip(int(host_2))+", idle_timeout=0,actions=drop"
    #                 rule = rule + "\n"
    #                 rule = rule + "sudo ovs-ofctl add-flow s"+str(switch)+" udp,priority=65499,nw_src="+convert_int_to_ip(int(host_1))+",nw_dst="+convert_int_to_ip(int(host_2))+", idle_timeout=0,actions=drop"
    #                 rule = rule + "\n"
    #                 rule = "sudo ovs-ofctl add-flow s"+str(switch)+" ip,priority=65499,nw_src="+convert_int_to_ip(int(host_1))+",nw_dst="+convert_int_to_ip(int(host_2))+",idle_timeout=0,actions=drop"
    #                 rule = rule + "\n"
                
    #                 rules_set.append(rule)

    # last rules
    for _slice in slice_details:
        for host_1 in slice_details[_slice]["hosts"]:
            for host_2 in slice_details[_slice]["path_between_host"][str(host_1)]:
                if not str(host_1) == str(host_2):
                    for switch in slice_details[_slice]["switches"]:
                        if str(_slice) in slice_to_port:
                            if is_slice_active[str(_slice)]:
                                rule = ""
                                
                                if not slice_to_port[str(_slice)] == "DEFAULT":
                                    rule = "sudo ovs-ofctl add-flow s"+str(switch)+" tcp,priority=65500,nw_src="+convert_int_to_ip(int(host_1))+",nw_dst="+convert_int_to_ip(int(host_2))+",tp_dst="+str(slice_to_port[str(_slice)])+",idle_timeout=0,actions=set_queue:"+_slice+",normal"
                                    rule = rule + "\n"
                                    rule = rule + "sudo ovs-ofctl add-flow s"+str(switch)+" udp,priority=65500,nw_src="+convert_int_to_ip(int(host_1))+",nw_dst="+convert_int_to_ip(int(host_2))+",tp_dst="+str(slice_to_port[str(_slice)])+",idle_timeout=0,actions=set_queue:"+_slice+",normal"
                                else:
                                    rule = "sudo ovs-ofctl add-flow s"+str(switch)+" ip,priority=65499,nw_src="+convert_int_to_ip(int(host_1))+",nw_dst="+convert_int_to_ip(int(host_2))+",idle_timeout=0,actions=set_queue:"+_slice+",normal"

                                rules_set.append(rule)
            rules_set.append("\n")
        rules_set.append("\n")


    f = open("queues.sh", "w")
    f.write('#!/bin/sh \n\n'+
        '\n'.join(dump_rules)+'\n\n'+
        '\n'.join(queues_definition)+'\n'+
        '\n'.join(rules_set))
    f.close()
