"""HEPHY ShuntBox simulation on TCP socket."""

import socketserver
import random, time
import datetime
import argparse
import re

start_time = time.time()
def uptime():
    return int(round(time.time() - start_time))

class ShuntBoxHandler(socketserver.BaseRequestHandler):

    write_termination = '\n'

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
                    self.send("HEPHY ShuntBox Emulator, Spanish Inquisition Inc.")

                if re.match(r'GET:UP \?', data):
                    self.send(f'{uptime():d}')

                if re.match(r'GET:RAM \?', data):
                    self.send('4242')

                elif re.match(r'GET:TEMP ALL', data):
                    values = []
                    for i in range(self.channels):
                        temp = random.uniform(22.0, 26.0)
                        values.append("{:.1f}".format(temp))
                    self.send(",".join(values))

                elif re.match(r'GET:TEMP \d+', data):
                    self.send(format(random.uniform(22.0, 26.0), '.1f'))

                elif re.match(r'SET:REL_(ON|OFF) (\d+|ALL)', data):
                    self.send("OK")

                elif re.match(r'GET:REL (\d+)', data):
                    self.send("0")

                elif re.match(r'GET:REL ALL', data):
                    self.send(",".join(["0"] * self.channels + 4))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=10003, type=int)
    args = parser.parse_args()

    print("ShuntBox simulation...")
    print("serving on port", args.port)

    server = socketserver.ThreadingTCPServer((args.host, args.port), ShuntBoxHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()

    print("ShuntBox simulation stopped.")

if __name__ == "__main__":
    main()
