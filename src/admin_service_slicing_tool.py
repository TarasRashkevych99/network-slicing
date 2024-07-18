from sys import exit
from admin_create_queues import create_queues_script
import json
import os
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

    # Specify the port to use
    if slice_counter == 1:
        print("This is the first slice to be defined and will be used for ICMP, acknowledgments and as default for some unmatched ports. Make sure to insert all the hosts and a coherent set of switches")
        port = "DEFAULT"
    else:
        while True:
            port = get_positive_integer(
                "To which application level port assign the slice: "
            )
            if str(port) in port_to_slice:
                print("ERROR, the current port is already reserved for slice "+port_to_slice[str(port)])
            else:
                break
    
    port_to_slice[str(port)] = str(slice_counter)
    slice_to_port[str(slice_counter)] = str(port)

    topology = get_topology() 

    slice_hosts_list = []
    slice_switch_list = []

    # Specify the hosts to include
    while True:
        host_to_add = get_positive_integer(f"Submit a host to insert in the slice {slice_counter}? (type '0' when all the hosts are added): ", True)
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

    # Specify the switches to include
    while True:
        switch_to_add = get_positive_integer(f"Submit a switch to insert in the slice {slice_counter}? (type '0' when all the switches are added): ", True)
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

    # Autonomously compute the edge switches within the one specified
    edge_switches = []
    for i in range(len(slice_hosts_list)):
        switch_to_consider = topology["hosts_to_switches_map"][str(slice_hosts_list[i])]

        if not switch_to_consider in edge_switches:
            edge_switches.append(switch_to_consider)
    
    edge_switches.sort()

    # ask to the user to connect the edge switches
    path_between_hosts_dict = {}
    for i in range(len(edge_switches)):
        for j in range(i+1,len(edge_switches)): # for every couple of edge switches
            path_between_switches = [int(edge_switches[i])] # include the first edge switch in the path

            while True:
                switch_to_add = get_positive_integer(f"Which is the next switch belonging to the path of slice {slice_counter} between s{edge_switches[i]} and s{edge_switches[j]}, edges excluded? (type '0' when all the switches are added) ", True)
                if switch_to_add != 0:
                    if not switch_to_add in slice_switch_list:
                        print("ERROR, the specified switch doesn't belong to the slice. \n")
                    elif switch_to_add in path_between_switches or switch_to_add == int(edge_switches[j]): # because the last switch is already included
                        print("ERROR, the specified switch already belongs to the path. \n")
                    elif not str(switch_to_add) in topology["links_among_switches"][str(path_between_switches[-1])]:
                        print(f"ERROR, the switches {switch_to_add} and {path_between_switches[-1]} doesn't have a link between them in the topology. \n")
                    elif available_link_capacity[str(switch_to_add)][str(path_between_switches[-1])] <= 0:
                        print(f"ERROR, the switches {switch_to_add} and {path_between_switches[-1]} doesn't have an available capacity for the current slice. \n")
                    else:
                        path_between_switches.append(switch_to_add)

                else:
                    #add last edge switch and exit
                    if not str(edge_switches[j]) in topology["links_among_switches"][str(path_between_switches[-1])]:
                        print(f"ERROR, the switch {edge_switches[j]} (the edge one) and {path_between_switches[-1]} doesn't have a link between them in the topology. Add other switches in order to complete the path.\n")
                    else:
                        path_between_switches.append(int(edge_switches[j]))
                        print("SUCCESS \n\n")
                        break
            
            # fill the path_between_hosts
            for h1_index in range(len(slice_hosts_list)):
                for h2_index in range(len(slice_hosts_list)): #for every host belonging to the slice
                    host_1 = str(slice_hosts_list[h1_index])
                    host_2 = str(slice_hosts_list[h2_index])

                    if not host_1 == host_2:
                        if not host_1 in path_between_hosts_dict:
                            path_between_hosts_dict[host_1] = {}
                        
                        if not host_2 in path_between_hosts_dict:
                            path_between_hosts_dict[host_2] = {}

                        if edge_switches[i] == topology["hosts_to_switches_map"][host_1] and edge_switches[j] == topology["hosts_to_switches_map"][host_2]:
                            path_between_hosts_dict[host_1][host_2] = path_between_switches
                            path_between_hosts_dict[host_2][host_1] = path_between_switches[::-1] # path inversed

    #add links between hosts sharing the same first switch
    for h1_index in range(len(slice_hosts_list)):
        for h2_index in range(len(slice_hosts_list)):
            host_1 = str(slice_hosts_list[h1_index])
            host_2 = str(slice_hosts_list[h2_index])

            if not host_1 == host_2:
                if not host_1 in path_between_hosts_dict:
                    path_between_hosts_dict[host_1] = {}
                
                if not host_2 in path_between_hosts_dict:
                    path_between_hosts_dict[host_2] = {}

                if topology["hosts_to_switches_map"][host_1] == topology["hosts_to_switches_map"][host_2]:
                    path_between_hosts_dict[host_1][host_2] = [topology["hosts_to_switches_map"][host_1]]
                    path_between_hosts_dict[host_2][host_1] = [topology["hosts_to_switches_map"][host_1]] # the path is composed only by a single switch

    # ask for the link capacity
    link_capacity = -1
    while True:
        link_capacity = get_positive_integer(f"Which is the capacity to assign to the links of the slice? ", False)

        is_capacity_valid = True

        for host_1 in path_between_hosts_dict.keys():
            for host_2 in path_between_hosts_dict[host_1].keys():
                if len(path_between_hosts_dict[host_1][host_2]) >= 2: # if the hosts are not connected to the same switch
                    for i in range(len(path_between_hosts_dict[host_1][host_2]) - 1): # for every link
                        switch_1 = str(path_between_hosts_dict[host_1][host_2][i])
                        switch_2 = str(path_between_hosts_dict[host_1][host_2][i + 1])
                        
                        available_capacity = available_link_capacity[switch_1][switch_2] # retrieve the link capacity

                        if link_capacity > available_capacity and is_capacity_valid: # if the link capacity is under the proposed one, ask again the capacity
                            print("ERROR, the specified capacity is not available (e.g. between s"+switch_1+" and s"+switch_2+")")
                            is_capacity_valid = False

        # if the capacity is valid
        available_link_capacity_updated = copy.deepcopy(available_link_capacity)
        if is_capacity_valid:
            for host_1 in path_between_hosts_dict.keys():
                for host_2 in path_between_hosts_dict[host_1].keys():
                    if len(path_between_hosts_dict[host_1][host_2]) >= 2:
                        for i in range(len(path_between_hosts_dict[host_1][host_2]) - 1): # for every link used
                            switch_1 = str(path_between_hosts_dict[host_1][host_2][i])
                            switch_2 = str(path_between_hosts_dict[host_1][host_2][i + 1])
                            
                            if available_link_capacity_updated[switch_1][switch_2] == available_link_capacity[switch_1][switch_2]: # if the capacity was not updated
                                available_link_capacity_updated[switch_1][switch_2] = available_link_capacity[switch_1][switch_2] - link_capacity

            break # all the links have at least the specified capacity, and the update was already done                      

    slice_details[str(slice_counter)] = { # the object will be written on the json
        "hosts" : slice_hosts_list,
        "switches" : slice_switch_list,
        "path_between_host" : path_between_hosts_dict,
        "link_capacity" : link_capacity,
    }

    print(f"\nSUCCESS, the slice added can be identified by number {slice_counter}\n")
    return slice_details, available_link_capacity_updated, port_to_slice, slice_to_port


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

