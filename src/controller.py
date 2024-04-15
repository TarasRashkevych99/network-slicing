from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp
import importlib.util
import json

class TrafficSlicing(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TrafficSlicing, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def _send_package(self, msg, datapath, in_port, actions):
        data = None
        ofproto = datapath.ofproto
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # IMPORT
        topology = get_topology()

        hosts_to_switches_map = topology["hosts_to_switches_map"]
        mac_to_port = topology["hosts_macs_to_switches_ports"]
        edges_to_ports = topology["edges_to_ports"]
        out_port_to_switch = topology["out_port_to_switch"]

        slices = get_slices()

        port_to_slice = slices["port_to_slice"]
        slice_details = slices["slice_details"]
        active_slices = slices["active_slices"]

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = str(datapath.id)

        if str(dst).startswith("33:33"):
            return

        print("DPID "+dpid)
        print("IN_PORT "+str(in_port))
        print("DEST "+str(dst))

        try:
            prev_switch = out_port_to_switch[dpid][str(in_port)] # switch from which I've received the package
        except:
            prev_switch = None # so package received from a host
        
        print("PREV_SWITCH "+str(prev_switch))

        if dpid in mac_to_port and dst in mac_to_port[dpid]: # if destination reached in next step 
            # TODO also consider if host belongs to slice
            out_port = mac_to_port[dpid][dst]
            
            print("DELIVERING TO HOST "+str(dst))
            print("OUT PORT "+str(out_port)+"\n")

            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            match = datapath.ofproto_parser.OFPMatch(eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)

        elif (pkt.get_protocol(udp.udp)):
            slice_number = str(port_to_slice[str(pkt.get_protocol(udp.udp).dst_port)])
            out_port = get_output_port(dpid,str(prev_switch),slice_details[slice_number]["switches"],edges_to_ports)

            print("DELIVERING THROUGH SLICE "+slice_number)
            print("OUT PORT "+str(out_port)+"\n")

            match = datapath.ofproto_parser.OFPMatch(
                in_port=in_port,
                eth_dst=dst,
                eth_type=ether_types.ETH_TYPE_IP,
                ip_proto=0x11,  # udp
                udp_dst=pkt.get_protocol(udp.udp).dst_port,
            )

            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)

        elif pkt.get_protocol(tcp.tcp):
            slice_number = str(port_to_slice[str(pkt.get_protocol(tcp.tcp).dst_port)])
            out_port = get_output_port(dpid,str(prev_switch),slice_details[slice_number]["switches"],edges_to_ports)

            print("DELIVERING THROUGH SLICE "+slice_number)
            print("OUT PORT "+str(out_port)+"\n")

            match = datapath.ofproto_parser.OFPMatch(
                in_port=in_port,
                eth_dst=dst,
                eth_src=src,
                eth_type=ether_types.ETH_TYPE_IP,
                ip_proto=0x06,  # tcp
                tcp_dst=pkt.get_protocol(tcp.tcp).dst_port,
            )
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)

        elif pkt.get_protocol(icmp.icmp):
            slice_number = str(port_to_slice["ICMP"])
            out_port = get_output_port(dpid,str(prev_switch),slice_details[slice_number]["switches"],edges_to_ports)

            print("DELIVERING THROUGH SLICE "+slice_number)
            print("OUT PORT "+str(out_port)+"\n")

            match = datapath.ofproto_parser.OFPMatch(
                in_port=in_port,
                eth_dst=dst,
                eth_src=src,
                eth_type=ether_types.ETH_TYPE_IP,
                ip_proto=0x01,  # icmp
            )
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)
        else:
            print("ERROR, I'm stucked \n")

def get_output_port(dpid,prev_switch,slice_switches,edges_to_ports):
    dpid_index = slice_switches.index(int(dpid))

    neighbor_switch_indexes = [dpid_index - 1, dpid_index + 1]

    if neighbor_switch_indexes[0] == -1:
        next_switch = slice_switches[neighbor_switch_indexes[1]]
    elif neighbor_switch_indexes[1] == len(slice_switches):
        next_switch = slice_switches[neighbor_switch_indexes[0]]
    elif str(slice_switches[neighbor_switch_indexes[0]]) == prev_switch:
        next_switch = slice_switches[neighbor_switch_indexes[1]]
    else:
        next_switch = slice_switches[neighbor_switch_indexes[0]]
    
    out_port = edges_to_ports[dpid][str(next_switch)][0]

    return out_port


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
