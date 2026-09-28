import errno
import gc
import select
import socket
import sys
import time


MAX_OUTPUT_BUFFER = 4096
CLOSE_TIMEOUT_MS = 1000
POLL_INTERVAL_MS = 100
GC_INTERVAL_MS = 5000
READ_SIZE = 256
_EWOULDBLOCK = getattr(errno, "EWOULDBLOCK", errno.EAGAIN)

_DATA = 0
_IAC = 1
_OPTION = 2
_SUBNEGOTIATION = 3
_SUBNEGOTIATION_IAC = 4


def _would_block(error):
    return bool(error.args) and error.args[0] in (errno.EAGAIN, _EWOULDBLOCK)


def _clean_utf8(data):
    """Keep complete, valid UTF-8 sequences; do not rely on decode(errors=...)."""
    result = bytearray()
    i = 0
    while i < len(data):
        first = data[i]
        if first < 128:
            size = 1
        elif 0xC2 <= first <= 0xDF:
            size = 2
        elif 0xE0 <= first <= 0xEF:
            size = 3
        elif 0xF0 <= first <= 0xF4:
            size = 4
        else:
            i += 1
            continue
        valid = i + size <= len(data)
        if valid and size > 1:
            for j in range(1, size):
                if not 0x80 <= data[i + j] <= 0xBF:
                    valid = False
                    break
            second = data[i + 1]
            if (first == 0xE0 and second < 0xA0) or (first == 0xED and second > 0x9F):
                valid = False
            if (first == 0xF0 and second < 0x90) or (first == 0xF4 and second > 0x8F):
                valid = False
        if valid:
            # Unicode C1 control characters are not printable input either.
            if not (size == 2 and first == 0xC2 and data[i + 1] < 0xA0):
                result.extend(data[i:i + size])
            i += size
        else:
            i += 1
    return result.decode("utf-8")


class Client:
    def __init__(self, sock, max_line_length):
        self.sock = sock
        self.max_line_length = max_line_length
        self.output = bytearray()
        self.line = bytearray()
        self.parser_state = _DATA
        self.pending_cr = False
        self.truncated = False
        self.last_activity = time.ticks_ms()
        self.closing_at = None
        self.closed = False
        self.reason = None

    def send(self, text):
        if self.closed or self.closing_at is not None:
            return
        # Reject oversized text before encoding, then check the actual byte size.
        if len(text) > MAX_OUTPUT_BUFFER - len(self.output):
            self.abort("output_overflow")
            return
        encoded = text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
        if len(self.output) + len(encoded) > MAX_OUTPUT_BUFFER:
            self.abort("output_overflow")
            return
        self.output.extend(encoded)

    def capacity(self):
        return MAX_OUTPUT_BUFFER - len(self.output)

    def try_send(self, text):
        if self.closed or self.closing_at is not None:
            return False
        if len(text) > self.capacity():
            return False
        encoded = text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
        if len(encoded) > self.capacity():
            return False
        self.output.extend(encoded)
        return True

    def close(self, message=None):
        if self.closed or self.closing_at is not None:
            return
        if message is not None:
            self.send(message)
        if not self.closed:
            self.reason = "close_requested"
            self.closing_at = time.ticks_ms()

    def abort(self, reason):
        self.reason = reason
        self.closed = True
        self.output = bytearray()

    def flush(self):
        if self.closed:
            return
        if self.output:
            try:
                sent = self.sock.send(self.output)
            except OSError as error:
                if not _would_block(error):
                    raise
            else:
                if sent == 0:
                    self.abort("peer_closed")
                    return
                if sent is not None:
                    self.output = self.output[sent:]
        if self.closing_at is not None:
            if not self.output or time.ticks_diff(time.ticks_ms(), self.closing_at) >= CLOSE_TIMEOUT_MS:
                self.closed = True

    def _finish_line(self):
        text = None if self.truncated else _clean_utf8(self.line)
        self.line = bytearray()
        self.truncated = False
        return text

    def feed(self, data):
        """Yield decoded lines, retaining framing/negotiation state across reads."""
        for byte in data:
            if self.parser_state == _IAC:
                if byte in (251, 252, 253, 254):
                    self.parser_state = _OPTION
                elif byte == 250:
                    self.parser_state = _SUBNEGOTIATION
                else:
                    # IAC IAC is an invalid UTF-8 data byte; other commands have no option.
                    self.parser_state = _DATA
                continue
            if self.parser_state == _OPTION:
                self.parser_state = _DATA
                continue
            if self.parser_state == _SUBNEGOTIATION:
                if byte == 255:
                    self.parser_state = _SUBNEGOTIATION_IAC
                continue
            if self.parser_state == _SUBNEGOTIATION_IAC:
                self.parser_state = _DATA if byte == 240 else _SUBNEGOTIATION
                continue
            if byte == 255:
                self.parser_state = _IAC
                continue

            if self.pending_cr:
                self.pending_cr = False
                if byte in (0, 10):
                    yield self._finish_line()
                    continue
            if byte == 13:
                self.pending_cr = True
            elif byte == 10:
                yield self._finish_line()
            elif self.truncated:
                continue
            elif byte in (8, 127):
                if self.line:
                    pos = len(self.line) - 1
                    while pos > 0 and self.line[pos] & 0xC0 == 0x80:
                        pos -= 1
                    self.line = self.line[:pos]
            elif byte >= 32:
                if len(self.line) < self.max_line_length:
                    self.line.append(byte)
                else:
                    self.truncated = True


