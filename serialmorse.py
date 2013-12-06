import serial
import time
import pyo
import select
import argparse
import sys


def main(serial_device, audio_device, freq, vol):

    # Set up and open the serial device
    try:
        ser = serial.Serial(serial_device,
                            baudrate=115200, rtscts=True)
    except (OSError, serial.SerialException) as e:
        print e
        sys.exit()
    ser.setRTS(True)  # Just in case

    # Set up audio
    pyoserv = pyo.Server(nchnls=1, audio=audio_device, duplex=0,
                         jackname='serialmorse').boot()
    pyoserv.setVerbosity(1)
    pyoserv.start()
    pyowave = pyo.Sine(freq=freq, mul=vol / float(100))

    # Loop and poll the CTS line. If you know how to do a
    # callback-style CTS line checking in a portable way, please open
    # an issue on GitHub. I did not find anything in pyserial or
    # twisted that would be of help.
    print "\nSerialmorse started. Go ahead. Press Enter to exit.\n"
    keystatus = False
    while(1):
        # Do a non-blocking select on stdin to see if Enter has been pressed.
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()  # Consume the line
            break
        # To avoid a complete busy wait, we poll the CTS line every 50 ms.
        time.sleep(0.005)
        keypoll = ser.getCTS()
        if keystatus != keypoll:
            keystatus = keypoll
            if keystatus is True:
                pyowave.out()
            if keystatus is False:
                pyowave.stop()
                pyowave.reset()  # Reset phase to zero for next play

    ser.close()
    pyoserv.stop()
    pyoserv.shutdown()


def check_freq(freq):
    ifreq = int(freq)
    if ifreq < 20 or ifreq > 22050:
        raise argparse.ArgumentTypeError("Frequency %s should be between 20 and 22050" % ifreq)
    return ifreq


def check_vol(vol):
    ivol = int(vol)
    if ivol < 0 or ivol > 100:
        raise argparse.ArgumentTypeError("Volume %s should be between 0 and 100" % ivol)
    return ivol


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Serial port Morse beeper. Read the installation and usage instructions on https://github.com/anttivs/serialmorse.')
    parser.add_argument('device', metavar='serial_device',
                        type=str,
                        help='Serial port name to which your key is connected, usually in /dev')
    parser.add_argument('-freq', metavar='frequency',
                        type=check_freq, required=False,
                        default=440, help='Sidetone (beep) pitch in Hz')
    parser.add_argument('-vol', metavar='volume',
                        type=check_vol, required=False,
                        default=50, help='Volume (amplitude) from 0 to 100')
    parser.add_argument('-audiodev', metavar='audio_output',
                        choices=['jack', 'coreaudio', 'portaudio'],
                        required=False,
                        default='jack', help='Audio output device if not using JACK (e.g., coreaudio on Mac, portaudio on Linux)')
    args = parser.parse_args()
    main(args.device, args.audiodev, args.freq, args.vol)
