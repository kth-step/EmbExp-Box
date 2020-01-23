# Maintaining boards and users in the server


## Find USB devices and serial numbers (just notes for now)
- `find /sys/devices -name "ttyUSB*"`
  ```
  /sys/devices/pci0000:00/0000:00:15.0/0000:03:00.0/usb3/3-2/3-2.1/3-2.1:1.0/ttyUSB1/tty/ttyUSB1
  /sys/devices/pci0000:00/0000:00:15.0/0000:03:00.0/usb3/3-2/3-2.1/serial
  /dev/serial/by-id/usb-FTDI_FT2232H_MiniModule_FTXK0VDJ-if01-port0
  ```
- `ls -la /dev/serial/by-id`


## Find network booting RPi
1. `sudo tcpdump -i enx00e04c680037 port bootpc`
1. The client asks for DHCP: `BOOTP/DHCP, Request from {MAC address}`.
1. Reply should be sent by our BOOTP/DHCP server.
1. `sudo tail -F /var/log/daemon.log` should show that `/tftpboot/bootcode.bin` cannot be found.


## Prepare TFTP for RPi network boot
1. Prepare some network boot options
   - `cp -r {EMBEXP-BOX}/tools/firmware/boot_{thelatest} /tftpboot/raspbian_{thelatest}`
   - `cp -r {EMBEXP-BOX}/tools/firmware/custom/rpi3_jtag_aarch64 /tftpboot/`
   - `cp -r {EMBEXP-BOX}/tools/firmware/custom/rpi2_jtag /tftpboot/`

1. Link the boot options for the respective devices (see `boxes.json` file for the `TFTP` ids), for example:
   - `ln -s /tftpboot/rpi3_jtag_aarch64 /tftpboot/79ae849b`
   - `ln -s /tftpboot/rpi3_jtag_aarch64 /tftpboot/ce3e32b9`
   - `ln -s /tftpboot/rpi3_jtag_aarch64 /tftpboot/7c648f61`
   - `ln -s /tftpboot/rpi2_jtag /tftpboot/08ba2f58`


## Prepare a new master rootfs for RPi
1. Flash a Raspbian Lite image on an SD card.
1. Mount it in the server with (adjust the device name)
   `sudo mount /dev/sdb2 /mnt`.
1. Copy it to the local rootfs master store (adjust the directory name)
   `sudo rsync -xa --progress /mnt/ /nfs_master/raspbian_lite_2019_07_10`.
1. Unmount the SD card and remove it with
   `sudo umount /dev/sdb2`.


## Prepare a derived rootfs (TBD, old notes follow)
1. Prepare root filesystem for the client RPi3
   1. `sudo mkdir /nfs/client1`
   1. mount a diff filesystem
1. Export rootfs via NFS
   1. `echo "/nfs/client1 *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports`
1. Use the exported rootfs for Raspbian
   1. Fix the linux boot command in `/tftpboot/cmdline.txt` by replacing `root=` to the end with `root=/dev/nfs nfsroot=192.168.0.254:/nfs/client1,vers=3 rw ip=dhcp rootwait elevator=deadline`.
   1. Fix the linux filesystem table in `/nfs/client1/etc/fstab` by removing the lines mentioning `/dev/mmcblkp1` and `/dev/mmcblkp2`. Only `proc` should be left in this file.


## Create a new user
1. `sudo adduser USERNAME`
1. `sudo usermod -aG devel USERNAME`
1. `sudo usermod -aG plugdev USERNAME`
1. setup ssh keys
   - `ssh-copy-id "-p 4422 USERNAME@tcs79.csc.kth.se"`, or
   - create `/home/USERNAME/.ssh/authorized_keys`, `chmod 700 /home/USERNAME/.ssh`, `chmod 600 /home/USERNAME/.ssh/authorized_keys`


## Known issues
- minimodule (JTAG/serial) communication/driver issue?
  - device cannot be found by openocd
  - `lsusb -v` output stutters (most likely runs into timeouts) and prints `(error)` where the serial number of the device is supposed to be
  - a box power down and power up and `tools/usbreset` solves the issue


