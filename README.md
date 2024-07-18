# Network-slicing
This repository provides a dynamic network slicing implementation of a user-defined network

## Instructions
In order to run the project it is required to clone the repository into a [comnetsemu](https://git.comnets.net/public-repo/comnetsemu) testbed.

### STEP 0
Clean your enviroment to remove the existing interfaces
```sh
sudo mn -c
```


### STEP 1
Generate the topology by doing:
```sh
cd src
sudo python3 generate_topology.py
```
And by following the CLI indications.

### STEP 2
Runs the following commands in order to run respectively the slicing tool, the ryu controller and the mininet emulator on 3 different terminal's windows:
```sh
cd src
sudo python3 admin_service_slicing_tool.py
```
```sh
cd src
ryu-manager controller.py
```
```sh
cd src
sudo python3 create_network.py
```
The commands must to be executed in this precise order.

## Provided examples
2 examples were already provided in the repo in order to test the project without generating a new topology and the related slices.

### Scenario 1

![scenario 1 with 4 hosts and 3 slices](/images/scenario_1.png)
**Caveat**: In order to run the topology provided as an example, don't run generate_topology.py that will overwrite, otherwise, the already provided one. In addition, while executing admin_service_slicing_tool.py specify through the CLI the desire to use the existing slices.json file.

The following scenario can be executed by doing:
```sh
sudo mn -c
```
```sh
cd src
ryu-manager controller.py
```
```sh
cd src
sudo python3 create_network.py
```
```sh
cd src
sudo python3 admin_service_slicing_tool.py
```

### Testing the slices

To test the network connectivity:
```sh
pingall
```

To test the DEFAULT slice:
```sh
h4 iperf -s -u -p 110 -b 100M &
h1 iperf -c 10.0.0.4 -u -b 100M -p 110 -t 10 -i 1
```

To test the VIDEO STREAMING slice:
```sh
h4 iperf -s -u -p 554 -b 100M &
h1 iperf -c 10.0.0.4 -u -b 100M -p 554 -t 10 -i 1
```

To test the HTTP slice:
```sh
h4 iperf -s -u -p 80 -b 100M &
h1 iperf -c 10.0.0.4 -u -b 100M -p 80 -t 10 -i 1
```

To activate and deactivate the existing slices use respectively the option '2' and '3' within the slicing tool menu.