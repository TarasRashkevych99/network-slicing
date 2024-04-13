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


def add_slice(slice_nodes_path, port_to_slice, slice_counter):

    slice_nodes_path_list = []

    while True:
        switch_to_add = get_positive_integer(f"Which is the next switch belonging to the path of slice {slice_counter} (type '0' when all the switches are added)? ", True)
        if switch_to_add != 0:
            # TODO check if path is feasible
            if switch_to_add in slice_nodes_path_list:
                print("ERROR, the specified switch already belongs to the path. \n")
            else:
                slice_nodes_path_list.append(switch_to_add)
        else:
            break

    slice_nodes_path[str(slice_counter)] = slice_nodes_path_list

    if input("Do you want to use this slice for ICMP (y/N)? ").lower() == "y":
        port = "ICMP"
    else:
        port = get_positive_integer(
            "From which application level port assign the slice (if the port is already assigned, the old slice will be deactivated): "
        )

    port_to_slice[port] = slice_counter

    print(f"\nSUCCESS, the slice added can be identified by number {slice_counter}\n")
    return slice_nodes_path, port_to_slice


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

def define_virtual_queue(slice_nodes_path, virtual_queues, slice_counter):
    while True:
        n_slice = get_positive_integer("On which slice do you want to add a virtual queue: ")
        if n_slice < slice_counter:
            break
        else:
            print("ERROR, the specified slice doesn't exists")

    queue_capacity = []

    for i in range(len(slice_nodes_path[str(n_slice)]) - 1):
        # TODO compare with available capacity
        link_capacity = get_positive_integer(f"Specify the capacity of the virtual queue between s{slice_nodes_path[str(n_slice)][i]} and s{slice_nodes_path[str(n_slice)][i+1]}: ")
        queue_capacity.append(link_capacity)

    if str(n_slice) not in virtual_queues:
        virtual_queues[str(n_slice)] = {}

    virtual_queues[str(n_slice)][len(virtual_queues[str(n_slice)])] = queue_capacity

    return virtual_queues

def execute_operation(operation, slice_nodes_path, port_to_slice, slice_counter, is_slice_active, virtual_queues, slices_json_path):
    if operation == 1:
        slice_nodes_path, port_to_slice = add_slice(slice_nodes_path, port_to_slice, slice_counter)
        is_slice_active[str(slice_counter)] = True
        slice_counter = slice_counter + 1
    elif operation == 2:
        is_slice_active = activate_slice(is_slice_active, slice_counter)
    elif operation == 3:
        is_slice_active = deactivate_slice(is_slice_active, slice_counter)
    elif operation == 4:
        virtual_queues = define_virtual_queue(slice_nodes_path, virtual_queues, slice_counter)
    elif operation == 5:
        exit(0)

    slices_options = (
        {
            "port_to_slice": port_to_slice,
            "slice_nodes_path": slice_nodes_path,
            "active_slices": is_slice_active,
            "virtual_queues" : virtual_queues,
        },
    )

    with open(slices_json_path, "w", encoding="utf-8") as f:
        json.dump(slices_options, f, ensure_ascii=False, indent=4)

    return slice_counter, slice_nodes_path, port_to_slice, is_slice_active

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
        slice_nodes_path = {}
        port_to_slice = {}
        is_slice_active = {}
        virtual_queues = {}
        slice_counter, slice_nodes_path, port_to_slice, is_slice_active = execute_operation(1, slice_nodes_path, port_to_slice, slice_counter, is_slice_active, virtual_queues, slices_json_path)
    else:
        with open(slices_json_path, "r", encoding="utf-8") as f:
            slices_options = json.load(f)[0]

        slice_nodes_path = slices_options["slice_nodes_path"]
        port_to_slice = slices_options["port_to_slice"]
        is_slice_active = slices_options["active_slices"]
        virtual_queues = slices_options["virtual_queues"]
        slice_counter = int(max(is_slice_active, key=int)) + 1


    while True:
        while True:
            operation = get_positive_integer(
                "'1' to define a slice, \n"
                + "'2' to activate an existing slice \n"
                + "'3' to deactivate a slice \n"
                + "'4' to define a virtual queue \n"
                + "'5' to exit \n"
            )

            if operation > 5:
                print("Error, the value written must to be between '1' and '5'")
            else:
                break

        slice_counter, slice_nodes_path, port_to_slice, is_slice_active = execute_operation(operation, slice_nodes_path, port_to_slice, slice_counter, is_slice_active, virtual_queues, slices_json_path)
