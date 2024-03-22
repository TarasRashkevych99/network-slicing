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

def reassign_slices():
    udp_slice = get_positive_integer("Which slice to use for UDP messages : ")
    tcp_slice = get_positive_integer("Which slice to use for TCP messages : ")
    icmp_slice = get_positive_integer("Which slice to use for ICMP messages : ")

    with open("slice_port.py", "r") as file:
        content = file.readlines()

    for i, line in enumerate(content):
        if "udp_slice" in line:
            content[i] = f"udp_slice = {udp_slice}\n"
        elif "tcp_slice" in line:
            content[i] = f"tcp_slice = {tcp_slice}\n"
        elif "icmp_slice" in line:
            content[i] = f"icmp_slice = {icmp_slice}\n"

    with open("slice_port.py", "w") as file:
        file.writelines(content)

    return udp_slice, tcp_slice, icmp_slice

def add_slice(slice_port, slice_to_add, mac_to_port, udp_slice, tcp_slice, icmp_slice):

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

    end_switches = list(slice_port.keys())

    udp_slice = slice_to_add if input("Do you want to use this slice for UDP messages [y/N]: ").lower() == "y" else udp_slice
    tcp_slice = slice_to_add if input("Do you want to use this slice for TCP messages [y/N]: ").lower() == "y" else tcp_slice
    icmp_slice = slice_to_add if input("Do you want to use this slice for ICMP messages [y/N]: ").lower() == "y" else icmp_slice

    source_code = f"""
slice_port = {slice_port}
end_switches = {end_switches}

udp_slice = {udp_slice}
tcp_slice = {tcp_slice}
icmp_slice = {icmp_slice}
"""
    with open("slice_port.py", "w") as file:
        file.write(source_code)

    print(f"SUCCESS, the slice added can be identified by number {slice_to_add}")
    return slice_port, udp_slice, tcp_slice, icmp_slice



if __name__ == "__main__":
    with open("mac_to_port.py", "r") as file:
        mac_to_port_dict = file.read()

    exec(mac_to_port_dict)

    slice_to_add = 1
    slice_port = {}
    udp_slice = -1
    tcp_slice = -1
    icmp_slice = -1


    while True:
        while True:
            operation = get_positive_integer("'1' to add a slice, \n'2' to activate/deactivate the existing ones \n")

            if operation > 2:
                print("Error, the value written must to be '1' or '2'")
            else:
                break
        
        if operation == 1:
            slice_port, udp_slice, tcp_slice, icmp_slice = add_slice(slice_port, slice_to_add, mac_to_port, udp_slice, tcp_slice, icmp_slice)
            slice_to_add = slice_to_add + 1 
        elif operation == 2:
            udp_slice, tcp_slice, icmp_slice = reassign_slices()    

