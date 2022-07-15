"""Keithley 2410 simulation on TCP socket."""

import socketserver
import random, time
import datetime
import argparse
import re


class K2410Handler(socketserver.BaseRequestHandler):

    state = {"OUTP": 0, "VDC": 0.0}

    write_termination = "\r\n"

    channels = 10

    average_enable = 0
    average_type = "REP"
    average_count = 10

    def recv(self, n):
        data = self.request.recv(1024)
        if data:
            print("recv ({}, {})".format(len(data), data), flush=True)
        return data.decode()

    def send(self, message):
        data = "{}{}".format(message, self.write_termination).encode()
        self.request.send(data)
        print("send ({}, {})".format(len(data), data), flush=True)

    def handle(self):
        # Keep socket alive
        while True:
            time.sleep(0.100)  # throttle
            for data in self.recv(1024).split("\r\n"):
                data = data.strip()

                if re.match(r"\*IDN\?", data):
                    self.send("Keithley 2410 Emulator, Spanish Inquisition Inc.")

                elif re.match(r"\*OPC\?", data):
                    self.send("1")

                elif re.match(r"\*ESR\?", data):
                    self.send("1")

                elif re.match(r"\:SYST\:ERR\?", data):
                    self.send('0,"no error"')

                elif re.match(r"\:SENS\:VOLT\:AVER\:STAT\?", data):
                    self.send("{:d}".format(type(self).average_enable))

                elif re.match(r"\:SENS\:VOLT\:AVER\:STAT\s+(ON|OFF|1|0)", data):
                    value = data.split()[-1]
                    type(self).average_enable = {"ON": 1, "OFF": 0, "1": 1, "0": 0}[
                        value
                    ]

                elif re.match(r"\:SENS\:VOLT\:AVER\:TCON\?", data):
                    self.send(type(self).average_type)

                elif re.match(r"\:SENS\:VOLT\:AVER\:TCON\s+(MOV|REP)", data):
                    value = data.split()[-1]
                    type(self).average_type = value

                elif re.match(r"\:SENS\:VOLT\:AVER\:COUN\?", data):
                    self.send("{:d}".format(type(self).average_count))

                elif re.match(r"\:SENS\:VOLT\:AVER\:COUN\s+(\d+)", data):
                    value = int(data.split()[-1])
                    type(self).average_count = value

                elif re.match(r"\:?SENS\:CURR\:PROT\:TRIP\?", data):
                    self.send("0")

                elif re.match(r"\:?SOUR\:VOLT\:LEV\?", data):
                    self.send(self.state.get("VDC"))

                elif re.match(r"\:?SOUR\:VOLT\:LEV\s+[\w\.\+\-]+", data):
                    value = data.split()[1].lower()
                    self.state["VDC"] = float(value)

                elif re.match(r"\:?OUTP\?", data):
                    self.send(self.state.get("OUTP"))

                elif re.match(r"\:?OUTP\s+[\w\.\+\-]+", data):
                    value = data.split()[1].lower()
                    self.state["OUTP"] = {"0": 0, "1": 1, "off": 0, "on": 1}[value]

                elif re.match(r"\:?READ\?", data):
                    self.send(
                        ",".join(
                            [format(random.uniform(0.000020, 0.0000245), "E")] * 10
                        )
                    )

                elif re.match(r"\:?FETC[h]?\?", data):
                    values = []
                    for i in range(self.channels):
                        vdc = self.state.get("VDC") + random.random(-0.1, +0.1)
                        values.append("{:E}VDC,+0.000SECS,+0.0000RDNG#".format(vdc))
                    self.send(",".join(values))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default=10002, type=int)
    args = parser.parse_args()

    print("Keithley 2410 simulation...")
    print("serving on port", args.port)

    server = socketserver.ThreadingTCPServer((args.host, args.port), K2410Handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()

    print("K2410 simulation stopped.")


if __name__ == "__main__":
    main()