class TelnetServer:
    def __init__(self, controller, port, max_clients, idle_timeout, max_line_length):
        self.controller = controller
        self.port = port
        self.max_clients = max_clients
        self.idle_timeout_ms = idle_timeout * 1000
        self.max_line_length = max_line_length
        self.listener = None
        self.poller = select.poll()
        self.clients = {}
        self.last_tick = time.ticks_ms()
        self.last_gc = self.last_tick

    def start(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("0.0.0.0", self.port))
            listener.listen(self.max_clients)
            listener.setblocking(False)
            self.poller.register(listener, select.POLLIN)
        except BaseException:
            listener.close()
            raise
        self.listener = listener
        print("Telnet listening on port", self.port)

    def _remove(self, client):
        sock = client.sock
        if sock not in self.clients:
            return
        del self.clients[sock]
        try:
            self.poller.unregister(sock)
        except OSError:
            pass
        try:
            sock.close()
        except OSError as error:
            sys.print_exception(error)
        client.closed = True
        try:
            self.controller.on_disconnect(client, client.reason)
        except Exception as error:
            sys.print_exception(error)

    def _accept(self):
        try:
            sock, _ = self.listener.accept()
        except OSError as error:
            if _would_block(error):
                return
            raise
        client = None
        try:
            sock.setblocking(False)
            client = Client(sock, self.max_line_length)
            if len(self.clients) >= self.max_clients:
                # No rejection queue: one best-effort non-blocking send, then release.
                self.controller.on_reject(client, "server_full")
                client.flush()
                return
            self.clients[sock] = client
            self.poller.register(sock, select.POLLIN)
            self.controller.on_connect(client)
        except Exception as error:
            sys.print_exception(error)
            if client is not None:
                client.abort("connection_error")
        finally:
            if sock not in self.clients:
                sock.close()
                if client is not None:
                    client.closed = True
            elif client.closed:
                self._remove(client)

    def _read(self, client):
        if client.closed or client.closing_at is not None:
            return
        try:
            data = client.sock.recv(READ_SIZE)
        except OSError as error:
            if _would_block(error):
                return
            raise
        if not data:
            client.abort("peer_closed")
            return
        client.last_activity = time.ticks_ms()
        for line in client.feed(data):
            if line is None:
                self.controller.on_line_too_long(client)
            else:
                self.controller.on_line(client, line)
            if client.closed or client.closing_at is not None:
                break

    def poll_once(self):
        for entry in self.poller.poll(POLL_INTERVAL_MS):
            sock, events = entry[0], entry[1]
            if sock is self.listener:
                if events & (select.POLLERR | select.POLLHUP):
                    raise OSError("Telnet listener failed")
                self._accept()
                continue
            client = self.clients.get(sock)
            if client is None:
                continue
            try:
                if events & (select.POLLERR | select.POLLHUP):
                    if events & select.POLLERR:
                        print("Telnet client socket error")
                    client.abort("socket_error")
                elif events & select.POLLIN:
                    self._read(client)
            except Exception as error:
                sys.print_exception(error)
                client.abort("connection_error")

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_tick) >= POLL_INTERVAL_MS:
            self.last_tick = now
            self.controller.on_tick(now)
        for client in list(self.clients.values()):
            try:
                if not client.closed and client.closing_at is None:
                    if time.ticks_diff(now, client.last_activity) >= self.idle_timeout_ms:
                        self.controller.on_timeout(client)
                        client.close()
                        client.reason = "idle_timeout"
                client.flush()
                if not client.closed:
                    events = select.POLLIN if client.closing_at is None else 0
                    if client.output:
                        events |= select.POLLOUT
                    self.poller.modify(client.sock, events)
            except Exception as error:
                sys.print_exception(error)
                client.abort("connection_error")
            if client.closed:
                self._remove(client)
        if time.ticks_diff(now, self.last_gc) >= GC_INTERVAL_MS:
            gc.collect()
            self.last_gc = now

    def run(self):
        if self.listener is None:
            raise RuntimeError("Start the telnet listener before running it")
        try:
            while self.listener is not None:
                self.poll_once()
        finally:
            self.stop()

    def stop(self):
        for client in list(self.clients.values()):
            client.abort("server_stopped")
            self._remove(client)
        if self.listener is not None:
            try:
                self.poller.unregister(self.listener)
            except OSError:
                pass
            self.listener.close()
            self.listener = None
