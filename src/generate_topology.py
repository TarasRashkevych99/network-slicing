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


def get_hosts_to_switches_map(n_host, n_switch, switches_port_next_id):
    host_to_switch = {}
    for i in range(1, n_host + 1):
        while True:
            switch_id = get_positive_integer(f"To which switch link the host h{i}: ")
            if switch_id <= n_switch:
                host_to_switch[i] = switch_id
                switches_port_next_id[switch_id] += 1
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
                hex_string = "{:X}".format(key)

                padded_hex_string = hex_string.zfill(12)

                mac_address = ":".join(
                    [
                        padded_hex_string[i : i + 2]
                        for i in range(0, len(padded_hex_string), 2)
                    ]
                )

                host_attached[mac_address] = port_counter
                port_counter = port_counter + 1

        mac_to_port[switch] = host_attached

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


def add_links_among_switches(link_dict, n_switch, switches_port_next_id):
    link_added = {}
    edges_to_ports = {}
    out_port_to_switch = {}

    for i in range(1, n_switch + 1):
        for j in range(i + 1, n_switch + 1):
            while True:
                link_used = input(
                    "Insert the link name between s"
                    + str(i)
                    + " and s"
                    + str(j)
                    + " (return if you don't want to add a link): "
                )

                if link_used in link_dict or link_used == "":
                    break
                else:
                    print("Error, the name specified does not exists.")

            if not link_used == "":
                if not i in link_added:
                    link_added[i] = {}
                link_added[i][j] = link_used

                if not j in link_added:
                    link_added[j] = {}
                link_added[j][i] = link_used

                if not i in edges_to_ports:
                    edges_to_ports[i] = {}
                edges_to_ports[i][j] = (
                    switches_port_next_id[i],
                    switches_port_next_id[j],
                )

                if not j in edges_to_ports:
                    edges_to_ports[j] = {}
                edges_to_ports[j][i] = edges_to_ports[i][j][::-1]

                if not i in out_port_to_switch:
                    out_port_to_switch[i] = {}
                out_port_to_switch[i][switches_port_next_id[i]] = j

                if not j in out_port_to_switch:
                    out_port_to_switch[j] = {}
                out_port_to_switch[j][switches_port_next_id[j]] = i

                switches_port_next_id[i] += 1
                switches_port_next_id[j] += 1

    return link_added, edges_to_ports, out_port_to_switch


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

    switches_port_next_id = {i: 1 for i in range(1, number_of_switches + 1)}

    hosts_to_switches_map = get_hosts_to_switches_map(
        number_of_hosts, number_of_switches, switches_port_next_id
    )

    links = get_links()

    links_among_switches, edges_to_ports, out_port_to_switch = add_links_among_switches(
        links, number_of_switches, switches_port_next_id
    )

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
            "edges_to_ports": edges_to_ports,
            "out_port_to_switch": out_port_to_switch
        },
    )

    with open("topology.json", "w", encoding="utf-8") as f:
        json.dump(network_config, f, ensure_ascii=False, indent=4)
