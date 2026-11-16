#!/usr/bin/env bash
# Q1 correctness (eval_plan_v3): last-token logits of each path vs G0, one fresh process per (prompt, path), scoring skipped.
#   bash quality.sh q1      8 prompts of 1024 tokens (seeds 1,2 = existing sampled-1/-2; seeds 3..8 sampled here) x {G0, G0 control, G1, H0, H1, O0, O1}
#   bash quality.sh gate    gate version: prompt seed 1 only, O1 at p=8192 (the 11-14 configuration) and no O0
#   bash quality.sh bitwise Gate: step-1 prefill logits of the frozen build vs the unchanged reference build $REFSRC (default /notebooks/hm-main),
#                           O0 and O1 switches, P8192, 1024 tokens, torch.equal via bitwise_compare.py (= jobs/memopt/compare.py); also first token
#   bash quality.sh q4096   Tier 2: 4 prompts of 4096 tokens (seeds 1..4, sampled here), p from best_p at 4096
# v4 (eval_plan_v4 section 5; every path at its own regime's in-flight count, p from best_p1.txt, HP from hm1_<L>.json / hm1o_<L>.json):
#   bash quality.sh v4        8 prompts x 1024 tokens: G0, G0 control, G1, O1 p*_on, HP1 (all 1 in flight), H1 g512u512d0, HT1 shipped (2 in flight) -> quality-v4/
#   bash quality.sh v4off     the same prompts: O0 p*_off, HP0 (1 in flight), H0, HT0 (2); seed-1 files of earlier runs are reused (copied after an env/config check)
#   bash quality.sh v4p P     O1 at p=P (p*_on of 2048 or 4096 when it differs from 1024), 1024-token prompts
#   bash quality.sh pmbq | pmbq4096   the per-micro-batch search picks (pmb_top_<L>.txt, H1 switches, 2 in flight) added to quality-v4 / quality-v4-4096
#   bash quality.sh v5q L     eval_plan_v5 rows C/D: G0 (+control), HS1 author entry, HS1.ours_gu (hso_<L>.json), no --inflight as in m2b-L; 2048 -> quality-v4-2048 (8), 4096 -> quality-v4-4096 (4)
#   bash quality.sh ggq       diagnostic (11-15): HeteroMosaic runtime with 0/0/0 on both micro-batches (pm_GG_1024.json, H1 switches) at 2 and 1 in flight, quality-v4 prompts
#   bash quality.sh q4096v4   4 prompts x 4096 tokens, the on paths (G0, G0 control, G1, O1 p*_on(4096), HP1, H1, HT1) -> quality-v4-4096/
# Add --remaining to list the missing runs. Resumable: an existing .npz is kept. Results $RES/quality[-gate|-4096]/seed<N>/*.npz, comparison-<N>.json.
# G0 is gpu_original-L-r0 and its control gpu_original-L-r1 (path_logits.py --compare looks for that stem); other stems are the cell names.
set -uo pipefail
MODE=${1:?q1|gate|q4096|v4|v4off|v4p P|q4096v4|pmbq|pmbq4096}; REM=${2:-}; PP=""
[ "$MODE" = v4p ] && { PP=${2:?v4p needs P}; REM=${3:-}; }
[ "$MODE" = ggq ] && REM=${2:-}
[ "$MODE" = v5q ] && { VL=${2:?v5q needs L (2048|4096)}; REM=${3:-}; }
case $MODE in v4|v4off|v4p|q4096v4|pmbq|pmbq4096) export BESTP_FILE=best_p1.txt ;; esac
source "$(dirname "$0")/common.sh"
env_setup
if [ $MODE = bitwise ]; then
    REFSRC=${REFSRC:-/notebooks/hm-main}; OUT=$RES/gate-bitwise; mkdir -p "$OUT"; status=0
    for name in O0 O1; do for which in ref new; do
        [ -s "$OUT/$name-1024-$which.npz" ] && continue
        [ -n "$REM" ] && { echo "bitwise: $name-$which"; continue; }
        past_deadline && { echo "deadline $STOP"; exit 75; }
        [ $which = ref ] && T=$REFSRC || T=$SRC
        cell_switches $name
        ( exec 9> "$LOCK"; flock 9; cd "$T"; clear_switches; for pair in $SW; do export "$pair"; done
          env | grep '^HETEROMEGA_' | sort > "$OUT/$name-1024-$which.env"
          export PYTHONPATH="$T/build/py:$T/build/py/unified_llm_w4a16:$T" HETEROMOSAIC_ROOT="$T"
          LD_PRELOAD=$T/deployment-results/count_ioctls.so timeout -k 30 1800 python3 tools/npu_error_probe/path_logits.py --method merged_ffn \
              --model "$MODEL" --build build --merged-ffn-config "$T/deployment-results/deployment-p8192.json" --ref "$REF" --prompt-tokens 1024 \
              --inflight 2 --ppl-tokens 64 --new-tokens 64 --out "$OUT/$name-1024-$which.npz" ) > "$OUT/$name-1024-$which.log" 2>&1 \
            && echo "$name $which ok" || { echo "$name $which FAILED"; status=1; }
    done; done
    [ -z "$REM" ] && python3 "$JOBS/bitwise_compare.py" logits "$OUT" | tee "$OUT/compare.txt"
    exit $status
