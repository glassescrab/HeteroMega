#!/usr/bin/env bash
# 11-15 user diagnostic, after cp2-v6 and before cp2-v7b: is the ~2e-3 KL of 512/512/0 / HeteroMosaic from its NPU GEMM or from the rest of its
# runtime? quality path (last-token logits + 64 greedy tokens), quality-v4 prompts (8 x 1024), HeteroMosaic runtime with 0/0/0 (pm_GG_1024.json,
# H1 switches) at 2 and at 1 in flight; KL / top-1 vs G0 and G1 (kl_summary.py), next to H1 and HT1 of quality-v4.
set -uo pipefail
J=/notebooks/hm-jobs/cp2; R=/notebooks/hm-results/cp2
export SRC=/notebooks/hm-cp2b RES=$R STOP_LONG_AFTER_UTC=${STOP_LONG_AFTER_UTC:-2026-11-16T19:30Z}
until grep -q '^exit=' /notebooks/aup-runs/cp2-v6/run.log 2>/dev/null; do sleep 30; done
while pgrep -f "bash (eval3|quality|chain_pmb|chain_r1u|chain_v5|chain_v6)\.sh" > /dev/null; do sleep 10; done
[ -e "$R/STOP_CHAIN" ] && { echo "STOP_CHAIN present: not starting"; exit 0; }
cd "$J" && cp quality.new9.sh quality.sh || exit 2
bash quality.sh ggq --remaining
echo "=== $(date -u +%H:%M:%S) quality ggq"; bash quality.sh ggq; echo "quality ggq exit $?"
python3 kl_summary.py "$R/quality-v4" gpu_original-1024-r1 G1-1024-r0 H1-1024-r0 HT1-1024-r0 PM.GG_i2-1024-r0 PM.GG_i1-1024-r0 O1-1024-r0 | tee "$R/quality-v4.ggq.kl.txt"
cd /notebooks && tar czf hm-cp2-v6b.tgz hm-results/cp2/quality-v4/seed*/PM.GG_* hm-results/cp2/quality-v4/comparison-* hm-results/cp2/quality-v4.ggq.kl.txt hm-results/cp2/configs/pm_GG_1024.json aup-runs/cp2-v6b \
  && md5sum hm-cp2-v6b.tgz
echo "chain done $(date -u +%H:%M:%S)"
