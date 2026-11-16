#!/usr/bin/env bash
# 11-16 config-ranking check, phase 1: 1x1 smoke of every cell of S1-S4 (rk<S>s-L) and of the AFTER search stages (apmbs-L), with the cell gate
# (rk_check.py) and reports, then one quality path (RK1.A_auth, prompt seed 1) into quality-rk-smoke. Nothing here enters the results.
# Dry-run matrices: bash eval3.sh STAGE --dry (no GPU/NPU). Phase 2 is chain_rk.sh.
set -uo pipefail
J=/notebooks/hm-jobs/cp2; R=/notebooks/hm-results/cp2
export SRC=/notebooks/hm-cp2b RES=$R CFGDIR=$R/configs-rk STOP_LONG_AFTER_UTC=${STOP_LONG_AFTER_UTC:-2026-11-17T16:30Z}
mkdir -p "$CFGDIR"   # base configs of the reported cells (identical files), so that pm/pmb files of this check stay apart from configs/
for f in hr hs hso_2048 hso_4096 hm_1024 hm_2048 hm_4096 hm_1024.shipped hm_2048.shipped hm_4096.shipped; do [ -e "$CFGDIR/$f.json" ] || cp "$R/configs/$f.json" "$CFGDIR/" || exit 2; done
cd "$J" || exit 2
for s in rk1s-1024 rk2s-2048 rk3s-2048 rk4s-4096 apmbs-2048 apmbs-4096; do
    echo "=== $(date -u +%H:%M:%S) $s"; bash eval3.sh $s; echo "stage $s exit $?"
    python3 rk_report.py "$R" $s > "$R/$s.report.md" 2>&1
done
echo "=== $(date -u +%H:%M:%S) quality smoke"; QSEEDS=1 QOUT=$R/quality-rk-smoke bash quality.sh rkq 1024; echo "quality smoke exit $?"
echo "smoke done $(date -u +%H:%M:%S)"
