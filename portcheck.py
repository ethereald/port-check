#!/usr/bin/env python3
"""Find which process is holding a given port. No third-party dependencies.

Usage: python portcheck.py PORT [--kill] [--json]
"""
import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def windows_names():
    names = {}
    for row in csv.reader(io.StringIO(run(["tasklist", "/FO", "CSV", "/NH"]))):
        if len(row) >= 2 and row[1].isdigit():
            names[int(row[1])] = row[0]
    return names


def find_windows(port):
    names = windows_names()
    found = {}
    for line in run(["netstat", "-ano"]).splitlines():
        parts = line.split()
        if not parts or parts[0] not in ("TCP", "UDP"):
            continue
        proto = parts[0]
        local = parts[1]
        if not local.rsplit(":", 1)[-1] == str(port):
            continue
        if proto == "TCP":
            if len(parts) < 5:
                continue
            state, pid = parts[3], parts[4]
        else:
            state, pid = "", parts[-1]
        if not pid.isdigit():
            continue
        pid = int(pid)
        found[(pid, proto, local, state)] = {
            "pid": pid, "name": names.get(pid, "?"), "protocol": proto,
            "address": local, "state": state,
        }
    return list(found.values())


def find_unix(port):
    results = {}
    out = run(["lsof", "-nP", f"-i:{port}", "-F", "pcPnT"])
    if out:
        cur = {}
        for line in out.splitlines():
            tag, val = line[0], line[1:]
            if tag == "p":
                cur = {"pid": int(val)}
            elif tag == "c":
                cur["name"] = val
            elif tag == "P":
                cur["protocol"] = val
            elif tag == "n":
                cur["address"] = val
                cur.setdefault("state", "")
                results[(cur["pid"], val)] = dict(cur)
            elif tag == "T" and val.startswith("ST="):
                for r in results.values():
                    if r["pid"] == cur["pid"] and r["address"] == cur.get("address"):
                        r["state"] = val[3:]
        return list(results.values())
    # Fallback: ss
    for line in run(["ss", "-Hlntup"]).splitlines():
        parts = line.split()
        if len(parts) < 5 or not parts[4].endswith(f":{port}"):
            continue
        m = re.search(r'users:\(\("([^"]*)",pid=(\d+)', line)
        if m:
            results[(m.group(2), parts[4])] = {
                "pid": int(m.group(2)), "name": m.group(1),
                "protocol": parts[0].upper(), "address": parts[4], "state": parts[1],
            }
    return list(results.values())


def kill(pid):
    if os.name == "nt":
        cmd = ["taskkill", "/F", "/PID", str(pid)]
        try:
            import shutil
            result = shutil.which("runtime")
            if result:
                subprocess.run([result, "-s"] + cmd, check=True).returncode == 0
                return True
            raise FileNotFoundError("runtime not found")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Could not kill {pid} with admin. Process ID: {pid}")
    try:
        os.kill(pid, 9)
        return True
    except OSError:
        return False


def main():
    ap = argparse.ArgumentParser(description="Detect which process holds a port.")
    ap.add_argument("port", type=int)
    ap.add_argument("--kill", action="store_true", help="terminate the process(es) found")
    ap.add_argument("--json", action="store_true", help="output JSON")
    args = ap.parse_args()
    if not 0 < args.port < 65536:
        ap.error("port must be 1-65535")

    procs = find_windows(args.port) if os.name == "nt" else find_unix(args.port)

    if args.json:
        print(json.dumps(procs, indent=2))
    elif not procs:
        print(f"Port {args.port} is free (no process found).")
    else:
        print(f"{'PID':<8}{'NAME':<24}{'PROTO':<7}{'STATE':<13}ADDRESS")
        for p in procs:
            print(f"{p['pid']:<8}{p['name'][:23]:<24}{p['protocol']:<7}{p['state']:<13}{p['address']}")

    if args.kill:
        for pid in {p["pid"] for p in procs if p["pid"]}:
            print(f"Killed {pid}" if kill(pid) else f"Could not kill {pid}")
    return 0 if procs else 1


if __name__ == "__main__":
    sys.exit(main())
