import json


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


def add_slice(slice_port, slice_to_add):

    input_switch = get_positive_integer("From which switch add the slice: ")
    input_port = get_positive_integer(f"From which port of s{input_switch}: ")

    output_switch = get_positive_integer("To which switch add the slice: ")
    output_port = get_positive_integer(f"From which port of s{output_switch}: ")

    if input_switch in slice_port:
        slice_port[input_switch][slice_to_add] = input_port
    else:
        input_dictionary = {}
        input_dictionary[slice_to_add] = input_port
        slice_port[input_switch] = input_dictionary

    if output_switch in slice_port:
        slice_port[output_switch][slice_to_add] = output_port
    else:
        output_dictionary = {}
        output_dictionary[slice_to_add] = output_port
        slice_port[output_switch] = output_dictionary

    print(f"\nSUCCESS, the slice added can be identified by number {slice_to_add}\n")
    return slice_port


def assign_slice(port_to_slice, slice_to_add):
    while True:
        n_slice = get_positive_integer("Which slice do you want to assign: ")
        if n_slice < slice_to_add:
            break
        else:
            print("ERROR, the specified slice doesn't exists")

    port = get_positive_integer(
        "From which packet port assign the slice (if the port is already assigned, the old slice will be deactivated): "
    )

    port_to_slice[port] = n_slice

    return port_to_slice


def deactivate_slice(port_to_slice, slice_to_add):
    while True:
        n_slice = get_positive_integer("Which slice do you want to deactivate: ")
        if n_slice < slice_to_add:
            break
        else:
            print("ERROR, the specified slice doesn't exists")

    port = int(
        input("From which packet port (type '0' to remove it from everywhere): ")
    )

    if port == 0:
        port_to_slice = {
            key: val for key, val in port_to_slice.items() if val != n_slice
        }
    else:
        if port_to_slice[port] == n_slice:
            del port_to_slice[port]
        else:
            print(
                "ERROR, the specified port-slice mapping to deactivate doesn't exists"
            )

    return port_to_slice


def icmp_slice(port_to_slice, slice_to_add):
    while True:
        n_slice = get_positive_integer("Which slice do you want to use for ICMP: ")
        if n_slice < slice_to_add:
            break
        else:
            print("ERROR, the specified slice doesn't exists")

    port_to_slice["ICMP"] = n_slice

    return port_to_slice


if __name__ == "__main__":
    slice_counter = 1
    slice_port = {}
    port_to_slice = {}

    while True:
        while True:
            operation = get_positive_integer(
                "'1' to define a slice, \n"
                + "'2' to activate an existing ones \n"
                + "'3' to deactivate a slice \n"
                + "'4' to assign/reassign a slice for ICMP\n"
            )

            if operation > 4:
                print("Error, the value written must to be '1' or '4'")
            else:
                break

        if operation == 1:
            slice_port = add_slice(slice_port, slice_counter)
            slice_counter = slice_counter + 1
        elif operation == 2:
            port_to_slice = assign_slice(port_to_slice, slice_counter)
        elif operation == 3:
            port_to_slice = deactivate_slice(port_to_slice, slice_counter)
        elif operation == 4:
            port_to_slice = icmp_slice(port_to_slice, slice_counter)

        slices_options = (
            {
                "port_to_slice": port_to_slice,
                "slice_port": slice_port,
                "end_switches": list(slice_port.keys()),
            },
        )

        with open("slices.json", "w", encoding="utf-8") as f:
            json.dump(slices_options, f, ensure_ascii=False, indent=4)
