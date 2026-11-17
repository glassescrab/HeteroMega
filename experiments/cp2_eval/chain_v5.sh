#!/usr/bin/env bash
# 11-15 eval_plan_v5 rows B/C/D: after cp2-r1u exits: remove STOP_CHAIN, write hso_<L>.json, install eval3.new6.sh, smokes of the new ours cells
# (stop if any is not DONE / fb>0 / wrong group / not 2 in flight), then m4-2048 (B), m2b-2048 (C), m2b-4096 (D); cellmed + v5_report per stage; tarball.
set -uo pipefail
J=/notebooks/hm-jobs/cp2; R=/notebooks/hm-results/cp2
export SRC=/notebooks/hm-cp2b RES=$R STOP_LONG_AFTER_UTC=${STOP_LONG_AFTER_UTC:-2026-11-16T19:45Z}
until grep -q '^exit=' /notebooks/aup-runs/cp2-r1u/run.log 2>/dev/null; do sleep 30; done
while pgrep -f "bash (eval3|quality|chain_pmb|chain_r1u)\.sh" > /dev/null; do sleep 10; done
rm -f "$R/STOP_CHAIN"
cd "$J" && cp eval3.new6.sh eval3.sh && python3 make_v5_configs.py "$R/configs" || exit 2
for s in v5smoke m4-2048 m2b-2048 m2b-4096; do bash eval3.sh $s --list | sort | uniq -c; done
ok=1
echo "=== $(date -u +%H:%M:%S) v5smoke"; bash eval3.sh v5smoke; echo "stage v5smoke exit $?"
python3 v5_report.py "$R" v5smoke | tee "$R/v5smoke.report.md"
for L in 2048 4096; do
    cs=$((L / 2)); I=$(ls -d "$R"/v5smoke/HS1.ours_gu-$L-s1)
    [ -e "$I/DONE" ] && grep -qx 'uncached_fallback=0' "$I/info.txt" && grep -qx 'inflight_seen=2' "$I/info.txt" \
      && grep -q "selection=Using grouped kernels_gemm_chunked (chunk_size=$cs, chunk_schedule=\[$cs\], inflight=2, prompt_len=$L)" "$I/info.txt" \
      && echo "smoke $L ok" || { echo "SMOKE_FAIL $L"; ok=0; }
done
if [ $ok = 1 ]; then
    for s in m4-2048 m2b-2048 m2b-4096; do
        [ -e "$R/STOP_CHAIN" ] && { echo "STOP_CHAIN present: not starting $s"; break; }
        echo "=== $(date -u +%H:%M:%S) $s"; bash eval3.sh "$s"; echo "stage $s exit $?"
        python3 cellmed.py "$R/$s" | tee "$R/$s.cellmed.txt"; python3 v5_report.py "$R" "$s" > "$R/$s.report.md" 2>&1
    done
fi
cd /notebooks && tar czf hm-cp2-v5.tgz hm-results/cp2/v5smoke* hm-results/cp2/m4-2048* hm-results/cp2/m2b-* hm-results/cp2/configs/hso_* hm-results/cp2/configs/hs.json \
    hm-results/cp2/configs/hm_2048*.json aup-runs/cp2-v5 \
  && rm -rf hm-cp2-v5-parts && mkdir hm-cp2-v5-parts && (cd hm-cp2-v5-parts && split -b 20m -d ../hm-cp2-v5.tgz part-) && md5sum hm-cp2-v5.tgz && ls hm-cp2-v5-parts
echo "chain done $(date -u +%H:%M:%S)"
