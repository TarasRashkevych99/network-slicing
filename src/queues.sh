#!/bin/sh 

sudo ovs-vsctl set port s1-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000000 \
queues:1=@slice_1 \
queues:2=@slice_2 \
queues:3=@slice_3 -- \
--id=@slice_1 create queue other-config:min-rate=10000 other-config:max-rate=2000000 -- \
--id=@slice_2 create queue other-config:min-rate=10000 other-config:max-rate=6000000 -- \
--id=@slice_3 create queue other-config:min-rate=10000 other-config:max-rate=1000000

sudo ovs-vsctl set port s1-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000000 \
queues:1=@slice_1 \
queues:2=@slice_2 \
queues:3=@slice_3 -- \
--id=@slice_1 create queue other-config:min-rate=10000 other-config:max-rate=2000000 -- \
--id=@slice_2 create queue other-config:min-rate=10000 other-config:max-rate=6000000 -- \
--id=@slice_3 create queue other-config:min-rate=10000 other-config:max-rate=1000000

sudo ovs-vsctl set port s1-eth3 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=15000000 \
queues:1=@slice_1 \
queues:2=@slice_2 -- \
--id=@slice_1 create queue other-config:min-rate=10000 other-config:max-rate=2000000 -- \
--id=@slice_2 create queue other-config:min-rate=10000 other-config:max-rate=6000000

sudo ovs-vsctl set port s2-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=15000000 \
queues:1=@slice_1 \
queues:2=@slice_2 -- \
--id=@slice_1 create queue other-config:min-rate=10000 other-config:max-rate=2000000 -- \
--id=@slice_2 create queue other-config:min-rate=10000 other-config:max-rate=6000000

sudo ovs-vsctl set port s2-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=15000000 \
queues:1=@slice_1 \
queues:2=@slice_2 -- \
--id=@slice_1 create queue other-config:min-rate=10000 other-config:max-rate=2000000 -- \
--id=@slice_2 create queue other-config:min-rate=10000 other-config:max-rate=6000000

sudo ovs-vsctl set port s4-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000000 \
queues:1=@slice_1 -- \
--id=@slice_1 create queue other-config:min-rate=10000 other-config:max-rate=2000000

sudo ovs-vsctl set port s4-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000000 \
queues:2=@slice_2 -- \
--id=@slice_2 create queue other-config:min-rate=10000 other-config:max-rate=6000000

sudo ovs-vsctl set port s4-eth3 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=15000000 \
queues:1=@slice_1 \
queues:2=@slice_2 -- \
--id=@slice_1 create queue other-config:min-rate=10000 other-config:max-rate=2000000 -- \
--id=@slice_2 create queue other-config:min-rate=10000 other-config:max-rate=6000000









sudo ovs-ofctl add-flow s1 ip,priority=65499,nw_src=10.0.0.1,nw_dst=10.0.0.4,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s2 ip,priority=65499,nw_src=10.0.0.1,nw_dst=10.0.0.4,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s4 ip,priority=65499,nw_src=10.0.0.1,nw_dst=10.0.0.4,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s1 ip,priority=65499,nw_src=10.0.0.1,nw_dst=10.0.0.2,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s2 ip,priority=65499,nw_src=10.0.0.1,nw_dst=10.0.0.2,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s4 ip,priority=65499,nw_src=10.0.0.1,nw_dst=10.0.0.2,idle_timeout=0,actions=set_queue:2,normal


sudo ovs-ofctl add-flow s1 ip,priority=65499,nw_src=10.0.0.2,nw_dst=10.0.0.4,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s2 ip,priority=65499,nw_src=10.0.0.2,nw_dst=10.0.0.4,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s4 ip,priority=65499,nw_src=10.0.0.2,nw_dst=10.0.0.4,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s1 ip,priority=65499,nw_src=10.0.0.2,nw_dst=10.0.0.1,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s2 ip,priority=65499,nw_src=10.0.0.2,nw_dst=10.0.0.1,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s4 ip,priority=65499,nw_src=10.0.0.2,nw_dst=10.0.0.1,idle_timeout=0,actions=set_queue:2,normal


sudo ovs-ofctl add-flow s1 ip,priority=65499,nw_src=10.0.0.4,nw_dst=10.0.0.1,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s2 ip,priority=65499,nw_src=10.0.0.4,nw_dst=10.0.0.1,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s4 ip,priority=65499,nw_src=10.0.0.4,nw_dst=10.0.0.1,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s1 ip,priority=65499,nw_src=10.0.0.4,nw_dst=10.0.0.2,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s2 ip,priority=65499,nw_src=10.0.0.4,nw_dst=10.0.0.2,idle_timeout=0,actions=set_queue:2,normal
sudo ovs-ofctl add-flow s4 ip,priority=65499,nw_src=10.0.0.4,nw_dst=10.0.0.2,idle_timeout=0,actions=set_queue:2,normal




sudo ovs-ofctl add-flow s1 tcp,priority=65500,nw_src=10.0.0.1,nw_dst=10.0.0.2,tp_dst=99,idle_timeout=0,actions=set_queue:3,normal
sudo ovs-ofctl add-flow s1 udp,priority=65500,nw_src=10.0.0.1,nw_dst=10.0.0.2,tp_dst=99,idle_timeout=0,actions=set_queue:3,normal


sudo ovs-ofctl add-flow s1 tcp,priority=65500,nw_src=10.0.0.2,nw_dst=10.0.0.1,tp_dst=99,idle_timeout=0,actions=set_queue:3,normal
sudo ovs-ofctl add-flow s1 udp,priority=65500,nw_src=10.0.0.2,nw_dst=10.0.0.1,tp_dst=99,idle_timeout=0,actions=set_queue:3,normal