fi
case $MODE in
    q1) L=1024; SEEDS="1 2 3 4 5 6 7 8"; OUT=$RES/quality ;;
    gate) L=1024; SEEDS="1"; OUT=$RES/quality-gate ;;
    q4096) L=4096; SEEDS="1 2 3 4"; OUT=$RES/quality-4096 ;;
    v4|v4off|v4p) L=1024; SEEDS="1 2 3 4 5 6 7 8"; OUT=$RES/quality-v4 ;;
    q4096v4|pmbq4096) L=4096; SEEDS="1 2 3 4"; OUT=$RES/quality-v4-4096 ;;
    pmbq|ggq) L=1024; SEEDS="1 2 3 4 5 6 7 8"; OUT=$RES/quality-v4 ;;
    v5q) L=$VL; case $L in 2048) SEEDS="1 2 3 4 5 6 7 8" ;; 4096) SEEDS="1 2 3 4" ;; *) echo "v5q: L must be 2048 or 4096"; exit 2 ;; esac; OUT=$RES/quality-v4-$L ;;
esac
case $MODE in
    v4|q4096v4) [ -n "$(bestp $L on)" ] || { echo "no best_p1 on-p for $L"; exit 2; } ;;
    v4off) [ -n "$(bestp $L off)" ] || { echo "no best_p1 off-p for $L"; exit 2; } ;;
