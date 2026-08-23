#!/usr/bin/env python3
"""Densify a route polyline, project checkpoints onto it, emit the data file.

Input:  /tmp/route_raw.json      (Vyntel MCP routes response with polyline)
        /tmp/checkpoints.json    (checkpoint city coordinates from MCP search)
Output: data/route_whitefield_calangute.json
"""
import json, math, sys

MAX_SEG = 800  # meters; segments longer than this are linearly subdivided

def haversine(a, b):
    R = 6371000
    la1, lo1, la2, lo2 = map(math.radians, [a[1], a[0], b[1], b[0]])
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))

def densify(pl):
    out = [pl[0]]
    for i in range(1, len(pl)):
        a, b = pl[i - 1], pl[i]
        n = int(haversine(a, b) // MAX_SEG)
        for k in range(1, n + 1):
            f = k / (n + 1)
            out.append([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f])
        out.append(b)
    return out

def main():
    route = json.load(open("/tmp/route_raw.json"))["data"]
    cps = json.load(open("/tmp/checkpoints.json"))
    pl = densify(route["polyline"])

    cum = [0.0]
    for i in range(1, len(pl)):
        cum.append(cum[-1] + haversine(pl[i - 1], pl[i]))
    total = cum[-1]

    named = [
        ("Start — Whitefield, Bengaluru", pl[0][0], pl[0][1]),
        ("Tumakuru",  cps["Tumakuru, Karnataka"]["lng"],  cps["Tumakuru, Karnataka"]["lat"]),
        ("Chitradurga", cps["Chitradurga, Karnataka"]["lng"], cps["Chitradurga, Karnataka"]["lat"]),
        ("Hubballi",  cps["Hubballi, Karnataka"]["lng"],  cps["Hubballi, Karnataka"]["lat"]),
        ("Belagavi",  cps["Belagavi, Karnataka"]["lng"],  cps["Belagavi, Karnataka"]["lat"]),
        ("Finish — Calangute Beach, Goa", cps["Calangute Beach, Goa"]["lng"], cps["Calangute Beach, Goa"]["lat"]),
    ]
    checkpoints = []
    for name, lng, lat in named:
        best = min(range(len(pl)), key=lambda i: (pl[i][0] - lng) ** 2 + (pl[i][1] - lat) ** 2)
        checkpoints.append({"name": name, "t": cum[best] / total})

    out = {"polyline": pl, "total_m": total, "checkpoints": checkpoints}
    json.dump(out, open("data/route_whitefield_calangute.json", "w"))
    print(f"points={len(pl)} total_km={total/1000:.0f} checkpoints={len(checkpoints)}")

if __name__ == "__main__":
    sys.exit(main())
