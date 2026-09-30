"""Parent-owned CONNECT-only egress for formal attempts; never mounted in seats."""

from __future__ import annotations

import asyncio
import contextlib
import ctypes
import ipaddress
import json
import os
import re
import socket
import threading
from dataclasses import dataclass
from pathlib import Path

import yaml

from scripts.common.repo_root import project_interpreter
from scripts.review.isolation import ReviewIsolationError

_HOST = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+\Z")


def canonical_host(value: str) -> bool:
    if (len(value) > 253 or not _HOST.fullmatch(value) or any(len(p) > 63 for p in value.split('.'))
            or value.rsplit('.', 1)[-1].isdigit()):
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return True
    return False


def load_allowlist(agent: str) -> frozenset[str]:
    path = Path(__file__).resolve().parents[1] / "config" / "attempt_provider_egress.yaml"
    data = yaml.safe_load(path.read_bytes())
    hosts = data["harnesses"][agent]
    if not isinstance(hosts, list) or not hosts or any(not isinstance(h, str) or not canonical_host(h) for h in hosts):
        raise ReviewIsolationError("attempt_egress_allowlist_invalid")
    return frozenset(hosts)


def normalize_address(value: str):
    address = ipaddress.ip_address(value)
    return address.ipv4_mapped if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped else address


def host_addresses() -> frozenset:
    """Enumerate *all* interface addresses using Linux getifaddrs, fail closed."""
    class Ifaddrs(ctypes.Structure):
        pass

    Ifaddrs._fields_ = [
        ("next", ctypes.POINTER(Ifaddrs)), ("name", ctypes.c_char_p), ("flags", ctypes.c_uint),
        ("addr", ctypes.c_void_p), ("netmask", ctypes.c_void_p), ("union", ctypes.c_void_p),
        ("data", ctypes.c_void_p),
    ]
    libc = ctypes.CDLL(None, use_errno=True)
    libc.getifaddrs.argtypes = [ctypes.POINTER(ctypes.POINTER(Ifaddrs))]
    libc.getifaddrs.restype = ctypes.c_int
    libc.freeifaddrs.argtypes = [ctypes.POINTER(Ifaddrs)]
    head = ctypes.POINTER(Ifaddrs)()
    if libc.getifaddrs(ctypes.byref(head)) != 0:
        raise ReviewIsolationError("attempt_egress_interfaces_unavailable")
    found = set()
    try:
        current = head
        while current:
            item = current.contents
            if item.addr:
                family = ctypes.c_ushort.from_address(item.addr).value
                if family in (socket.AF_INET, socket.AF_INET6):
                    offset, size = (4, 4) if family == socket.AF_INET else (8, 16)
                    found.add(normalize_address(socket.inet_ntop(family, ctypes.string_at(item.addr + offset, size))))
            current = item.next
    finally:
        libc.freeifaddrs(head)
    if not found:
        raise ReviewIsolationError("attempt_egress_interfaces_empty")
    return frozenset(found)


def validate_answers(answers: list[str], local: frozenset) -> list:
    if not answers:
        raise ValueError("empty DNS answer")
    addresses = [normalize_address(a) for a in answers]
    if any(not a.is_global or a.is_multicast or a.is_reserved or a.is_unspecified or a in local for a in addresses):
        raise ValueError("forbidden destination")
    return list(dict.fromkeys(addresses))


def connect_target(header: bytes, allowlist: frozenset[str]) -> str:
    """RFC 9110 CONNECT authority, deliberately narrower than general HTTP."""
    lines = header.decode("ascii").split("\r\n")
    method, target, version = lines[0].split(" ")
    if method != "CONNECT" or version not in {"HTTP/1.0", "HTTP/1.1"}:
        raise ValueError("CONNECT required")
    host, port = target.split(":")
    if port != "443" or not canonical_host(host) or host not in allowlist:
        raise ValueError("destination refused")
    seen_host = False
    for line in lines[1:-2]:
        name, value = line.split(":", 1)
        if not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name) or any(ord(c) < 32 for c in value.strip()):
            raise ValueError("malformed header")
        if name.lower() == "host":
            if seen_host or value.strip() != target:
                raise ValueError("conflicting Host")
            seen_host = True
        if name.lower() in {"content-length", "transfer-encoding"}:
            raise ValueError("CONNECT body refused")
    return host


@dataclass(frozen=True)
class Limits:
    header_bytes: int = 8192
    connections: int = 16
    resolvers: int = 2
    header_seconds: float = 5
    resolve_seconds: float = 5
    connect_seconds: float = 10
    idle_seconds: float = 60
    buffer_bytes: int = 65536


DEFAULT_LIMITS = Limits()