# assign_slice is currently not used, it can be useful to reassing in real time a slice to a port

# def assign_slice(slice_counter, port_to_slice, slice_to_port):
#     n_slice = int(input("Which slice do you want to assign: "))

#     if n_slice >= slice_counter:
#         print("Error, the slice specified doesn't exist \n")
#         return port_to_slice, slice_to_port

#     if input("Do you want to use this slice for ICMP, for ACK responses or as default slice (y/N)? ").lower() == "y":
#         port = "DEFAULT"
#     else:
#         port = get_positive_integer(
#             "To which application level port assign the slice (if the port is already assigned, the old slice will be deactivated): "
#         )

#     if str(port) in port_to_slice:
#         del slice_to_port[str(port_to_slice[str(port)])]

#     if str(n_slice) in slice_to_port:
#         del port_to_slice[str(slice_to_port[str(n_slice)])]

#     port_to_slice[str(port)] = str(n_slice)
#     slice_to_port[str(n_slice)] = str(port)

#     return port_to_slice, slice_to_port

def print_debug(slice_details, is_slice_active, available_link_capacity, slice_to_port):
    full_link_capacity = {}
    topology = get_topology()

    for switch_1 in topology["links_among_switches"]:
        full_link_capacity[switch_1] = {}

        for switch_2 in topology["links_among_switches"][switch_1]: # for every couple of switches
            link_type = topology["links_among_switches"][switch_1][switch_2]
            link_full_capacity = topology["links"][link_type]

            full_link_capacity[switch_1][switch_2] = link_full_capacity # store its full capacity (topology related)

    print("\n--- AVAILABLE LINK CAPACITY TO BE ASSIGNED ---")

    for switch_1 in available_link_capacity:
        for switch_2 in available_link_capacity[switch_1]:
            if switch_1 < switch_2: # for every unordered couple of switch, retrieve the full and available capacity, in order to present in absolute and percentage terms the available capacity
                available_capacity = available_link_capacity[switch_1][switch_2]
                full_capacity = full_link_capacity[switch_1][switch_2]
                print("s"+str(switch_1)+" <--> s"+str(switch_2)+" : "+str(available_capacity)+" Mbps, available "+str(round((available_capacity/full_capacity)*100,2))+"%")

    for slice_ in slice_details:
        if slice_ in slice_to_port: # set the ports used by the slice
            port = slice_to_port[slice_]
        else:
            port = "False"

        print("\n--- SLICE "+slice_+" ---")
        print("HOSTS: ")
        print(*slice_details[slice_]["hosts"]) # * is used to print inline a list
        print("SWITCHES: ")
        print(*slice_details[slice_]["switches"])
        print("ACTIVATED: "+str(is_slice_active[slice_]))
        print("ASSIGNED: "+str(port))
        print("LINK CAPACITY: "+str(slice_details[slice_]["link_capacity"])+" Mbps")
        print("LINKS USAGE BY THE SLICE: ")

        slice_links_dict = {}
        for host_1 in slice_details[slice_]["path_between_host"].keys():
            for host_2 in slice_details[slice_]["path_between_host"][host_1].keys():
                path_between_host = slice_details[slice_]["path_between_host"][host_1][host_2]
                if len(path_between_host) >= 2 and int(host_1) < int(host_2): 
                    for i in range(len(path_between_host) - 1):
                        switch_1 = str(path_between_host[i])
                        switch_2 = str(path_between_host[i + 1])
                        
                        #if switch_1 < switch_2:
                        if not switch_1 in slice_links_dict:
                            slice_links_dict[switch_1] = {}
                        
                        if not switch_2 in slice_links_dict[switch_1]: # in order to avoid to print multiple times the same link
                            slice_links_dict[switch_1][switch_2] = True
                            print("s"+str(switch_1)+" <--> s"+str(switch_2)+": "+str(round((slice_details[slice_]["link_capacity"]/full_link_capacity[switch_1][switch_2])*100,2))+"%")
        
        if not slice_links_dict:
            print("All the links of the slice are between hosts and switches")
    print("\n")


