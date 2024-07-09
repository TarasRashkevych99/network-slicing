import json
from sys import exit
import os
from admin_create_queues import create_queues_script
import subprocess
import copy

def get_positive_integer(message, allow_zero = False):
    if allow_zero:
        lower_bound = 0
    else:
        lower_bound = 1

    while True:
        user_input = input(message)
        try:
            user_input = int(user_input)
            if user_input < lower_bound:
                print("Error, the value specified must to be a positive integer")
                continue
            break
        except ValueError:
            print("Error, the value specified must to be a positive integer")
    return user_input

def get_topology():
    try:
        with open("topology.json") as f:
            topology = json.load(f)
            return topology[0]
    except FileNotFoundError:
        print("The topology file was not found, you have to generate it first")
        exit()

def add_slice(slice_details, slice_counter, available_link_capacity): 
    topology = get_topology() 

    slice_hosts_list = []
    slice_switch_list = []

    while True:
        host_to_add = get_positive_integer(f"Submit a host to insert in the slice {slice_counter} (type '0' when all the hosts are added)? ", True)
        if host_to_add != 0:
            if host_to_add > topology["number_of_hosts"]:
                print("ERROR, the specified host doesn't exists. \n")
            elif host_to_add in slice_hosts_list:
                print("ERROR, the specified host already belongs to the slice. \n")
            else:
                slice_hosts_list.append(host_to_add)
        elif len(slice_hosts_list) < 2:
            print("ERROR, at least 2 hosts must belong to the slice. \n")
        else:
            break

    while True:
        switch_to_add = get_positive_integer(f"Submit a switch to insert in the slice {slice_counter} (type '0' when all the switches are added)? ", True)
        if switch_to_add != 0:
            if switch_to_add > topology["number_of_switches"]:
                print("ERROR, the specified switch doesn't exists. \n")
            elif switch_to_add in slice_switch_list:
                print("ERROR, the specified switch already belongs to the slice. \n")
            else:
                slice_switch_list.append(switch_to_add)
        elif len(slice_switch_list) < 1:
            print("ERROR, at least a switch must belong to the slice. \n")
        else:
            break

    edge_switches = []
    for i in range(len(slice_hosts_list)):
        switch_to_consider = topology["hosts_to_switches_map"][str(slice_hosts_list[i])]

        if not switch_to_consider in edge_switches:
            edge_switches.append(switch_to_consider)
    
    edge_switches.sort()

    path_between_hosts_dict = {}
    for i in range(len(edge_switches)):
        for j in range(i+1,len(edge_switches)):
            path_between_switches = [int(edge_switches[i])]

            while True:
                switch_to_add = get_positive_integer(f"Which is the next switch belonging to the path of slice {slice_counter} between s{edge_switches[i]} and s{edge_switches[j]}? (type '0' when all the switches are added) ", True)
                if switch_to_add != 0:
                    if not switch_to_add in slice_switch_list:
                        print("ERROR, the specified switch doesn't belong to the slice. \n")
                    elif switch_to_add in path_between_switches or switch_to_add == int(edge_switches[j]):
                        print("ERROR, the specified switch already belongs to the path. \n")
                    elif not str(switch_to_add) in topology["links_among_switches"][str(path_between_switches[-1])]:
                        print(f"ERROR, the switches {switch_to_add} and {path_between_switches[-1]} doesn't have a link between them in the topology. \n")
                    elif available_link_capacity[str(switch_to_add)][str(path_between_switches[-1])] <= 0:
                        print(f"ERROR, the switches {switch_to_add} and {path_between_switches[-1]} doesn't have an available capacity for the current slice. \n")
                    else:
                        path_between_switches.append(switch_to_add)

                else:
                    #add last switch and exit
                    if not str(edge_switches[j]) in topology["links_among_switches"][str(path_between_switches[-1])]:
                        print(f"ERROR, the switch {edge_switches[j]} (the edge one) and {path_between_switches[-1]} doesn't have a link between them in the topology. Add other switches in order to complete the path.\n")
                    else:
                        path_between_switches.append(int(edge_switches[j]))
                        print("SUCCESS \n\n")
                        break
            
            for h1_index in range(len(slice_hosts_list)):
                for h2_index in range(len(slice_hosts_list)):
                    h1 = str(slice_hosts_list[h1_index])
                    h2 = str(slice_hosts_list[h2_index])

                    if not h1 == h2:
                        if not h1 in path_between_hosts_dict:
                            path_between_hosts_dict[h1] = {}
                        
                        if not h2 in path_between_hosts_dict:
                            path_between_hosts_dict[h2] = {}

                        if edge_switches[i] == topology["hosts_to_switches_map"][h1] and edge_switches[j] == topology["hosts_to_switches_map"][h2]:
                            path_between_hosts_dict[h1][h2] = path_between_switches
                            path_between_hosts_dict[h2][h1] = path_between_switches[::-1]

    #add links between hosts sharing the same first switch
    for h1_index in range(len(slice_hosts_list)):
        for h2_index in range(len(slice_hosts_list)):
            h1 = str(slice_hosts_list[h1_index])
            h2 = str(slice_hosts_list[h2_index])

            if not h1 == h2:
                if not h1 in path_between_hosts_dict:
                    path_between_hosts_dict[h1] = {}
                
                if not h2 in path_between_hosts_dict:
                    path_between_hosts_dict[h2] = {}

                if topology["hosts_to_switches_map"][h1] == topology["hosts_to_switches_map"][h2]:
                    path_between_hosts_dict[h1][h2] = [topology["hosts_to_switches_map"][h1]]
                    path_between_hosts_dict[h2][h1] = [topology["hosts_to_switches_map"][h1]]

    link_capacity = -1
    while True:
        link_capacity = get_positive_integer(f"Which is the capacity to assign to the links of the slice? ", False)

        is_capacity_valid = True

        for host1 in path_between_hosts_dict.keys():
            for host2 in path_between_hosts_dict[host1].keys():
                if len(path_between_hosts_dict[host1][host2]) >= 2:
                    for i in range(len(path_between_hosts_dict[host1][host2]) - 1):
                        switch1 = str(path_between_hosts_dict[host1][host2][i])
                        switch2 = str(path_between_hosts_dict[host1][host2][i + 1])
                        
                        available_capacity = available_link_capacity[switch1][switch2]

                        if link_capacity > available_capacity and is_capacity_valid:
                            print("ERROR, the specified capacity is not available (e.g. between s"+switch1+" and s"+switch2+")")
                            is_capacity_valid = False

        available_link_capacity_updated = copy.deepcopy(available_link_capacity)
        if is_capacity_valid:
            for host1 in path_between_hosts_dict.keys():
                for host2 in path_between_hosts_dict[host1].keys():
                    if len(path_between_hosts_dict[host1][host2]) >= 2:
                        for i in range(len(path_between_hosts_dict[host1][host2]) - 1):
                            switch1 = str(path_between_hosts_dict[host1][host2][i])
                            switch2 = str(path_between_hosts_dict[host1][host2][i + 1])
                            
                            if available_link_capacity_updated[switch1][switch2] == available_link_capacity[switch1][switch2]: # so, if it wasn't already updated
                                available_link_capacity_updated[switch1][switch2] = available_link_capacity[switch1][switch2] - link_capacity

            break # all the links have at least the specified capacity                            



    # link_capacity_dict = {}
    # for host1 in path_between_hosts_dict.keys():
    #     for host2 in path_between_hosts_dict[host1].keys():
    #         if len(path_between_hosts_dict[host1][host2]) >= 2:
    #             for i in range(len(path_between_hosts_dict[host1][host2]) - 1):
    #                 switch1 = str(path_between_hosts_dict[host1][host2][i])
    #                 switch2 = str(path_between_hosts_dict[host1][host2][i + 1])

    #                 if not switch1 in link_capacity_dict.keys(): # check if dict for switch1 exists
    #                     link_capacity_dict[switch1] = {}

    #                 if not switch2 in link_capacity_dict[switch1].keys(): # check if dict for switch1 switch2 link exists
    #                     new_available_capacity = available_capacity - link_capacity
    #                     available_link_capacity[switch1][switch2] = new_available_capacity
    #                     available_link_capacity[switch2][switch1] = new_available_capacity

    #                     link_capacity_dict[switch1][switch2] = link_capacity

    #                 if not switch2 in link_capacity_dict.keys(): # check if dict for switch2 exists
    #                     link_capacity_dict[switch2] = {}

    #                 if not switch2 in link_capacity_dict[switch2].keys() and not link_capacity == -1: # check if dict for switch2 switch1 link exists
    #                     link_capacity_dict[switch2][switch1] = link_capacity

    slice_details[str(slice_counter)] = {
        "hosts" : slice_hosts_list,
        "switches" : slice_switch_list,
        "path_between_host" : path_between_hosts_dict,
        "link_capacity" : link_capacity,
    }

    print(f"\nSUCCESS, the slice added can be identified by number {slice_counter}\n")
    return slice_details, available_link_capacity_updated


