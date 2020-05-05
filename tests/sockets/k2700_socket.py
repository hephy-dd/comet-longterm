"""Keithley 2700 simulation on TCP socket."""

import socketserver
import random, time
import datetime
import argparse
import re

class K2700Handler(socketserver.BaseRequestHandler):

    write_termination = '\r'

    channels = 10

    def recv(self, n):
        data = self.request.recv(1024)
        if data:
            print('recv ({}, {})'.format(len(data), data), flush=True)
        return data.decode()

    def send(self, message):
        data = "{}{}".format(message, self.write_termination).encode()
        self.request.send(data)
        print('send ({}, {})'.format(len(data), data), flush=True)

    def handle(self):
        # Keep socket alive
        while True:
            time.sleep(.100) # throttle
            for data in self.recv(1024).split('\r\n'):
                data = data.strip()

                if re.match(r'\*IDN\?', data):
                    self.send("Keithley 2700 Emulator, Spanish Inquisition Inc.")

                elif re.match(r'\*OPC\?', data):
                    self.send("1")

                elif re.match(r'\*ESR\?', data):
                    self.send("1")

                elif re.match(r'\:SYST\:ERR\?', data):
                    self.send('0,"no error"')

                elif re.match(r'\:SAMP\:COUN\s+\d+', data):
                    K2700Handler.channels = int(data.split()[-1])

                elif re.match(r'\:?READ\?', data):
                    self.send(",".join(["0.000024"] * K2700Handler.channels))

                elif re.match(r'\:?FETC[h]?\?', data):
                    values = []
                    for i in range(K2700Handler.channels):
                        vdc = random.uniform(.00025,.001)
                        values.append("{:E}VDC,+0.000SECS,+0.0000RDNG#".format(vdc))
                    time.sleep(random.uniform(.5, 1.0)) # rev B10 ;)
                    self.send(",".join(values))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=10001, type=int)
    args = parser.parse_args()

    print("Keithley 2700 simulation...")
    print("serving on port", args.port)

    server = socketserver.ThreadingTCPServer((args.host, args.port), K2700Handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()

    print("K2410 simulation stopped.")

if __name__ == "__main__":
    main()
