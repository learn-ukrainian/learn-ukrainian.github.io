"""Projected stdlib-only TCP-to-Unix relay and child supervisor for an attempt."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
import signal
import socket


async def pump(reader, writer, activity):
    loop = asyncio.get_running_loop()
    while True:
        try:
            data = await asyncio.wait_for(reader.read(65536), 60)
        except TimeoutError:
            if loop.time() - activity[0] < 60:
                continue
            raise
        if not data:
            return
        activity[0] = loop.time()
        writer.write(data)
        await asyncio.wait_for(writer.drain(), 60)
        activity[0] = loop.time()


async def run(endpoint, command):
    # Relative AF_UNIX connect avoids the short sockaddr_un pathname limit.
    directory, name = os.path.split(endpoint)
    original = os.getcwd()
    os.chdir(directory)
    try:
        with socket.socket(socket.AF_UNIX) as probe:
            probe.settimeout(2)
            probe.connect(name)
        tasks = set()

        async def relay(reader, writer):
            upstream = None
            pumps = []
            try:
                remote, upstream = await asyncio.wait_for(asyncio.open_unix_connection(name, limit=65536), 2)
                activity = [asyncio.get_running_loop().time()]
                pumps = [asyncio.create_task(pump(reader, upstream, activity)),
                         asyncio.create_task(pump(remote, writer, activity))]
                await asyncio.wait(pumps, return_when=asyncio.FIRST_COMPLETED)
            except (OSError, TimeoutError):
                pass
            finally:
                for task in pumps:
                    task.cancel()
                await asyncio.gather(*pumps, return_exceptions=True)
                for stream in (writer, upstream):
                    if stream is not None:
                        stream.close()
                        with contextlib.suppress(OSError, TimeoutError):
                            await asyncio.wait_for(stream.wait_closed(), 1)

        def accept(reader, writer):
            if len(tasks) >= 16:
                writer.close()
                return
            task = asyncio.create_task(relay(reader, writer))
            tasks.add(task)
            task.add_done_callback(tasks.discard)

        server = await asyncio.start_server(accept, "127.0.0.1", 0, limit=65536)
        url = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        env = {k: v for k, v in os.environ.items() if k.lower() not in
               {"https_proxy", "http_proxy", "all_proxy", "no_proxy"}}
        env.update(HTTPS_PROXY=url, https_proxy=url, HTTP_PROXY=url, http_proxy=url,
                   ALL_PROXY=url, all_proxy=url, NO_PROXY="", no_proxy="")
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(*command, env=env, cwd=original, close_fds=True)
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, lambda s=sig: proc.send_signal(s) if proc.returncode is None else None)
            return await proc.wait()
        finally:
            server.close()
            await server.wait_closed()
            if proc is not None and proc.returncode is None:
                proc.kill()
                await proc.wait()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        os.chdir(original)


def main():
    parser = argparse.ArgumentParser(
        description="Relay attempt-local HTTPS proxy traffic to the parent Unix socket.\n"
                    "Internal formal-attempt launcher; do not use for ordinary dispatches.",
        epilog="Example: $PROJECT_PYTHON attempt_forwarder.py egress.sock /bin/true\n"
               "Outputs: namespace-local listener, proxy environment, child stdout/stderr.\n"
               "Exit codes: child's status, or 125 when relay startup fails.\n"
               "Related: formal-review-attempt-isolation runbook; #9251.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("endpoint", help="Attempt-local parent Unix socket path, e.g. runtime/egress.sock")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Absolute native CLI followed by its arguments")
    args = parser.parse_args()
    if not args.command:
        parser.error("command required")
    try:
        return asyncio.run(run(args.endpoint, args.command))
    except (OSError, TimeoutError):
        print("attempt_forwarder_start_failed", file=__import__("sys").stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
