#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
import json


class NetworkSlicingTopo(Topo):
    def __init__(self):
        # Initialize topology
        Topo.__init__(self)

        topology = get_topology()
        number_of_hosts = topology["number_of_hosts"]
        number_of_switches = topology["number_of_switches"]
        hosts_to_switches_map = topology["hosts_to_switches_map"]
        links = topology["links"]
        links_among_switches = topology["links_among_switches"]

        # Create template host, switch, and link
        host_config = dict(inNamespace=True)
        host_link_config = dict()

        for i in range(number_of_hosts):
            self.addHost("h%d" % (i + 1), **host_config)

        for i in range(number_of_switches):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), **sconfig)

        for host in hosts_to_switches_map:
            self.addLink(
                "h%d" % (int(host) + 1),
                "s%d" % (hosts_to_switches_map[host] + 1),
                **host_link_config,
            )

        for origin_switch_id, connections in links_among_switches.items():
            for destination_switch_id, link_name in connections.items():
                self.addLink(
                    "s%d" % (int(origin_switch_id) + 1),
                    "s%d" % (int(destination_switch_id) + 1),
                    **dict(bw=links[link_name]),
                )


def get_topology():
    try:
        with open("topology.json") as f:
            topology = json.load(f)
            return topology[0]
    except FileNotFoundError:
        print("The topology file was not found, you have to generat it first")
        exit()


topos = {"networkslicingtopo": (lambda: NetworkSlicingTopo())}

if __name__ == "__main__":
    topo = NetworkSlicingTopo()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)
    net.build()
    net.start()
    CLI(net)
    net.stop()
