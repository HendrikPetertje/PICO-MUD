import socket


class DNSServer:
    """
    Minimal DNS responder. Answers ALL A-record queries with the Pi's IP.
    This makes every domain resolve to the Pi, which triggers the OS
    captive portal detector and pops up the browser automatically.
    """

    def __init__(self, ip):
        self.ip = ip
        self._ip_bytes = bytes(int(x) for x in ip.split("."))

    def _question_end(self, data):
        i = 12
        while i < len(data):
            length = data[i]
            if length == 0:
                i += 1
                break
            if length & 0xC0 == 0xC0:
                i += 2
                break
            i += 1 + length
        i += 4  # skip QTYPE + QCLASS
        return i

    def _build_response(self, data):
        tid = data[:2]
        flags = b"\x85\x80"
        qdcount = data[4:6]
        ancount = b"\x00\x01"
        nscount = b"\x00\x00"
        arcount = b"\x00\x00"

        q_end = self._question_end(data)
        question = data[12:q_end]

        answer = (
            b"\xc0\x0c"
            b"\x00\x01"
            b"\x00\x01"
            b"\x00\x00\x00\x1e"  # TTL 30s
            b"\x00\x04"
            + self._ip_bytes
        )

        return tid + flags + qdcount + ancount + nscount + arcount + question + answer

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 53))
        print("DNS server running")
        try:
            while True:
                try:
                    data, addr = sock.recvfrom(512)
                    if len(data) < 12:
                        continue
                    if data[2] & 0xF8 != 0:
                        continue
                    response = self._build_response(data)
                    sock.sendto(response, addr)
                except Exception as e:
                    print("DNS error:", e)
        finally:
            sock.close()
