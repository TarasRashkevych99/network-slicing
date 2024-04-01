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


def get_hosts_to_switches_map(n_host, n_switch):
    host_to_switch = {}
    for i in range(n_host):
        while True:
            switch_id = get_positive_integer(f"To which switch link the host h{i+1}: ")
            if switch_id <= n_switch:
                host_to_switch[i] = switch_id - 1  # -1 to get right index
                break
            else:
                print(f"Error, the switch must to be between 1 and {n_switch}")
    print("\n")
    return host_to_switch


def get_hosts_macs_to_switches_ports(host_to_switch):
    mac_to_port = {}

    switches_used = set(host_to_switch.values())

    for switch in switches_used:
        host_attached = {}
        port_counter = 1

        for key, value in host_to_switch.items():
            if value == switch:
                hex_string = "{:X}".format(key + 1)

                padded_hex_string = hex_string.zfill(12)

                mac_address = ":".join(
                    [
                        padded_hex_string[i : i + 2]
                        for i in range(0, len(padded_hex_string), 2)
                    ]
                )

                host_attached[mac_address] = port_counter
                port_counter = port_counter + 1

        mac_to_port[switch + 1] = host_attached

    return mac_to_port


def get_links():
    link_dict = {}
    n_links = get_positive_integer(
        "Insert the number of links' type that will be added between switches: "
    )

    for i in range(n_links):
        while True:
            link_name = input(f"Insert the name of the link {str(i)}: ")

            if link_name == "":
                print("Error, the name specified must to be non empty.")
            elif link_name == "host":
                print("Error, the name couldn't be host.")
            elif link_name in link_dict:
                print("Error, the name specified already exists.")
            else:
                break

        link_bw = get_positive_integer(
            f"Insert the bandwidth of the link {link_name} (in Mbps): "
        )

        link_dict[link_name] = link_bw

        print("\n")

    return link_dict


def add_links_among_switches(link_dict, n_switch):
    link_added = {}

    for i in range(n_switch):
        for j in range(i + 1, n_switch):
            while True:
                link_used = input(
                    "Insert the link name between s"
                    + str(i + 1)
                    + " and s"
                    + str(j + 1)
                    + " (return if you don't want to add a link): "
                )

                if link_used in link_dict or link_used == "":
                    break
                else:
                    print("Error, the name specified does not exists.")

            if not link_used == "":
                link_added[i] = {"link_name": link_used, "destination_switch_id": j}

    return link_added


if __name__ == "__main__":
    number_of_hosts = get_positive_integer("Insert the number of hosts: ")
    if number_of_hosts == 1:
        print("There will be added 1 host, named h1\n")
    else:
        print(
            f"There will be added {str(number_of_hosts)} hosts, from h1 to h{str(number_of_hosts)}\n"
        )

    number_of_switches = get_positive_integer("Insert the number of switches: ")
    if number_of_switches == 1:
        print("There will be added 1 switch, named s1\n")
    else:
        print(
            f"There will be added {str(number_of_switches)} switches, from s1 to s{str(number_of_switches)}\n"
        )

    hosts_to_switches_map = get_hosts_to_switches_map(
        number_of_hosts, number_of_switches
    )

    links = get_links()

    links_among_switches = add_links_among_switches(links, number_of_switches)

    hosts_macs_to_switches_ports = get_hosts_macs_to_switches_ports(
        hosts_to_switches_map
    )

    network_config = (
        {
            "number_of_hosts": number_of_hosts,
            "number_of_switches": number_of_switches,
            "hosts_to_switches_map": hosts_to_switches_map,
            "hosts_macs_to_switches_ports": hosts_macs_to_switches_ports,
            "links": links,
            "links_among_switches": links_among_switches,
        },
    )

    with open("topology.json", "w", encoding="utf-8") as f:
        json.dump(network_config, f, ensure_ascii=False, indent=4)
