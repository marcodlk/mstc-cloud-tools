import subprocess


def find(ip):
    out = subprocess.check_output(["nslookup", ip])
    lines = out.decode("utf-8")
    for line in lines.split("\n"):
        if "name" in line:
            parts = line.split("=")
            located = parts[1].strip()
            if located.endswith("."):
                located = located[:-1]
            return located
    return None