def activate_slice(is_slice_active, slice_counter):
    while True:
        n_slice = get_positive_integer("Which slice do you want to activate: ")
        if n_slice < slice_counter:
            break
        else:
            print("ERROR, the specified slice doesn't exists")

    is_slice_active[str(n_slice)] = True

    return is_slice_active


def deactivate_slice(is_slice_active, slice_counter):
    while True:
        n_slice = get_positive_integer("Which slice do you want to deactivate: ")
        if n_slice < slice_counter:
            break
        else:
            print("ERROR, the specified slice doesn't exists")

    is_slice_active[str(n_slice)] = False

    return is_slice_active

def assign_slice(slice_counter, port_to_slice, slice_to_port):
    n_slice = int(input("Which slice do you want to assign: "))

    if n_slice >= slice_counter:
        print("Error, the slice specified doesn't exist \n")
        return port_to_slice, slice_to_port

    if input("Do you want to use this slice for ICMP, for ACK responses or as default slice (y/N)? ").lower() == "y":
        port = "DEFAULT"
    else:
        port = get_positive_integer(
            "To which application level port assign the slice (if the port is already assigned, the old slice will be deactivated): "
        )

    if str(port) in port_to_slice:
        del slice_to_port[str(port_to_slice[str(port)])]

    if str(n_slice) in slice_to_port:
        del port_to_slice[str(slice_to_port[str(n_slice)])]

    port_to_slice[str(port)] = str(n_slice)
    slice_to_port[str(n_slice)] = str(port)

    return port_to_slice, slice_to_port

