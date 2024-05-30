import json
from sys import exit
import os

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
    slice_switch_path_list = []

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
        switch_to_add = get_positive_integer(f"Which is the next switch belonging to the path of slice {slice_counter} (type '0' when all the switches are added)? ", True)
        if switch_to_add != 0:
            if switch_to_add > topology["number_of_switches"]:
                print("ERROR, the specified switch doesn't exists. \n")
            elif switch_to_add in slice_switch_path_list:
                print("ERROR, the specified switch already belongs to the path. \n")
            elif len(slice_switch_path_list) > 0 and not str(switch_to_add) in topology["links_among_switches"][str(slice_switch_path_list[-1])]:
                print(f"ERROR, the switches {switch_to_add} and {slice_switch_path_list[-1]} doesn't have a link between them in the topology. \n")
            elif len(slice_switch_path_list) > 0 and available_link_capacity[str(switch_to_add)][str(slice_switch_path_list[-1])] <= 0:
                print(f"ERROR, the switches {switch_to_add} and {slice_switch_path_list[-1]} doesn't have an available capacity for the current slice. \n")
            else:
                slice_switch_path_list.append(switch_to_add)
        elif len(slice_switch_path_list) < 1:
            print("ERROR, at least a switch must belong to the slice. \n")
        else:
            break

    queue_capacity = []

    for i in range(len(slice_switch_path_list) - 1):
        switch_1 = str(slice_switch_path_list[i])
        switch_2 = str(slice_switch_path_list[i+1])
        available_capacity = available_link_capacity[switch_1][switch_2]

        while True:
            proposed_link_capacity = get_positive_integer(f"Specify the capacity of the virtual queue between s{switch_1} and s{switch_2}: ")

            if proposed_link_capacity <= available_capacity:
                new_available_capacity = available_capacity - proposed_link_capacity
                available_link_capacity[switch_1][switch_2] = new_available_capacity
                available_link_capacity[switch_2][switch_1] = new_available_capacity

                queue_capacity.append(proposed_link_capacity)
                break
            else:
                print(f"ERROR, the available capacity for the link is {available_capacity}. \n")

    slice_details[str(slice_counter)] = {
        "hosts" : slice_hosts_list,
        "switches" : slice_switch_path_list,
        "capacity" : queue_capacity
    }

    print(f"\nSUCCESS, the slice added can be identified by number {slice_counter}\n")
    return slice_details, available_link_capacity


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

def assign_slice(slice_counter, port_to_slice):
    n_slice = int(input("Which slice do you want to assign: "))

    if n_slice >= slice_counter:
        print("Error, the slice specified doesn't exist \n")
        return port_to_slice

    if input("Do you want to use this slice for ICMP (y/N)? ").lower() == "y":
        port = "ICMP"
    elif input("Do you want to use this slice for the ACK responses or as default slice (y/N)? ").lower() == "y":
        port = "DEFAULT"
    else:
        port = get_positive_integer(
            "To which application level port assign the slice (if the port is already assigned, the old slice will be deactivated): "
        )

    port_to_slice[port] = n_slice

    return port_to_slice


def execute_operation(operation, slice_details, port_to_slice, slice_counter, is_slice_active, slices_json_path, available_link_capacity):
    if operation == 1:
        slice_details, available_link_capacity = add_slice(slice_details, slice_counter, available_link_capacity)
        is_slice_active[str(slice_counter)] = True
        slice_counter = slice_counter + 1
    elif operation == 2:
        is_slice_active = activate_slice(is_slice_active, slice_counter)
    elif operation == 3:
        is_slice_active = deactivate_slice(is_slice_active, slice_counter)
    elif operation == 4:
        port_to_slice = assign_slice(slice_counter, port_to_slice)
    elif operation == 5:
        exit(0)

    slices_options = (
        {
            "port_to_slice": port_to_slice,
            "slice_details": slice_details,
            "active_slices": is_slice_active,
            "available_link_capacity": available_link_capacity
        },
    )

    with open(slices_json_path, "w", encoding="utf-8") as f:
        json.dump(slices_options, f, ensure_ascii=False, indent=4)

    return slice_counter, slice_details, port_to_slice, is_slice_active

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
        is_slice_active = {}

        topology = get_topology()
        available_link_capacity = {}

        for switch1 in topology["links_among_switches"]:
            available_link_capacity[switch1] = {}

            for switch2 in topology["links_among_switches"][switch1]:
                link_type = topology["links_among_switches"][switch1][switch2]
                link_full_capacity = topology["links"][link_type]

                available_link_capacity[switch1][switch2] = link_full_capacity

        slice_counter, slice_details, port_to_slice, is_slice_active = execute_operation(1, slice_details, port_to_slice, slice_counter, is_slice_active, slices_json_path, available_link_capacity)
    else:
        with open(slices_json_path, "r", encoding="utf-8") as f:
            slices_options = json.load(f)[0]

        slice_details = slices_options["slice_details"]
        port_to_slice = slices_options["port_to_slice"]
        is_slice_active = slices_options["active_slices"]
        available_link_capacity = slices_options["available_link_capacity"]

        slice_counter = int(max(is_slice_active, key=int)) + 1


    while True:
        while True:
            operation = get_positive_integer(
                "'1' to define a slice, \n"
                + "'2' to activate an existing slice \n"
                + "'3' to deactivate a slice \n"
                + "'4' to assign a slice \n"
                + "'5' to exit \n"
            )

            if operation > 5:
                print("Error, the value written must to be between '1' and '5'")
            else:
                break

        slice_counter, slice_details, port_to_slice, is_slice_active = execute_operation(operation, slice_details, port_to_slice, slice_counter, is_slice_active, slices_json_path, available_link_capacity)
