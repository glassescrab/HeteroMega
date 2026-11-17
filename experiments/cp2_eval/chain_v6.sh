#!/usr/bin/env bash
# 11-15 user: after cp2-v5: ablation split unit x in flight at 1024 (abl1s smoke gate -> abl1-1024), then last-token KL of rows C/D (quality.sh v5q 2048, 4096).
set -uo pipefail
J=/notebooks/hm-jobs/cp2; R=/notebooks/hm-results/cp2
export SRC=/notebooks/hm-cp2b RES=$R STOP_LONG_AFTER_UTC=${STOP_LONG_AFTER_UTC:-2026-11-16T19:45Z}
until grep -q '^exit=' /notebooks/aup-runs/cp2-v5/run.log 2>/dev/null; do sleep 30; done
while pgrep -f "bash (eval3|quality|chain_pmb|chain_r1u|chain_v5)\.sh" > /dev/null; do sleep 10; done
[ -e "$R/STOP_CHAIN" ] && { echo "STOP_CHAIN present: not starting"; exit 0; }
cd "$J" && cp eval3.new7.sh eval3.sh && cp quality.new7.sh quality.sh && cp v5_report.new.py v5_report.py || exit 2
for s in abl1s-1024 abl1-1024; do bash eval3.sh $s --list | sort | uniq -c; done
bash quality.sh v5q 2048 --remaining; bash quality.sh v5q 4096 --remaining
echo "=== $(date -u +%H:%M:%S) abl1s-1024"; bash eval3.sh abl1s-1024; echo "stage abl1s-1024 exit $?"
python3 v5_report.py "$R" abl1s-1024 | tee "$R/abl1s-1024.report.md"
ok=1; n=0
for D in "$R"/abl1s-1024/*-s1; do n=$((n + 1))
    want=$(sed -n 's/^inflight=//p' "$D/case.txt")
    { [ -e "$D/DONE" ] && grep -qx 'uncached_fallback=0' "$D/info.txt" && grep -qx "inflight_seen=$want" "$D/info.txt" && ! ls "$D"/BAD_* > /dev/null 2>&1; } \
      && echo "smoke ${D##*/} ok" || { echo "SMOKE_FAIL ${D##*/}"; ok=0; }
done
[ $n = 6 ] || { echo "SMOKE_FAIL: $n smoke dirs, expected 6"; ok=0; }
if [ $ok = 1 ] && [ ! -e "$R/STOP_CHAIN" ]; then
    echo "=== $(date -u +%H:%M:%S) abl1-1024"; bash eval3.sh abl1-1024; echo "stage abl1-1024 exit $?"
    python3 cellmed.py "$R/abl1-1024" | tee "$R/abl1-1024.cellmed.txt"; python3 v5_report.py "$R" abl1-1024 > "$R/abl1-1024.report.md" 2>&1
else echo "abl1-1024 not started (smoke failed or STOP_CHAIN)"; fi
for L in 2048 4096; do
    [ -e "$R/STOP_CHAIN" ] && { echo "STOP_CHAIN present: not starting v5q $L"; break; }
    echo "=== $(date -u +%H:%M:%S) quality v5q $L"; bash quality.sh v5q $L; echo "quality v5q $L exit $?"
    python3 kl_summary.py "$R/quality-v4-$L" | tee "$R/quality-v4-$L.kl.txt"
done
cd /notebooks && tar czf hm-cp2-v6.tgz hm-results/cp2/abl1* hm-results/cp2/quality-v4-2048* hm-results/cp2/quality-v4-4096* hm-results/cp2/configs/hso_* \
    hm-results/cp2/configs/hs.json hm-results/cp2/configs/hm_1024.json hm-results/cp2/configs/hp_g0u0d512.json aup-runs/cp2-v6 \
  && rm -rf hm-cp2-v6-parts && mkdir hm-cp2-v6-parts && (cd hm-cp2-v6-parts && split -b 20m -d ../hm-cp2-v6.tgz part-) && md5sum hm-cp2-v6.tgz && ls hm-cp2-v6-parts
echo "chain done $(date -u +%H:%M:%S)"