def print_debug(slice_details, is_slice_active, available_link_capacity, slice_to_port):
    full_link_capacity = {}
    topology = get_topology()

    for switch1 in topology["links_among_switches"]:
        full_link_capacity[switch1] = {}

        for switch2 in topology["links_among_switches"][switch1]:
            link_type = topology["links_among_switches"][switch1][switch2]
            link_full_capacity = topology["links"][link_type]

            full_link_capacity[switch1][switch2] = link_full_capacity

    print("\n--- AVAILABLE LINK CAPACITY TO BE ASSIGNED ---")

    for switch1 in available_link_capacity:
        for switch2 in available_link_capacity[switch1]:
            if switch1 < switch2:
                available_capacity = available_link_capacity[switch1][switch2]
                full_capacity = full_link_capacity[switch1][switch2]
                print("s"+str(switch1)+" <--> s"+str(switch2)+" : "+str(available_capacity)+" Mbps, available "+str(round((available_capacity/full_capacity)*100,2))+"%")

    for slice_ in slice_details:
        if slice_ in slice_to_port:
            port = slice_to_port[slice_]
        else:
            port = "False"

        print("\n--- SLICE "+slice_+" ---")
        print("HOSTS: ")
        print(*slice_details[slice_]["hosts"])
        print("SWITCHES: ")
        print(*slice_details[slice_]["switches"])
        print("ACTIVATED: "+str(is_slice_active[slice_]))
        print("ASSIGNED: "+str(port))
        print("LINK CAPACITY: "+str(slice_details[slice_]["link_capacity"])+" Mbps")
        print("LINKS USAGE BY THE SLICE: ")

        link_printed = {}
        for host1 in slice_details[slice_]["path_between_host"].keys():
            for host2 in slice_details[slice_]["path_between_host"][host1].keys():
                path_between_host = slice_details[slice_]["path_between_host"][host1][host2]
                if len(path_between_host) >= 2 and int(host1) < int(host2):
                    for i in range(len(path_between_host) - 1):
                        switch1 = str(path_between_host[i])
                        switch2 = str(path_between_host[i + 1])
                        
                        if switch1 < switch2:
                            if not switch1 in link_printed:
                                link_printed[switch1] = {}
                            
                            if not switch2 in link_printed[switch1]:
                                link_printed[switch1][switch2] = True
                                print("s"+str(switch1)+" <--> s"+str(switch2)+": "+str(round((slice_details[slice_]["link_capacity"]/full_link_capacity[switch1][switch2])*100,2))+"%")
    print("\n")


