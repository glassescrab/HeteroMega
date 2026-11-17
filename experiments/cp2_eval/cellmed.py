import glob, json, statistics, sys, re, os
stage = sys.argv[1]
cells = {}
for d in sorted(glob.glob(f"{stage}/*-s*")):
    if not os.path.exists(f"{d}/DONE"): continue
    bad = [b for b in ("BAD_INFLIGHT", "BAD_SELECTION") if os.path.exists(f"{d}/{b}")]
    js = [j for j in glob.glob(f"{d}/*.result.json")]
    if len(js) != 1: print("skip", d, len(js)); continue
    r = json.load(open(js[0]))
    reps = r["reps"]
    t = [1000 * x["prefill_s"] for x in sorted(reps, key=lambda x: x["rep"])]
    case = dict(l.strip().split("=", 1) for l in open(f"{d}/case.txt") if "=" in l)
    info = dict(l.strip().split("=", 1) for l in open(f"{d}/info.txt") if "=" in l)
    name = re.sub(r"-s\d+$", "", os.path.basename(d))
    cells.setdefault(name, []).append((statistics.median(t[1:]), t[0], case.get("switches", "").strip(), info.get("uncached_fallback"), info.get("inflight_seen"), bad, len(t)))
for n, v in cells.items():
    meds = [x[0] for x in v]
    print(f"{n:22s} n={len(v)} cell={statistics.median(meds):8.1f} min={min(meds):8.1f} max={max(meds):8.1f} spread={100*(max(meds)-min(meds))/statistics.median(meds):4.1f}% reps={v[0][6]} fb={sorted(set(x[3] for x in v))} infl={sorted(set(x[4] for x in v))} bad={[x[5] for x in v if x[5]]} sw={v[0][2]}")
