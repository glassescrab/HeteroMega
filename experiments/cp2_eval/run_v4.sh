#!/usr/bin/env bash
# Whole CP2 v4 evaluation (eval_plan_v4 sections 7, 10, 11): Tier 1 then Tier 2, resumable: re-run the same command after an interruption.
# SRC=/notebooks/hm-cp2b (common.sh default), results $RES=/notebooks/hm-results/cp2, new stage names only. No build/compile stage (artifacts p<=13312 exist).
# Before every process (eval3.sh) and every stage it checks STOP_LONG_AFTER_UTC (default 2026-11-15T19:30Z); past it nothing new starts, the unfinished
# work is written to $RES/remaining.txt and the script exits 0. Env passes through (SRC RES NOU SEED P_ON_1024 ...).
# gate4 (pre-launch smokes) runs first; any failed smoke or BAD_INFLIGHT/BAD_SELECTION stops the run (exit 3) before a timed stage starts.
# Dependencies are in the order: hprobe1-1024 -> hprobe1b-1024 (hm1_1024, hm1o_1024) -> uprobe1 (HP1 with/without UNCACHED) -> sweep1-1024 (best_p1.txt) -> main1-1024 ...
# kcmp-L is not run: main1-L contains G0 G1F O0 OK1 already (plan 10.3). main2b-1024 is not run: HB is inside main2-L (plan 10.6).
# DO NOT resume jobs/cp2/run_all.sh (v3: it would run v3 stages with ours at 2 in flight).
J=/notebooks/hm-jobs/cp2
source "$J/common.sh"
TIER1=${TIER1-"gate4 main2-1024 hprobe1-1024 hprobe1b-1024 uprobe1 sweep1-1024 edge-1024 main1-1024 mech1-1024 qv4 hprobe1-2048 sweep1-2048 edge-2048 main1-2048 hbcheck-2048 main2-2048 qv4p-2048 main2i4-2048"}   # env overrides (a partial re-run)
TIER2=${TIER2-"edgelate-1024 hprobe1-4096 sweep1-4096 edge-4096 main1-4096 hbcheck-4096 main2-4096 qv4p-4096 qv4off mech1-2048 mech1-4096 ref2-2048 ref2-4096 q4096v4 repl1-1024 repl2-1024 ev2-1024"}
mkdir -p "$RES"
runstage() {
    local s=$1 mode=${2:-} L p p1
    case $s in
        qv4) bash "$J/quality.sh" v4 $mode ;;
        qv4off) bash "$J/quality.sh" v4off $mode ;;
        q4096v4) bash "$J/quality.sh" q4096v4 $mode ;;
        qv4p-*) L=${s#qv4p-}; p=$(BESTP_FILE=best_p1.txt bestp "$L" on); p1=$(BESTP_FILE=best_p1.txt bestp 1024 on)
            [ -z "$p" ] || [ "$p" = "$p1" ] || bash "$J/quality.sh" v4p "$p" $mode ;;   # only when p*_on(L) differs from p*_on(1024)
        edgelate-1024) [ "$(BESTP_FILE=best_p1.txt bestp 1024 off)" = 6144 ] && bash "$J/eval3.sh" sweep1lo-1024 $mode; return 0 ;;   # deferred from Tier 1: the extension of the 1024 O0 sweep
        edge-*) L=${s#edge-}   # O0's sweep minimum at the range edge 6144 -> O0 at p = 1024..5120 (the main1 of this length is not delayed at 1024: it runs at the edge, labelled)
            [ "$(BESTP_FILE=best_p1.txt bestp "$L" off)" = 6144 ] && [ "$L" != 1024 ] && bash "$J/eval3.sh" "sweep1lo-$L" $mode; return 0 ;;
        *) bash "$J/eval3.sh" "$s" $mode ;;
    esac
}
gate_ok() { local bad; bad=$(ls "$RES"/gate4/*/BAD_* "$RES"/gate4/*/FAILED 2>/dev/null); [ -z "$bad" ] || { echo "gate4 problems: $bad"; return 1; }; }
stopped=0; : > "$RES/remaining.tmp"
for s in $TIER1 $TIER2; do
    if [ $stopped = 0 ] && past_deadline; then stopped=1; fi
    if [ $stopped = 0 ]; then
        echo "=== $(date -u +%H:%M:%S) $s"
        runstage "$s"; rc=$?
        [ $rc = 75 ] && stopped=1
        if [ "$s" = gate4 ]; then [ $rc = 0 ] && gate_ok || { echo "gate4 failed (exit $rc): fix before the timed stages"; rm -f "$RES/remaining.tmp"; exit 3; }; fi
        [ $rc = 0 ] || [ $rc = 75 ] || echo "stage $s exit $rc (continuing)"
        [ "$s" = uprobe1 ] && echo "HP1 uses UNCACHED: $(cat "$RES/hp1_u.txt" 2>/dev/null)"
        [ "$s" = sweep1-1024 ] && [ "$(BESTP_FILE=best_p1.txt bestp 1024 off)" = 6144 ] && echo "O0 sweep minimum at the edge 6144 at 1024: sweep1lo-1024 is queued at the start of Tier 2"
    fi
    if [ $stopped = 1 ]; then
        case $s in edge-*|edgelate-*) ;; *) runstage "$s" --remaining 2>&1 | tail -n 400 >> "$RES/remaining.tmp" ;; esac
    fi
done
if [ $stopped = 1 ]; then mv "$RES/remaining.tmp" "$RES/remaining.txt"; echo "deadline reached: remaining work in $RES/remaining.txt"; else rm -f "$RES/remaining.tmp" "$RES/remaining.txt"; echo "all stages done"; fi
exit 0
