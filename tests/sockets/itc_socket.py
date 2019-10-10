"""CTS climate chamber simulation on TCP socket."""

import socketserver
import random, time
import datetime
import argparse
import re

def fake_analog_channel(channel, minimum, maximum):
    """Retruns analog channel fake reading."""
    actual = random.uniform(minimum, maximum)
    target = random.uniform(minimum, maximum)
    return '{} {:05.1f} {:05.1f}'.format(channel, actual, target)

class ClimateHandler(socketserver.BaseRequestHandler):

    temp = 24.0
    humid = 55.0

    def recv(self, n):
        data = self.request.recv(1024)
        if data:
            print('recv ({}, {})'.format(len(data), data), flush=True)
        return data.decode()

    def send(self, message):
        data = message.encode()
        self.request.send(data)
        print('send ({}, {})'.format(len(data), data), flush=True)

    def handle(self):
        # Keep socket alive
        while True:
            time.sleep(.100) # throttle
            data = self.recv(1024)

            if re.match(r'T', data):
                dt = datetime.datetime.now().strftime('T%d%m%y%H%M%S')
                self.send(dt)

            elif re.match(r't\d{12}', data):
                t = datetime.datetime.strptime(data, 't%d%m%y%H%M%S')
                dt = t.strftime('T%d%m%y%H%M%S')
                self.send(dt)

            elif re.match(r'A0', data):
                self.temp += random.uniform(-.25, +.25)
                self.temp = min(60., max(20., self.temp))
                self.send("{} {:05.1f} {:05.1f}".format(data, self.temp, 24.0))

            elif re.match(r'A[34]', data):
                result = fake_analog_channel(data, -45., +185.)
                self.send(result)

            elif re.match(r'A1', data):
                self.humid += random.uniform(-.25, +.25)
                self.humid = min(95., max(15., self.humid))
                self.send("{} {:05.1f} {:05.1f}".format(data, self.humid, 55.0))

            elif re.match(r'A2', data):
                result = fake_analog_channel(data, +0., +15.)
                self.send(result)

            elif re.match(r'A[56]', data):
                result = fake_analog_channel(data, +5., +98.)
                self.send(result)

            elif re.match(r'A7', data):
                result = fake_analog_channel(data, -50., +150.)
                self.send(result)

            elif re.match(r'A8', data):
                result = fake_analog_channel(data, -80., +190.)
                self.send(result)

            elif re.match(r'A9', data):
                result = fake_analog_channel(data, -0., +25.)
                self.send(result)

            elif re.match(r'A\:', data):
                result = fake_analog_channel(data, -50., +100.)
                self.send(result)

            elif re.match(r'A\;', data):
                result = fake_analog_channel(data, -0., +25.)
                self.send(result)

            elif re.match(r'A\<', data):
                result = fake_analog_channel(data, +2., +5.)
                self.send(result)

            elif re.match(r'A[\=\>]', data):
                result = fake_analog_channel(data, -100., +200.)
                self.send(result)

            elif re.match(r'A\?', data):
                result = fake_analog_channel(data, -80., +200.)
                self.send(result)

            elif re.match(r'a[1-7]\s(-?\d+.\d)', data):
                self.send('a')

            elif re.match(r'S', data):
                result = 'S11110100\x06'
                self.send(result)

            elif re.match(r'P', data):
                result = 'P000'
                self.send(result)

            elif re.match(r'P\d{3}', data):
                self.send(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=1080, type=int)
    args = parser.parse_args()

    print("CTS simulation...")
    print("serving on port", args.port)

    server = socketserver.ThreadingTCPServer((args.host, args.port), ClimateHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()

    print("CTS simulation stopped.")

if __name__ == "__main__":
    main()
