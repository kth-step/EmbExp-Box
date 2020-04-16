# EmbExp-Box - embedded experiments in a box
This repository contains an infrastructure for a group of users to remotely or locally develop, debug and run low-level software in a unified manner.
The remote connection just requires a single SSH connection to work, which obviates the need for messy cabling and trivial reoccuring problems when messing with hardware setups.
On the server side, all hardware boards can be contained in a number of boxes that are attached to a server, which together just sit in a remote lab room or simply someone's office.

This infrastructure can be easily integrated to conduct bare-metal software experiments, as well as a component of a continuous integration pipeline or similar tasks.
The companion repository [`EmbExp-ProgPlatform`](https://github.com/kth-step/EmbExp-ProgPlatform) is making use of the `EmbExp-Box` infrastructure to provide a rudimentary bare-metal execution environment for low-level hardware experiments.


## Supported targets
- ARM Cortex-A7 - ARMv7-A (Raspberry Pi 2B)
- ARM Cortex-A53 - ARMv8-A (Raspberry Pi 3B)
- ARM Cortex-A72 - ARMv8-A (Raspberry Pi 4B)
- ARM Cortex-M0 - ARMv6-M (LPCXpresso LPC11C24)
- SiFive Freedom E300 - RV32IMAC (Arty A7-100T)


## Getting started
In order to use this infrastructure, a server is always required.
The first step is to identify the connection parameters of an existing server with a box or build one.
Second, a client connection can be established to the server, or to the local host if the goal is to develop locally.
Refer to the documentation below and in the directory `doc`.
Furthermore, the scripts in the directory `interface` print basic information about their usage when they are executed with the command switch `--help`.


## Software components
Introduced:
- BoxServer: claim and power management
- BoxRemote: remotely connect to BoxServer

Reused:
- xc3sprog: program Arty A7 FPGA
- SerialRedirector: communication
- OpenOCD: JTAG gdb debugging
- DHCP/TFTP: for experiment network, TFTP advertising, and TFTP network boot
- NFS: network file system for linux boot


## Client connection
To establish a connection:
- Place a configuration file in `config/networks.json` following the template [`config/networks.json.example`](config/networks.json.example). This must be suitable for an existing server.
- Run the script `interface/remote.py` to start a remote connection, e.g., `./interface/remote.py rpi3` to connect to a Raspberry Pi 3 using the default connection index.


## Server setup outline
Refer to [`doc/SETUP.md`](doc/SETUP.md) for the detailed steps. The essential points are:
- Network configuration
- DHCP/TFTP
- NFS
- Startup scripts for firewall setup and BoxServer startup
- User management and device access


## Box building outline
Refer to [`doc/HARDWARE.md`](doc/HARDWARE.md) for the detailed steps.


## Maintenance outline
Refer to [`doc/MAINTENANCE.md`](doc/MAINTENANCE.md) for the detailed steps.


## Directory index
- `config`
  - Configuration for BoxServer
  - OpenOCD configuration files
- `doc`
  - Setup guide
  - Hardware guide with pictures
  - Maintenance guide
- `interface`
  - User interface code
- `lib`
  - Python libraries
- `tests`
  - Scripts for testing
- `tools`
  - BoxServer
  - SerialRedirector
  - OpenOCD
  - Startup scripts
  - Firmware and kernel binaries



