#!/usr/bin/env bash
# 11-15 user requests: smokes of the new HeteroMosaic cells at 2048/4096 (config matrix), then kab1-1024 (kernel ablation, 1 in flight),
# then main1a-2048 and main1a-4096 (regime 1 with the author's HeteroMosaic entry), then reports and a results tarball (split, md5).
# Waits for any running aup job of ours (cp2-kab1s) to end first; installs eval3.new.sh only when no eval3 instance runs.
set -uo pipefail
J=/notebooks/hm-jobs/cp2; R=/notebooks/hm-results/cp2
export SRC=/notebooks/hm-cp2b RES=$R STOP_LONG_AFTER_UTC=${STOP_LONG_AFTER_UTC:-2026-11-16T18:00Z}
until grep -q '^exit=' /notebooks/aup-runs/cp2-kab1s/run.log 2>/dev/null; do sleep 20; done
while pgrep -f "bash eval3.sh" > /dev/null; do sleep 20; done
cd "$J" && { cmp -s eval3.new.sh eval3.sh || cp eval3.new.sh eval3.sh; }
for s in main1as-2048 main1as-4096; do echo "=== $(date -u +%H:%M:%S) $s"; bash eval3.sh "$s"; python3 kab1_report.py "$R" "$s" > "$R/$s.matrix.md" 2>&1; done
for s in kab1-1024 main1a-2048 main1a-4096; do
    [ -e "$R/STOP_CHAIN" ] && { echo "STOP_CHAIN present: not starting $s"; break; }
    echo "=== $(date -u +%H:%M:%S) $s"; bash eval3.sh "$s"; echo "stage $s exit $?"
    python3 kab1_report.py "$R" "$s" > "$R/$s.report.md" 2>&1
done
python3 aggregate.py "$R" > "$R/aggregate.out" 2>&1; echo "aggregate rc=$?"
cd /notebooks && tar czf hm-cp2-kab1.tgz hm-results/cp2/kab1* hm-results/cp2/main1a* hm-results/cp2/configs hm-results/cp2/aggregate aup-runs/cp2-kab1s aup-runs/cp2-kab1 \
  && rm -rf hm-cp2-kab1-parts && mkdir hm-cp2-kab1-parts && (cd hm-cp2-kab1-parts && split -b 20m -d ../hm-cp2-kab1.tgz part-) && md5sum hm-cp2-kab1.tgz && ls hm-cp2-kab1-parts
echo "chain done $(date -u +%H:%M:%S)"