def execute_operation(operation, slice_details, port_to_slice, slice_to_port, slice_counter, is_slice_active, slices_json_path, available_link_capacity):
    if operation == 1:
        slice_details, available_link_capacity = add_slice(slice_details, slice_counter, available_link_capacity)
        is_slice_active[str(slice_counter)] = True
        slice_counter = slice_counter + 1
    elif operation == 2:
        is_slice_active = activate_slice(is_slice_active, slice_counter)
    elif operation == 3:
        is_slice_active = deactivate_slice(is_slice_active, slice_counter)
    elif operation == 4:
        port_to_slice, slice_to_port = assign_slice(slice_counter, port_to_slice, slice_to_port)
    elif operation == 5:
        print_debug(slice_details, is_slice_active, available_link_capacity, slice_to_port)
    elif operation == 6:
        for switch in range(1,get_topology()["number_of_switches"]+1):
            rule = "sudo ovs-ofctl del-flows s"+str(switch)
            subprocess.run([rule], shell=True)
        exit(0)

    slices_options = (
        {
            "port_to_slice": port_to_slice,
            "slice_to_port": slice_to_port,
            "slice_details": slice_details,
            "active_slices": is_slice_active,
            "available_link_capacity": available_link_capacity
        },
    )

    with open(slices_json_path, "w", encoding="utf-8") as f:
        json.dump(slices_options, f, ensure_ascii=False, indent=4)

    if not operation == 5:
        create_queues_script()
        subprocess.run(["sh queues.sh"], shell=True)

    return slice_counter, slice_details, port_to_slice, slice_to_port, is_slice_active, available_link_capacity

if __name__ == "__main__":
    slices_json_path = "slices.json"
    create_slices_json = True

    if os.path.exists(slices_json_path):
        while True:
            path_action = get_positive_integer(
                f"'1' to modify the existing {slices_json_path}, \n"
                + "'2' to overwrite it by creating a new one \n"
            )
            
            if path_action > 2:
                print("Error, the value written must to be '1' or '2'")
            else:
                if path_action == 1:
                    create_slices_json = False
                break

    if create_slices_json:
        slice_counter = 1
        slice_details = {}
        port_to_slice = {}
        slice_to_port = {}
        is_slice_active = {}

        topology = get_topology()
        available_link_capacity = {}

        for switch1 in topology["links_among_switches"]:
            available_link_capacity[switch1] = {}

            for switch2 in topology["links_among_switches"][switch1]:
                link_type = topology["links_among_switches"][switch1][switch2]
                link_full_capacity = topology["links"][link_type]

                available_link_capacity[switch1][switch2] = link_full_capacity

        slices_options = (
            {
                "port_to_slice": port_to_slice,
                "slice_to_port": slice_to_port,
                "slice_details": slice_details,
                "active_slices": is_slice_active,
                "available_link_capacity": available_link_capacity
            },
        )

        with open(slices_json_path, "w", encoding="utf-8") as f:
            json.dump(slices_options, f, ensure_ascii=False, indent=4)

        slice_counter, slice_details, port_to_slice, slice_to_port, is_slice_active, available_link_capacity = execute_operation(1, slice_details, port_to_slice, slice_to_port, slice_counter, is_slice_active, slices_json_path, available_link_capacity)
    else:
        with open(slices_json_path, "r", encoding="utf-8") as f:
            slices_options = json.load(f)[0]

        slice_details = slices_options["slice_details"]
        port_to_slice = slices_options["port_to_slice"]
        slice_to_port = slices_options["slice_to_port"]
        is_slice_active = slices_options["active_slices"]
        available_link_capacity = slices_options["available_link_capacity"]

        if is_slice_active: # if it's not empty, so it exists at least a slice
            slice_counter = int(max(is_slice_active, key=int)) + 1
        else:
            slice_counter = 0

        create_queues_script()
        subprocess.run(["sh queues.sh"], shell=True)

    while True:
        while True:
            operation = get_positive_integer(
                "'1' to define a slice, \n"
                + "'2' to activate an existing slice \n"
                + "'3' to deactivate a slice \n"
                + "'4' to assign a slice \n"
                + "'5' to have printed the currently defined slices \n"
                + "'6' to exit \n"
            )

            if operation > 6:
                print("Error, the value written must to be between '1' and '6'")
            else:
                break

        slice_counter, slice_details, port_to_slice, slice_to_port, is_slice_active, available_link_capacity = execute_operation(operation, slice_details, port_to_slice, slice_to_port, slice_counter, is_slice_active, slices_json_path, available_link_capacity)
