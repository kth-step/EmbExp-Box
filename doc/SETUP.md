# Setting up a box server


## Install dependencies
The program `python3` should be at least Python 3.7 (tested with Python 3.7.3).
Run the following commands.
- general
  ```
  sudo apt install git
  sudo apt install screen
  sudo apt install dnsutils ethtool
  sudo apt install rsync
  ```
- python (install for all, is something like this needed? `umask 022`)
  ```
  sudo apt install python3-pip
  sudo pip3 install nanpy
  sudo pip3 install pyserial
  ```
- OpenOCD
  ```
  sudo apt install make gcc
  sudo apt install libtool autotools-dev automake pkg-config
  sudo apt install libusb-dev libusb-1.0-0-dev libusb-1.0-doc
  sudo apt install libhidapi-dev
  sudo apt install libftdi-dev
  ```


## Compile OpenOCD
Run the following commands.
```
cd {EMBEXP-BOX}
git submodule init
git submodule update
cd tools/openocd
git clean -dfx
./bootstrap
./configure --enable-jlink --enable-ftdi --enable-stlink --enable-cmsis-dap --enable-openjtag
make -j4
```


## Setup network configuration
1. Fix the IP of the server. This has to be done at least for the experiment network interface. (for Raspbian additionally: Switch to standard Debian networking.)
   1. Determine interface names with `ip a`.
   1. Adjust `/etc/network/interfaces`.
      ```
      # The primary network interface
      allow-hotplug enp6s0
      iface enp6s0 inet static
      	address 192.168.51.44
      	netmask 255.255.255.0
      	gateway 192.168.51.254
      #	address 130.237.224.32
      #	netmask 255.255.255.0
      #	gateway 130.237.224.1
      
      # The experiment network interface
      allow-hotplug enx00e04c680037
      iface enx00e04c680037 inet static
      	address 192.168.0.254
      	netmask 255.255.255.0
      ```
   1. Raspbian: `sudo systemctl disable dhcpcd`
   1. Raspbian: `sudo systemctl enable networking`
   1. Raspbian: `sudo reboot`
   1. Adjust `/etc/resolv.conf`. See below.
      ```
      nameserver 127.0.0.1
      nameserver 8.8.8.8
      ```
   1. `sudo chattr +i /etc/resolv.conf`

1. Disable IPv6.
   - Raspbian: Adjust `sudo nano /boot/cmdline.txt`.
     - Add this at the end of the command line ` ipv6.disable=1`
   - Debian: Adjust `/etc/sysctl.conf`.
     - Add `net.ipv6.conf.all.disable_ipv6 = 1` and then run `sudo sysctl -p`

1. Configure SSH daemon to use keep alive messages.
   - Adjust `/etc/ssh/sshd_config`.
     ```
     TCPKeepAlive yes
     KeepAlive yes
     ClientAliveInterval 60
     ClientAliveCountMax 10
     ```


## DHCP/TFTP server
1. Install and setup dnsmasq for DNS and DHCP.
   1. `sudo apt update`
   1. `sudo apt install dnsmasq tcpdump`
   1. Disable dnsmasq interfering with DNS resolution.
      1. `sudo rm /etc/resolvconf/update.d/dnsmasq`
      1. `sudo reboot`
   1. Create dnsmasq config. Also, to disable dnsmasq on the interface to the internet, only on our experiment network!
      1. `sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.bak`
      1. `echo | sudo tee /etc/dnsmasq.conf`
      1. Adjust `/etc/dnsmasq.conf`. NOTICE: Make sure to fill in the internet interface for no-dhcp!
         ```
         no-dhcp-interface=enp6s0
         
         #port=0
         #dhcp-range=130.237.224.255,proxy
         dhcp-range=192.168.0.50,192.168.0.150,255.255.255.0,12h
         log-dhcp
         enable-tftp
         tftp-root=/tftpboot
         pxe-service=0,"Raspberry Pi Boot"
         ```

1. Create the TFTP directory.
   1. `sudo mkdir /tftpboot`
   1. `sudo chmod 777 /tftpboot`
   1. `sudo systemctl enable dnsmasq.service`
   1. `sudo systemctl restart dnsmasq.service`

1. Restart dnsmasq.
   1. `sudo systemctl restart dnsmasq`

1. Prepare files in `/tftpboot`. See `MAINTENANCE.md`.


## NFS server
1. Run the following commands.
   ```
   sudo apt install nfs-kernel-server
   sudo systemctl enable rpcbind
   sudo systemctl restart rpcbind
   sudo systemctl enable nfs-kernel-server
   sudo systemctl restart nfs-kernel-server
   sudo mkdir /nfs
   sudo mkdir /nfs_master
   ```

1. Prepare root directories in `/nfs`, export them and use them as rootfs for Linux. See `MAINTENANCE.md`.


## Final startup configuration
- Create the file `/etc/rc.local` if it does not exist and execute `chmod +x /etc/rc.local`. Otherwise, just add the two lines for selecting the experiment network interface and running the startup script in your file.
  ```
  #!/bin/sh -e
  
  # select experiment network interface
  export EXPERIMENT_IF=enx00e04c680037
  # line for the startup stript
  /opt/embexp-box/tools/startup/startup.sh
  
  exit 0
  ```

- Configure the firewall
  - Configure the variable EXPERIMENT_IF to match your experiment network interface name. All traffic will be allowed for this interface!
  - Adjust `{EMBEXP-BOX}/tools/startup/firewall.sh`. (Normally nothing extra needs to be done here.)

- Notice: You may want to copy these startup files somewhere else and execute from there in order to better control modifications to it.


## Group `devel` and user access
- Create the devel group with `sudo groupadd devel`

- `/etc/sudoers`
  ```
  # Group devel specification (e.g. allow 'sudo reboot')
  %devel	ALL=NOPASSWD:/sbin/reboot
  ```

- udev - user access to devices
  1. `sudo cp {EMBEXP-BOX}/tools/openocd/contrib/60-openocd.rules /etc/udev/rules.d/`
  1. `sudo reboot`

- Refer to `MAINTENANCE.md` for how to create new users.



