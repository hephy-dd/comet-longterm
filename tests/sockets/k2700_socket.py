"""Keithley 2700 simulation on TCP socket."""

import socketserver
import random, time
import datetime
import argparse
import re

class K2700Handler(socketserver.BaseRequestHandler):

    write_termination = '\r'

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
            data = self.recv(1024).strip()

            if re.match(r'\*IDN\?', data):
                self.send("Keithley 2700 Emulator, Spanish Inquisition Inc.")

            elif re.match(r'\*[A-Z]+', data):
                pass

            elif re.match(r'\:?READ\?', data):
                self.send(",".join(["24.000"]*10))

            elif re.match(r'\:?FETC[h]?\?', data):
                self.send(",".join(["-4.32962079e-05VDC,+0.000SECS,+0.0000RDNG#"]*10))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=10001, type=int)
    args = parser.parse_args()

    print("Keithley 2410 simulation...")
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
