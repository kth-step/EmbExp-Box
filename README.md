# EmbExp-Box - embedded experiments in a box
The software components used here are:
- BoxServer: claim and power management
- SerialRedirector: communication
- OpenOCD: JTAG gdb debugging
- DHCP/TFTP: for experiment network, TFTP advertising, and TFTP network boot
- NFS: network file system for linux boot


## Setup outline
Refer to `doc/SETUP.md` for the detailed steps. The essential points are:
- Network configuration
- DHCP/TFTP
- NFS
- Startup scripts for firewall setup and BoxServer startup
- User management and device access


## Box building outline
Refer to `doc/HARDWARE.md` for the detailed steps.


## Maintenance outline
Refer to `doc/MAINTENANCE.md` for the detailed steps.


## Directory index
- `config`
  - Configuration for BoxServer
  - OpenOCD configuration files
- `doc`
  - Setup guide
  - Hardware guid with pictures
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
  - RaspberryPi firmware and kernel binaries (boot)