def execute_operation(operation, slice_details, port_to_slice, slice_to_port, slice_counter, is_slice_active, slices_json_path, available_link_capacity):
    if operation == 1:
        slice_details, available_link_capacity, port_to_slice, slice_to_port = add_slice(slice_details, slice_counter, available_link_capacity)
        is_slice_active[str(slice_counter)] = True
        slice_counter = slice_counter + 1
    elif operation == 2:
        is_slice_active = activate_slice(is_slice_active, slice_counter)
    elif operation == 3:
        is_slice_active = deactivate_slice(is_slice_active, slice_counter)
    # elif operation == 4:
    #     port_to_slice, slice_to_port = assign_slice(slice_counter, port_to_slice, slice_to_port)
    elif operation == 4:
        print_debug(slice_details, is_slice_active, available_link_capacity, slice_to_port)
    elif operation == 5:
        pass # with this pass will be simply re written the json and re executed the queues related scripts
    elif operation == 6:
        for switch in range(1,get_topology()["number_of_switches"]+1): # delete the rules for every switch and then exit
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

    if not operation == 4: # if the slice-related scenario is not changed, there is no the need to execute the bash
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

        for switch_1 in topology["links_among_switches"]:
            available_link_capacity[switch_1] = {}

            for switch_2 in topology["links_among_switches"][switch_1]:
                link_type = topology["links_among_switches"][switch_1][switch_2]
                link_full_capacity = topology["links"][link_type]

                available_link_capacity[switch_1][switch_2] = link_full_capacity # store the full_link_capacity that, at the beginning, will be also the available one

        slices_options = (
            {
                "port_to_slice": port_to_slice,
                "slice_to_port": slice_to_port,
                "slice_details": slice_details,
                "active_slices": is_slice_active,
                "available_link_capacity": available_link_capacity
            },
        )

        with open(slices_json_path, "w", encoding="utf-8") as f: # the basic informations about the topology are written in the json so that can be immediately be used by the controller
            json.dump(slices_options, f, ensure_ascii=False, indent=4)

        slice_counter, slice_details, port_to_slice, slice_to_port, is_slice_active, available_link_capacity = execute_operation(1, slice_details, port_to_slice, slice_to_port, slice_counter, is_slice_active, slices_json_path, available_link_capacity)
    
    else: # if I want to use a previous configuration
        with open(slices_json_path, "r", encoding="utf-8") as f:
            slices_options = json.load(f)[0]

        # I read the previously set values
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
                # + "'4' to assign a slice \n"
                + "'4' to have printed the currently defined slices \n"
                + "'5' to force the execution of the last add-flow \n"
                + "'6' to exit \n"
            )

            if operation > 6:
                print("Error, the value written must to be between '1' and '6'")
            else:
                break

        slice_counter, slice_details, port_to_slice, slice_to_port, is_slice_active, available_link_capacity = execute_operation(operation, slice_details, port_to_slice, slice_to_port, slice_counter, is_slice_active, slices_json_path, available_link_capacity)