esac
case $MODE in v4|v4off|v4p|q4096v4|pmbq|pmbq4096|v5q|ggq) ;; *) [ $MODE != gate ] && { [ -n "$(bestp $L on)" ] && [ -n "$(bestp $L off)" ] || { echo "no best p for $L (sweeps first, or P_ON_$L / P_OFF_$L)"; exit 2; }; } ;; esac
MAXSEQ=$((L + 160)); [ $L = 1024 ] && MAXSEQ=1600
prompt() { # SEED -> prompt file; existing sampled-1/-2 have 1536 tokens, others are sampled here (gpu_original, temperature 1)
    if [ $L = 1024 ] && [ "$1" -le 2 ]; then echo "$PROMPTS/sampled-$1.json"; else echo "$PROMPTS/sampled${L}-$1.json"; fi
}
paths() { # stem method build cfg-or-p switches
    local on off; on=$(bestp $L on); off=$(bestp $L off)
    [ $MODE = gate ] && { on=8192; off=""; }
    echo "gpu_original-$L-r0|gpu_original|build||"
    echo "gpu_original-$L-r1|gpu_original|build||"
    echo "G1-$L-r0|gpu_ffn_all|build-gpuffn||$GEN $FU"
    echo "H0-$L-r0|heteromosaic|build|$CFGDIR/hm_$L.json|"
    echo "H1-$L-r0|heteromosaic|build|$CFGDIR/hm_$L.json|$GEN"
    [ -n "$off" ] && echo "O0-$L-r0|merged_ffn|build|p$off|$SB"
    echo "O1-$L-r0|merged_ffn|build|p$on|$GEN $U $FU $RN $SB"
}
swof() { cell_switches "$1"; echo "$SW"; }
paths4() { # stem|method|build|cfg-or-p|switches|inflight
    local g0="gpu_original-$L-r0|gpu_original|build|||1
gpu_original-$L-r1|gpu_original|build|||1"
    case $MODE in
        v4|q4096v4) echo "$g0"
            echo "G1-$L-r0|gpu_ffn_all|build-gpuffn||$(swof G1)|1"
            echo "O1-$L-r0|merged_ffn|build|p$(bestp $L on)|$(swof O1)|1"
            echo "HP1-$L-r0|heteromosaic|build|$CFGDIR/hm1_$L.json|$(swof HP1)|1"
            echo "H1-$L-r0|heteromosaic|build|$CFGDIR/hm_$L.json|$(swof H1)|2"
            echo "HT1-$L-r0|heteromosaic|build|$CFGDIR/hm_$L.shipped.json|$(swof HT1)|2" ;;
        v4off) echo "$g0"
            echo "O0-$L-r0|merged_ffn|build|p$(bestp $L off)|$(swof O0)|1"
            echo "HP0-$L-r0|heteromosaic|build|$CFGDIR/hm1o_$L.json|$(swof HP0)|1"
            echo "H0-$L-r0|heteromosaic|build|$CFGDIR/hm_$L.json|$(swof H0)|2"
            echo "HT0-$L-r0|heteromosaic|build|$CFGDIR/hm_$L.shipped.json|$(swof HT0)|2" ;;
        v4p) echo "$g0"; echo "O1p$PP-$L-r0|merged_ffn|build|p$PP|$(swof O1)|1" ;;
        v5q) echo "$g0"
            echo "G1-$L-r0|gpu_ffn_all|build-gpuffn||$(swof G1)|1"   # second reference (GPU-only, new kernels); kept if it already exists (4096)
            echo "HS1-$L-r0|heteromosaic|build|$CFGDIR/hs.json|$(swof HS1)|-"
            echo "HS1.ours_gu-$L-r0|heteromosaic|build|$CFGDIR/hso_$L.json|$(swof HS1)|-" ;;
        ggq) echo "$g0"; for i in 2 1; do echo "PM.GG_i$i-1024-r0|heteromosaic|build|$CFGDIR/pm_GG_1024.json|$(swof H1)|$i"; done ;;
        pmbq|pmbq4096) local t; echo "$g0"; for t in $(cat "$CFGDIR/pmb_top_$L.txt"); do echo "PM.$t-$L-r0|heteromosaic|build|$CFGDIR/pm_${t}_$L.json|$(swof H1)|2"; done ;;
    esac
}
reuse() { # OLDPATH-without-.npz DSTSTEM PLANNED-CONFIG-or-empty SWITCHES [LOG]: copy a seed-1 result of an earlier run when its env/config/log show the same path
    local o=$1 dst=$2 cfgp=$3 sw=$4 logf=${5:-} has=0 want=0
    [ -s "$D/$dst.npz" ] || [ ! -s "$o.npz" ] && return
    [ -z "$cfgp" ] || python3 "$JOBS/hm_ratio.py" "$CFGDIR" same "$o.config.json" "$cfgp" "$L" || { echo "no reuse of $dst: config differs"; return; }
    if [ -s "$o.env" ]; then
        diff -q <(sort "$o.env") <({ echo HETEROMEGA_FFN_FINITE_CHECK=sampled; for x in $sw; do echo "$x"; done; } | sort) > /dev/null || { echo "no reuse of $dst: env differs"; return; }
    fi
    if [ -n "$logf" ]; then grep -q sdpa_bf16 "$logf" && has=1; [ -n "$sw" ] && want=1; [ $has = $want ] || { echo "no reuse of $dst: log kernels differ"; return; }; fi
    cp "$o.npz" "$D/$dst.npz"; echo "copied from $o (checkout hm-cp2; v4 runs hm-cp2b)" > "$D/$dst.reused"
}
seed1_reuse() { # v4/v4off at 1024, seed 1 only
    local Q=$RES/quality-gate/seed1 C=$RES/hcheck
    if [ $MODE = v4 ]; then
        reuse $Q/gpu_original-1024-r0 gpu_original-1024-r0 "" ""; reuse $Q/gpu_original-1024-r1 gpu_original-1024-r1 "" ""
        reuse $Q/G1-1024-r0 G1-1024-r0 "" "$(swof G1)"
        reuse $Q/H1-1024-r0 HT1-1024-r0 "$CFGDIR/hm_1024.shipped.json" "$(swof HT1)"
        reuse $C/H1g512-1024-r0 H1-1024-r0 "$CFGDIR/hm_1024.json" "$(swof H1)" $C/H1.log
    else
        reuse $Q/gpu_original-1024-r0 gpu_original-1024-r0 "" ""; reuse $Q/gpu_original-1024-r1 gpu_original-1024-r1 "" ""
        reuse $Q/H0-1024-r0 HT0-1024-r0 "$CFGDIR/hm_1024.shipped.json" ""
        reuse $C/H0g512-1024-r0 H0-1024-r0 "$CFGDIR/hm_1024.json" "" $C/H0.log
    fi
}
status=0
for s in $SEEDS; do
    f=$(prompt "$s"); D=$OUT/seed$s; mkdir -p "$D"
    PATHS=paths; case $MODE in v4|v4off|v4p|q4096v4|pmbq|pmbq4096|v5q|ggq) PATHS=paths4; [ "$s" = 1 ] && [ "$L" = 1024 ] && [ $MODE != v4p ] && [ $MODE != pmbq ] && [ $MODE != ggq ] && [ -z "$REM" ] && seed1_reuse ;; esac
    if [ ! -s "$f" ]; then
        [ -n "$REM" ] && { echo "$MODE: prompt $f"; continue; }
        past_deadline && { echo "deadline $STOP"; exit 75; }
        ( exec 9> "$LOCK"; flock 9; clear_switches; export PYTHONPATH="$SRC/build/py:$SRC/build/py/unified_llm_w4a16:$SRC"
          python3 tools/npu_error_probe/path_logits.py --sample-prompt "$f" --seed "$s" --sample-tokens "$L" --max-seq-len "$MAXSEQ" \
              --model "$MODEL" --build build ) > "$D/sample.log" 2>&1 || { echo "sampling seed $s failed"; status=1; continue; }
    fi
    while IFS='|' read -r stem method build cfg sw infl4; do
        [ -s "$D/$stem.npz" ] && continue
        [ -n "$REM" ] && { echo "$MODE: seed$s/$stem"; continue; }
        past_deadline && { echo "deadline $STOP"; exit 75; }
        infl=2; [ "$method" = gpu_original ] || [ "$method" = gpu_ffn_all ] && infl=1; [ -n "${infl4:-}" ] && infl=$infl4
        args=(--method "$method" --model "$MODEL" --build "$build" --ref "$f" --prompt-tokens "$L" --chunk 512
              --max-seq-len "$MAXSEQ" --no-score --out "$D/$stem.npz")
        [ "$infl" = - ] || args+=(--inflight "$infl")   # "-": no --inflight, the runtime selects the author's entry (v5q, as m2b-L)
        case $cfg in p*) args+=(--merged-ffn-config "$SRC/deployment-results/deployment-$cfg.json") ;; ?*) args+=(--config "$cfg") ;; esac
        ( exec 9> "$LOCK"; flock 9; clear_switches
          for pair in $sw; do export "$pair"; done
          env | grep '^HETEROMEGA_' | sort > "$D/$stem.env"
          export PYTHONPATH="$SRC/$build/py:$SRC/$build/py/unified_llm_w4a16:$SRC"
          LD_PRELOAD=$COUNT timeout -k 30 1200 python3 tools/npu_error_probe/path_logits.py "${args[@]}"
        ) > "$D/$stem.log" 2>&1 < /dev/null && echo "$(date -u +%H:%M:%S) seed$s $stem ok" || { echo "seed$s $stem FAILED: $(grep -hiE 'error|Traceback' "$D/$stem.log" | tail -1 | cut -c1-200)"; status=1; }
    done < <($PATHS)
    [ -z "$REM" ] && [ -s "$D/gpu_original-$L-r0.npz" ] && python3 tools/npu_error_probe/path_logits.py --compare "$D" --json "$OUT/comparison-$s.json" > "$OUT/comparison-$s.txt" 2>&1
done
exit $status