class AttemptEgress:
    """Bounded asyncio proxy with killable DNS processes and numeric connects."""

    def __init__(self, endpoint: Path, allowlist: frozenset[str], *, limits: Limits = DEFAULT_LIMITS):
        self.endpoint, self.allowlist, self.limits = endpoint, allowlist, limits
        self.local_addresses = host_addresses()
        self.records: list[dict] = []  # destination + byte count only; no payloads or addresses
        self.ready = threading.Event()
        self.error = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self.ready.wait(5) or self.error:
            self.cleanup()
            raise ReviewIsolationError("attempt_egress_start_failed")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.tasks = set()
        self.resolvers = asyncio.Semaphore(self.limits.resolvers)
        try:
            self.loop.run_until_complete(self._start())
            self.ready.set()
            self.loop.run_forever()
        except BaseException as exc:
            self.error = type(exc).__name__
            self.ready.set()
        finally:
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    async def _start(self):
        listener = socket.socket(socket.AF_UNIX)
        try:
            directory = os.open(self.endpoint.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                listener.bind(f"/proc/self/fd/{directory}/{self.endpoint.name}")
            finally:
                os.close(directory)
            listener.listen(self.limits.connections)
            listener.setblocking(False)
            self.server = await asyncio.start_unix_server(self._accept, sock=listener, limit=self.limits.header_bytes)
        except BaseException:
            listener.close()
            raise

    def _accept(self, reader, writer):
        if len(self.tasks) >= self.limits.connections:
            writer.close()
            return
        task = self.loop.create_task(self._serve(reader, writer))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _resolve(self, host):
        # getaddrinfo in a thread cannot be cancelled on a hung libc resolver.
        # A bounded child is killed/reaped on timeout or proxy cancellation.
        async with self.resolvers:
            proc = await asyncio.create_subprocess_exec(
                str(project_interpreter()), "-c",
                "import socket,json,sys; print(json.dumps(list(dict.fromkeys(a[4][0] for a in "
                "socket.getaddrinfo(sys.argv[1],443,type=socket.SOCK_STREAM)))))", host,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, limit=65536,
            )
            try:
                async with asyncio.timeout(self.limits.resolve_seconds):
                    output = bytearray()
                    while chunk := await proc.stdout.read(8192):
                        output.extend(chunk)
                        if len(output) > 65536:
                            raise ValueError("DNS answer too large")
                    await proc.wait()
                if proc.returncode != 0:
                    raise ValueError("DNS unavailable")
                return json.loads(output)
            finally:
                if proc.returncode is None:
                    with contextlib.suppress(ProcessLookupError):
                        proc.kill()
                await proc.wait()

    async def _connect(self, addresses):
        for address in addresses:
            sock = socket.socket(socket.AF_INET if address.version == 4 else socket.AF_INET6)
            sock.setblocking(False)
            try:
                # Numeric address and explicit family: never a second lookup.
                await self.loop.sock_connect(sock, (str(address), 443))
                return await asyncio.open_connection(sock=sock, limit=self.limits.buffer_bytes)
            except OSError:
                sock.close()
            except BaseException:
                sock.close()
                raise
        raise OSError("provider unreachable")

    async def _pump(self, reader, writer, record, activity):
        while True:
            try:
                data = await asyncio.wait_for(reader.read(self.limits.buffer_bytes), self.limits.idle_seconds)
            except TimeoutError:
                if self.loop.time() - activity[0] < self.limits.idle_seconds:
                    continue  # Activity in the other direction keeps the tunnel alive.
                raise
            if not data:
                return
            activity[0] = self.loop.time()
            writer.write(data)
            await asyncio.wait_for(writer.drain(), self.limits.idle_seconds)
            activity[0] = self.loop.time()
            record["bytes"] += len(data)

    async def _serve(self, reader, writer):
        upstream = None
        record = None
        pumps = []
        try:
            header = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), self.limits.header_seconds)
            if len(header) > self.limits.header_bytes:
                raise ValueError("header too large")
            host = connect_target(header, self.allowlist)
            record = {"destination": f"{host}:443", "bytes": 0}
            # One aggregate per allowed destination keeps logs bounded as well.
            existing = next((r for r in self.records if r["destination"] == record["destination"]), None)
            if existing is None:
                self.records.append(record)
            else:
                record = existing
            answers = await asyncio.wait_for(self._resolve(host), self.limits.resolve_seconds)
            addresses = validate_answers(answers, self.local_addresses)
            remote, upstream = await asyncio.wait_for(self._connect(addresses), self.limits.connect_seconds)
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await asyncio.wait_for(writer.drain(), self.limits.header_seconds)
            activity = [self.loop.time()]
            pumps = [asyncio.create_task(self._pump(reader, upstream, record, activity)),
                     asyncio.create_task(self._pump(remote, writer, record, activity))]
            await asyncio.wait(pumps, return_when=asyncio.FIRST_COMPLETED)
        except (OSError, ValueError, UnicodeError, TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError):
            if upstream is None:
                with contextlib.suppress(OSError, TimeoutError):
                    writer.write(b"HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n")
                    await asyncio.wait_for(writer.drain(), self.limits.header_seconds)
        finally:
            for task in pumps:
                task.cancel()
            await asyncio.gather(*pumps, return_exceptions=True)
            for stream in (writer, upstream):
                if stream is not None:
                    stream.close()
                    with contextlib.suppress(OSError, TimeoutError):
                        await asyncio.wait_for(stream.wait_closed(), 1)

    def cleanup(self):
        if self.loop.is_running():
            if hasattr(self, "server"):
                self.loop.call_soon_threadsafe(self.server.close)
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=10)
        if self.thread.is_alive():
            raise ReviewIsolationError("attempt_egress_cleanup_failed")
