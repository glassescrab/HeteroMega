#!/usr/bin/env bash
# 11-17 user: abl1-1024 and kab1-1024 again with HeteroMosaic's NPU GEMMs from our binaries (abl1n-1024, then kab1n-1024; HeteroMosaic cells on
# hm-npualign with hw_bins_ours, the other cells unchanged on hm-cp2b), each stage run twice (the second pass retries processes without DONE),
# then cellmed.py and the reports, then the results tarball. Every process takes gpu.lock itself. No stage starts after STAGE_STOP_UTC or
# when $R/STOP_ABL exists; no process starts after STOP_LONG_AFTER_UTC (eval3.sh deadline).
set -uo pipefail
J=/notebooks/hm-jobs/cp2; R=/notebooks/hm-results/cp2
export SRC=/notebooks/hm-cp2b RES=$R CFGDIR=$R/configs-rk STOP_LONG_AFTER_UTC=${STOP_LONG_AFTER_UTC:-2026-11-17T17:40Z}
STAGE_STOP=${STAGE_STOP_UTC:-2026-11-17T17:15Z}
while pgrep -f "(eval3|quality|smoke_rk)\.sh" > /dev/null; do sleep 10; done
mkdir -p "$CFGDIR"
for f in hr hm_1024 hm_1024.shipped hp_g0u0d512; do [ -e "$CFGDIR/$f.json" ] || cp "$R/configs/$f.json" "$CFGDIR/" || exit 2; done
cd "$J" || exit 2
stop() { if [ -e "$R/STOP_ABL" ]; then echo "STOP_ABL present: not starting $1"
         elif [[ $(date -u +%Y-%m-%dT%H:%MZ) > $STAGE_STOP ]]; then echo "past $STAGE_STOP: not starting $1"; else return 1; fi; }
run() { echo "=== $(date -u +%H:%M:%S) $1"; bash eval3.sh "$1"; echo "stage $1 exit $?"
        bash eval3.sh "$1"; echo "stage $1 second pass (processes without DONE) exit $?"
        python3 cellmed.py "$R/$1" > "$R/$1.cellmed.txt" 2>&1; python3 rk_report.py "$R" "$1" > "$R/$1.fingerprint.md" 2>&1
        case $1 in kab1*) python3 kab1_report.py "$R" "$1" ;; *) python3 v5_report.py "$R" "$1" ;; esac > "$R/$1.report.md" 2>&1; }
for s in abl1n-1024 kab1n-1024; do stop $s && break; run $s; done
cd /notebooks && tar czf hm-cp2-abln.tgz hm-results/cp2/abl1n* hm-results/cp2/kab1n* hm-results/cp2/configs-rk/abln* hm-results/cp2/configs-rk/*.ours.json \
  aup-runs/cp2-abln* && md5sum hm-cp2-abln.tgz && ls -l hm-cp2-abln.tgz
echo "chain done $(date -u +%H:%M:%S)"
