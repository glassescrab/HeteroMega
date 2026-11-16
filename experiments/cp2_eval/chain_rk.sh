#!/usr/bin/env bash
# 11-16 config-ranking check, phase 2 (after the controller reviewed smoke_rk.sh): S1-S4 timed (rk1-1024 rk2-2048 rk3-2048 rk4-4096), then our
# per-micro-batch search in the AFTER environment (apmb1/apmb2/apmbc at 2048, then 4096; pmb_win = fastest pattern of apmbc), then quality
# (quality.sh rkq 1024/2048/4096), then the results tarball. Every process takes gpu.lock itself. touch $R/STOP_RK: no further stage starts.
set -uo pipefail
J=/notebooks/hm-jobs/cp2; R=/notebooks/hm-results/cp2
export SRC=/notebooks/hm-cp2b RES=$R CFGDIR=$R/configs-rk STOP_LONG_AFTER_UTC=${STOP_LONG_AFTER_UTC:-2026-11-17T16:30Z}
while pgrep -f "(eval3|quality|smoke_rk)\.sh" > /dev/null; do sleep 10; done
mkdir -p "$CFGDIR"
for f in hr hs hso_2048 hso_4096 hm_1024 hm_2048 hm_4096 hm_1024.shipped hm_2048.shipped hm_4096.shipped; do [ -e "$CFGDIR/$f.json" ] || cp "$R/configs/$f.json" "$CFGDIR/" || exit 2; done
cd "$J" || exit 2
stop() { [ -e "$R/STOP_RK" ] && echo "STOP_RK present: not starting $1"; }
run() { echo "=== $(date -u +%H:%M:%S) $1"; bash eval3.sh "$1"; echo "stage $1 exit $?"
        python3 cellmed.py "$R/$1" > "$R/$1.cellmed.txt" 2>&1; python3 rk_report.py "$R" "$1" > "$R/$1.report.md" 2>&1; }
for s in rk1-1024 rk2-2048 rk3-2048 rk4-4096; do stop $s && break; run $s; done
for L in 2048 4096; do
    for s in apmb1-$L apmb2-$L apmbc-$L; do stop $s && break 2; run $s; done
    python3 hm_ratio.py "$CFGDIR" pmb_win $L "$R/apmbc-$L" > "$R/apmbc-$L.win.txt" 2>&1; cat "$R/apmbc-$L.win.txt"
done
for L in 1024 2048 4096; do
    stop "quality $L" && break
    echo "=== $(date -u +%H:%M:%S) quality rkq $L"; bash quality.sh rkq $L; echo "quality rkq $L exit $?"
    python3 kl_summary.py "$R/quality-rk-$L" > "$R/quality-rk-$L.kl.txt" 2>&1
done
cd /notebooks && tar czf hm-cp2-rk.tgz hm-results/cp2/rk* hm-results/cp2/apmb* hm-results/cp2/quality-rk-* hm-results/cp2/configs-rk aup-runs/cp2-rk-smoke aup-runs/cp2-rk \
  && rm -rf hm-cp2-rk-parts && mkdir hm-cp2-rk-parts && (cd hm-cp2-rk-parts && split -b 20m -d ../hm-cp2-rk.tgz part-) && md5sum hm-cp2-rk.tgz && ls hm-cp2-rk-parts
echo "chain done $(date -u +%H:%M:%S)"
