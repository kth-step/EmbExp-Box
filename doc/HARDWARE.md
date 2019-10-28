# The box
![The box](pictures/box/box-ext_small.jpg)

## Parts of a box
See the pictures in [`pictures/box`](pictures/box).

* Power supply
* Fan
* USB controller board (Arduino Nano)
* USB power outlets
* USB Hubs

## A RPi module
![RPi module](pictures/rpi/module-1_small.jpg)
See the pictures in [`pictures/rpi`](pictures/rpi).

### Wiring a RPi with a Mini module
USB bus power (VBUS to VCC).
   * CN3-1 to CN3-3

IO and chip power (3.3V to VCCIO).
   * CN2-1 to CN2-11
   * CN2-3 to CN2-21 (not strictly required, but nice to have)
   * CN2-5 to CN3-12 (not strictly required, but nice to have)

GND/TX/RX to RPi.
   * RPi-GND: CN2-2  to 14
   * RPi-TX : CN3-25 to 8  (GPIO14/TXD0)
   * RPi-RX : CN3-26 to 10 (GPIO15/RXD0)

JTAG (Mini module to RPi)
   * RPi to RPi: `1 (V3V3)` to `15 (GPIO22/ARM_TRST)`
   * unconnected: `16 (GPIO23/ARM_RTCK)`
   * `CN2-9` to `18 (Gpio24/ARM_TDO)`
   * `CN2-7` to `22 (Gpio25/ARM_TCK)`
   * `CN2-10` to `37 (Gpio26/ARM_TDI)`
   * `CN2-12` to `13 (Gpio27/ARM_TMS)`

### Prepare SD card with latest firmware files (enables network boot on every RPi and contains bugfixes)
From `{EMBEXP-BOX}/tools/rpi-firmware/boot_{thelatest}`, take the file `bootcode.bin` and copy it on an empty FAT32 formatted SD card.

### Cabling of a RPi module
* Power - micro usb
* Reset - jumper cable gnd and rst, rst with resistor in series (3,9 k ohm)
* UART/JTAG - mini usb
* Ethernet - patch cable



