#!/usr/bin/env bash
# CP2 evaluation runner (eval_plan_v3, extended by eval_plan_v4 incl. section 10). One stage per call: bash eval3.sh STAGE [--list | --remaining]
# v3 stages (in-flight 2 for H*/O*, kept for the record, never part of v4 tables): build compile gates sweep-1024 main-1024 mech-1024 sweep-4096
#   main-4096 sweep-2048 main-2048 abl-* mech-2048 mech-4096 t2-ref sweep-rest t2-o0rerun repl-1024
# v4 stages (L = 1024 2048 4096; every cell passes infl= explicitly; SRC default /notebooks/hm-cp2b):
#   regime 1 (1 in flight, best_p1.txt): gate4 (pre-launch smokes) uprobe1 hprobe1-L hprobe1b-1024 sweep1-L sweep1lo-L main1-L mech1-L kcmp-L repl1-1024
#   regime 2 (>= 2 in flight):           hbcheck-L main2-L main2i4-2048 ref2-L repl2-1024 ev2-1024         (quality: quality.sh v4 ...)
#   v5 (eval_plan_v5): v5smoke m4-2048 m2b-2048 m2b-4096; ablation split unit x in flight: abl1s-1024 (smoke) abl1-1024
#   per-micro-batch placement search (2 in flight): pmb1-L (middle, L=2048/4096) pmb2-L (first x last) pmbc-L (6x5 confirmation)
#   11-16 config-ranking check: rk1-1024 rk2-2048 rk3-2048 rk4-4096 (settings S1-S4, make_rk_configs.py; rk<S>s-L = 1x1 smoke), our search in the
#   AFTER environment apmb1-L apmb2-L apmbc-L (L=2048/4096; apmbs-L = 1x1 smoke). Their processes carry src= (tree hm-<src>) and pass rk_check.py.
#   bash eval3.sh STAGE --dry prints the effective config of every cell without running anything.
# A process whose log shows another in-flight count than its case.txt gets BAD_INFLIGHT (aggregate.py drops it).
# One process per case (evaluate_prefill.py --rounds 1). The stage's process list is shuffled once with a logged seed into
# $RES/STAGE/schedule.txt and reused on resume; a process whose dir has DONE is skipped, so re-running the same command continues.
# Exit: 0 all done, 1 some process failed, 75 deadline (STOP_LONG_AFTER_UTC) reached.  NOU="O1:4096 H1:4096" runs those cells as -U.
set -uo pipefail
STAGE=${1:?stage}; MODE=${2:-run}
source "$(dirname "$0")/common.sh"
case $STAGE in *-8192) REF=$PROMPTS/sampled-8256.json ;; *-16384) REF=$PROMPTS/sampled-16448.json ;; esac   # v5 rows 8192/16384: sampled-4160 is too short; same sampler, seed 1
SD=$RES/$STAGE
status=0
case $STAGE in sweep1-*|sweep1lo-*|main1-*|mech1-*|hprobe1*|kcmp-*|repl1-*|uprobe1) export BESTP_FILE=best_p1.txt ;; esac   # 1-in-flight sweep, not best_p.txt
LEN=${STAGE##*-}

bestp_or_die() { local p; p=$(bestp "$1" "$2"); [ -n "$p" ] || { echo "no p for L=$1 state=$2 (run sweep-$1 first, or set P_$(echo $2 | tr a-z A-Z)_$1)" >&2; exit 2; }; echo "$p"; }

procs() { # CELL L N REPS [opts]: N process lines; a bare O cell gets its p from best_p; NOU swaps in the -U fallback
    local c=$1 L=$2 n=$3 reps=$4 p="" k fb; shift 4
    if [[ $c =~ ^(O[A-Za-z0-9]*)p([0-9]+)$ ]]; then c=${BASH_REMATCH[1]}; p=${BASH_REMATCH[2]}; fi
    fb=$(fallback_of "$c"); case " ${NOU:-} " in *" $c:$L "*) [ -n "$fb" ] && c=$fb ;; esac
    if [[ $c == O* && -z $p ]]; then p=$(bestp_or_die "$L" "$([ "$c" = O0 ] && echo off || echo on)") || exit 2; fi
    for ((k = 1; k <= n; k++)); do echo "$c${p:+p$p} $L $k $reps $*"; done
}

procs_i() { local i=$1; shift; local a=("$@"); procs "${a[@]}" infl=$i; }   # procs with an explicit in-flight count: procs_i INFL CELL L N REPS [opts]

emit() { # the stage's processes, one line each: CELL L K REPS [tag= nt= infl= E=NAME=VALUE]
    local L c p
    case $STAGE in
        # ---- v4 (eval_plan_v4): regime 1 = one chunk in flight -------------------------------------------------------------------------
        uprobe1)  # HP1 + UNCACHED memory probe, 1 rep (plan 10.4); fits at both lengths -> hp1_u.txt = yes -> HP1 runs with UNCACHED
            for L in 1024 4096; do procs_i 1 HP1U $L 1 1 cfg=hm_$L.json; done ;;
        hprobe1-*) L=${STAGE#hprobe1-}   # 1024: screen of the 26 uniform combos, H1 only, 1 process x 5 reps; 2048/4096: top 3 of 1024 + shipped table, 1 x 3
            if [ "$L" = 1024 ]; then
                for c in $(python3 "$JOBS/hm_ratio.py" "$CFGDIR" combos1); do procs_i 1 H1 1024 1 5 tag=$c cfg=hp1_$c.json; done
            else
                for c in $(python3 "$JOBS/hm_ratio.py" "$CFGDIR" top1) shipped; do
                    if [ $c = shipped ]; then cf=hm_$L.shipped.json; else cf=hp1_${c}_$L.json; fi
                    procs_i 1 H1 $L 1 3 tag=$c cfg=$cf; procs_i 1 H0 $L 1 3 tag=$c cfg=$cf; done
            fi ;;
        hprobe1b-1024) for c in $(python3 "$JOBS/hm_ratio.py" "$CFGDIR" top1); do procs_i 1 H1 1024 2 5 tag=$c cfg=hp1_$c.json; procs_i 1 H0 1024 1 5 tag=$c cfg=hp1_$c.json; done ;;   # top 3 of the screen: H1 2 more processes; H0 1 process (its own pick, hm1o)
        sweep1-*) L=${STAGE#sweep1-}   # kernels on p=1024..13312 (13 points), off p=6144..13312 (8 points); 1 process x 3 reps at 1 in flight
            for p in 1024 2048 3072 4096 5120 6144 7168 8192 9216 10240 11264 12288 13312; do procs_i 1 O1p$p "$L" 1 3; done
            for p in 6144 7168 8192 9216 10240 11264 12288 13312; do procs_i 1 O0p$p "$L" 1 3; done ;;
        sweep1lo-*) L=${STAGE#sweep1lo-}; for p in 1024 2048 3072 4096 5120; do procs_i 1 O0p$p "$L" 1 3; done ;;   # only if O0's minimum sat at 6144
        main1-*) L=${STAGE#main1-}   # headline cells; HP0/HP1 use hm1_<L>.json; OK1 and G1F at every length (same-bundle row)
            for c in G0 G1 G1F HP0 HP1 O0 O1 OK1; do procs_i 1 $c "$L" 6 5; done
            if [ "$L" = 1024 ]; then procs_i 1 O1F "$L" 6 5; fi ;;   # if, not &&: emit's status must be 0 at L != 1024
        mech1-*) L=${STAGE#mech1-}   # A1: count pairs and stage events; A2: O1F vs O1 (6x5 here at 2048/4096, inside main1-1024 at 1024); timers
            if [ "$L" != 1024 ]; then procs_i 1 O1 "$L" 6 5; procs_i 1 O1F "$L" 6 5; fi
            for c in HP1 O1; do procs_i 1 $c "$L" 1 1 tag=c1 nt=1; procs_i 1 $c "$L" 1 2 tag=c2 nt=1; done
            if [ "$L" = 1024 ]; then for c in G0 G1 HP0 HP1 O0 O1 OK1 O1F; do procs_i 1 $c "$L" 1 2 tag=ev1 E=HETEROMEGA_STAGE_EVENTS=@D/ev; done
            else for c in G1 HP1 O1 OK1 O1F; do procs_i 1 $c "$L" 1 2 tag=ev1 E=HETEROMEGA_STAGE_EVENTS=@D/ev; done; fi
            procs_i 1 O1 "$L" 1 2 tag=tm E=HETEROMEGA_FFN_TIMERS=@D/tm
            procs_i 1 O1F "$L" 1 2 tag=tmF E=HETEROMEGA_FFN_TIMERS=@D/tm ;;
        kcmp-*) L=${STAGE#kcmp-}; for c in G0 G1F O0 OK1; do procs_i 1 $c "$L" 6 5; done ;;   # contained in main1-L now (G1F, OK1 added by plan 10.3); not in run_v4.sh
        gate4)  # pre-launch smokes (plan 11): 1 process x 1 rep; look at BAD_INFLIGHT / BAD_SELECTION / merged verdict of each
            for c in O1p13312 O1Fp13312 OK1p13312; do procs_i 1 $c 1024 1 1; done
            procs_i 1 HP1 1024 1 1 cfg=hp_g256u256d0.json; procs_i 1 HT1 1024 1 1; procs_i 4 H1 2048 1 1 ;;
        repl1-1024) for c in O1 HP1 G1; do procs_i 1 $c 1024 6 5; done ;;
        kab1-1024|kab1s-1024)   # 11-15 user: kernel ablation at 1 micro-batch in flight, three ladders in one randomized stage; kab1s = 1-rep smoke of every cell
            n=6; r=5; [ "$STAGE" = kab1s-1024 ] && { n=1; r=1; }
            for c in G0 GKM G1F G1 HK0 HKM HK1 HKU O0p5120 OKMp5120 OK1p5120 O1Fp5120 O1p5120; do procs_i 1 $c 1024 $n $r; done
            [ "$STAGE" = kab1-1024 ] && procs_i 1 O0p6144 1024 6 5; true ;;   # O0 at p*_off = 6144 too: the regime-1 row at 1024 uses the same p as main1a-2048/4096
        mech1a-*) L=${STAGE#mech1a-}   # 11-15: A1 diagnostics vs the author's HeteroMosaic entry (HKU = GEN+UNCACHED, labelled fallback HKUnU) at 1 in flight
            hk=HKU; [ "$L" = 1024 ] || hk=HKUnU   # UNCACHED where it fits: full fit only at 1024 (2048 partial, 4096 OOM in main1as)
            for c in $hk O1p5120; do procs_i 1 $c "$L" 1 2 tag=ev1 E=HETEROMEGA_STAGE_EVENTS=@D/ev; done
            if [ "$L" = 1024 ]; then for c in HKU O1p5120; do procs_i 1 $c 1024 1 1 tag=c1 nt=1; procs_i 1 $c 1024 1 2 tag=c2 nt=1; done; fi ;;
        main1a-*|main1as-*) L=${STAGE##*-}   # 11-15 user: regime 1 at 2048/4096, HeteroMosaic at the author's entry for L (HK*: hm_<L>.shipped.json) at 1 in flight
            if [[ $STAGE == main1as-* ]]; then for c in HK0 HKU; do procs_i 1 $c "$L" 1 1; done   # smoke of the new cells at L
            elif [ "$L" = 2048 ]; then for c in G0 G1 HK0 HKU HKUnU O0p6144 O1p5120; do procs_i 1 $c "$L" 6 5; done   # HKU smoke: 4 UNCACHED_FALLBACK calls (partial) -> HKUnU also run, used in the table
            else for c in G0 G1 HK0 HKUnU O0p6144 O1p5120; do procs_i 1 $c "$L" 6 5; done; fi ;;   # 4096: HKU OOM in the smoke -> labelled HKUnU only
        # ---- v4: regime 2 = two or more chunks in flight (ours absent) ------------------------------------------------------------------
        hbcheck-*) L=${STAGE#hbcheck-}   # HB = best token split at 2 in flight: 4 candidates, H1, 1 process x 3 reps (1024 uses the hprobe-1024 winner g256u256d256)
            for c in g256u256d0 g256u256d256 g256u256d512 g512u512d256; do procs_i 2 H1 "$L" 1 3 tag=$c cfg=hb_${c}_$L.json; done ;;
        main2-*) L=${STAGE#main2-}   # H = g512u512d0, HT = shipped token split, HB = best token split; only cells at >= 2 in flight (plan 11.4; the 1-in-flight
            for c in H0 H1 HT0 HT1 HB0 HB1; do procs_i 2 $c "$L" 6 5; done ;;   # numbers of the same configs come from hprobe1-L, shown cross-stage by aggregate.py)
        main2i4-2048) for c in H0 H1 HT0 HT1; do procs_i 4 $c 2048 3 5; done ;;
        uni2-*) L=${STAGE#uni2-}; procs_i 2 H1 "$L" 6 5 tag=g256u256d0 cfg=hb_g256u256d0_$L.json; procs_i 2 H1 "$L" 3 5 ;;   # 11-15 user: uniform 256/256/0 (HeteroMosaic 1024 setting) at every length, 2 concurrent; 512/512/0 x3 anchor
        rev2-1024) procs_i 2 H1 1024 6 5 tag=g0u0d512 cfg=hp_g0u0d512.json; procs_i 2 H1 1024 3 5 ;;   # 11-15 user: reverse split 0/0/512 at depth 2, formal 6x5; 512/512/0 x3 as same-stage anchor   # reference pair at the 2048 shipped table's own in-flight count
        ref2-*) L=${STAGE#ref2-}; for c in HS0 HS1; do procs $c "$L" 3 5; done ;;   # shipped chunking and in-flight (no --inflight): reference rows only
        repl2-1024) for c in H1 HT1; do procs_i 2 $c 1024 6 5; done ;;
        pmb1-*|pmb2-*) L=${STAGE#pmb?-}; f=$CFGDIR/pmb_mid_$L.txt; [[ $STAGE == pmb2-* ]] && f=$CFGDIR/pmb_ends_$L.txt   # 11-15 user: per-micro-batch placement
            for t in $(cat "$f" 2>/dev/null); do procs_i 2 H1 "$L" 1 3 tag=$t cfg=pm_${t}_$L.json; done ;;   # search screen (hm_ratio.py pmb_*), 1 process x 3 reps
        pmbc-*) L=${STAGE#pmbc-}   # confirmation: top 2 of the screens, uniform 512/512/0 (H1), uniform 0/0/512, the author's setting (HT1) and GPU-only (G1), 6x5 in one stage
            top=$(cat "$CFGDIR/pmb_top_$L.txt" 2>/dev/null); rev=$(printf "B%.0s" $(seq $((L / 512))))
            for t in $top; do procs_i 2 H1 "$L" 6 5 tag=$t cfg=pm_${t}_$L.json; done
            case " $top " in *" $rev "*) ;; *) procs_i 2 H1 "$L" 6 5 tag=$rev cfg=pm_${rev}_$L.json ;; esac
            for c in H1 HT1; do procs_i 2 $c "$L" 6 5; done
            procs_i 1 G1 "$L" 6 5 ;;   # GPU-only (all new kernels, 1 in flight) in the same stage: ours-vs-GPU-only at 2 in flight
        r1u-*) L=${STAGE#r1u-}; q=$(printf "Q%.0s" $(seq $((L / 512))))   # 11-15 user: HeteroMosaic config chosen by in-flight count: 1 in flight = 256/256/0
            procs_i 1 HKUnU "$L" 6 5 tag=$q cfg=pm_${q}_$L.json; for c in G1 O1p5120; do procs_i 1 $c "$L" 6 5; done ;;   # on every micro-batch (no UNCACHED, as HKUnU in main1a); same-stage ours and GPU-only
        ev2-1024) for c in H1 HT1; do procs_i 2 $c 1024 1 2 tag=ev2 E=HETEROMEGA_STAGE_EVENTS=@D/ev; done ;;
        # ---- 11-16 user: config-ranking check, S<n> = the reported row's setting (make_rk_configs.py); only gate/up/down change in a setting.
        # tag B_<cand> = BEFORE (hm-cp2b, no switches, original binaries, the author's attention on the NPU), A_<cand> = AFTER (hm-npualign, the
        # reported switches, our binaries), M_auth = MIDDLE (the reported cell), K_auth = KEYONLY (MIDDLE on hm-npualign: new PDI key, original binaries)
        rk[1-4]-*|rk[1-4]s-*) local S=${STAGE:2:1} n=6 m=3 r=5 hb ha fl cands ours rep k
            [[ $STAGE == rk?s-* ]] && { n=1; m=1; r=1; }
            case $S in 1) hb=HK0 ha=HKU fl=1 rep=hm_1024.shipped.json ours="" cands="auth g512u0d0 g256u0d0 g0u0d256" ;;   # kab1-1024 HKU
                       2) hb=HT0 ha=HT1 fl=4 rep=hm_2048.shipped.json ours=g512u512d0 cands="auth g512u512d0 AAAB g256u256d256" ;;   # m4-2048
                       3) hb=HS0 ha=HS1 fl="" rep=hs.json ours=g1024u1024d0 cands="auth g1024u1024d0 g1024u512d0 g1024u1024d256" ;;   # m2b-2048
                       4) hb=HS0 ha=HS1 fl="" rep=hs.json ours=g2048u2048d0 cands="auth g2048u2048d0 g1536u1536d0_g1792u1280d0 g2048u2048d512" ;; esac
            L=${STAGE##*-}
            for c in $cands; do
                k=$m; { [ $c = auth ] || [ $c = "$ours" ]; } && k=$n
                procs_i "$fl" $hb "$L" $m $r tag=B_$c cfg=rk${S}_${c}_b.json want=rk${S}_${c}_b.want.json src=cp2b
                procs_i "$fl" $ha "$L" $k $r tag=A_$c cfg=rk${S}_${c}_a.json want=rk${S}_${c}_a.want.json src=npualign
            done
            procs_i "$fl" $ha "$L" $n $r tag=M_auth cfg=$rep want=rk${S}_auth_m.want.json src=cp2b
            [ $S = 1 ] || procs_i "$fl" $ha "$L" $m $r tag=K_auth cfg=$rep want=rk${S}_auth_m.want.json src=npualign
            procs_i 1 G1 "$L" $n $r src=cp2b
            if [ $S = 1 ]; then procs_i 1 O1p5120 1024 $n $r src=cp2b; fi ;;   # ours as in kab1-1024
        apmb1-*|apmb2-*) L=${STAGE#apmb?-}; f=$CFGDIR/pmb_mid_$L.txt; [[ $STAGE == apmb2-* ]] && f=$CFGDIR/pmb_ends_$L.txt   # pmb1/pmb2, AFTER environment
            for t in $(cat "$f" 2>/dev/null); do procs_i 2 H1 "$L" 1 3 tag=$t cfg=pm_${t}_$L.ours.json src=npualign; done ;;
        apmbc-*|apmbs-*) L=${STAGE#apmb?-}; local n=6 r=5 top a S=3   # confirmation: top 2 of the screens, uniform 512/512/0 and 0/0/512, the AFTER author
            [[ $STAGE == apmbs-* ]] && { n=1; r=1; }                       # entry of the 2-in-flight setting (S3/S4) and G1, 6x5; smoke: the middle patterns, 1x1
            top=$(cat "$CFGDIR/pmb_top_$L.txt" 2>/dev/null); [[ $STAGE == apmbs-* ]] && top=$(cat "$CFGDIR/pmb_mid_$L.txt")
            a=$(printf "A%.0s" $(seq $((L / 512)))); [ "$L" = 4096 ] && S=4
            for t in $(printf "%s\n" $top $a ${a//A/B} | awk '!s[$0]++'); do procs_i 2 H1 "$L" $n $r tag=$t cfg=pm_${t}_$L.ours.json src=npualign; done
            procs HS1 "$L" $n $r tag=A_auth cfg=rk${S}_auth_a.json want=rk${S}_auth_a.want.json src=npualign
            procs_i 1 G1 "$L" $n $r src=cp2b ;;
        # ---- v3 stages ----------------------------------------------------------------------------------------------------------------
        gates)  # 1 process x 5 reps at 1024 (repro of the 11-14 numbers, memory-optimization check); 1 rep at 4096 = memory probes
            procs O1p8192 1024 1 5; procs HR 1024 1 5; procs H0 1024 1 5; procs H1 1024 1 5; procs G0 1024 1 5
            for c in O1p1024 O1p8192 H0 H1 G1; do procs $c 4096 1 1; done ;;
        sweep-hi-*) L=${STAGE#sweep-hi-}   # p > 8192 (hm-cp2b bounds patch); only p that passed smoke + logits (PHI_OK)
            for p in ${PHI_OK:-}; do procs O1p$p "$L" 1 3; procs O0p$p "$L" 1 3; done ;;
        main-1024-hp)  # O0/O1 main cells again at 1024 only if a p > 8192 won the sweep (labelled by stage)
            for st in on off; do p=$(bestp_or_die 1024 $st) || exit 2; c=O1; [ $st = off ] && c=O0
                [ "$p" -gt 8192 ] && procs ${c}p$p 1024 6 5; done ;;
        sweep-rest) for L in 1024 2048 4096; do for p in 1024 2048 3072 4096 5120; do procs O0p$p $L 1 3; done; done ;;
        sweep-*) L=${STAGE#sweep-}   # kernels on p=1024..8192; kernels off p=6144..8192 (Tier 1); 1 process x 3 reps
            for p in 1024 2048 3072 4096 5120 6144 7168 8192; do procs O1p$p "$L" 1 3; done
            for p in 6144 7168 8192; do procs O0p$p "$L" 1 3; done ;;
        main-*|repl-*) L=${STAGE#*-}
            for c in G0 G1 H0 H1 O0 O1; do procs $c "$L" 6 5; done
            [ "$STAGE" = main-4096 ] && procs HS "$L" 6 5
            case $STAGE in main-2048|main-4096) for c in G1 H1 O1; do procs $c "$L" 1 2 tag=ev1 infl=1 E=HETEROMEGA_STAGE_EVENTS=@D/ev; done ;; esac ;;
        hprobe-1024)  # HeteroMosaic FFN ratio probe (uniform gate/up/down npuM per chunk), H1 2 procs, H0 1 proc
            for c in $(python3 "$JOBS/hm_ratio.py" "$CFGDIR" combos); do procs H1 1024 2 5 tag=$c cfg=hp_$c.json; procs H0 1024 1 5 tag=$c cfg=hp_$c.json; done ;;
        hdiag-1024)  # why the shipped ratio is not optimal here: 1 chunk in flight, shipped (HR) vs re-tuned g512u512d0 (hm_1024), old/new kernels; g512 count pairs
            for c in H0 H1; do procs $c 1024 2 5 tag=hr1 cfg=hr.json infl=1; procs $c 1024 2 5 tag=g512i1 infl=1; done
            procs H1 1024 1 1 tag=c1 nt=1; procs H1 1024 1 2 tag=c2 nt=1 ;;
        mech-*) L=${STAGE#mech-}   # A2 cell, HR, count pairs, inflight-1 stage events (FFN stage time), FFN timers +- serialized GPU
            [ "$L" = 1024 ] && procs HR 1024 3 5
            procs O1F "$L" 6 5
            for c in H1 O1; do procs $c "$L" 1 1 tag=c1 nt=1; procs $c "$L" 1 2 tag=c2 nt=1; done
            [ "$L" = 1024 ] && for c in G0 G1 H0 H1 O0 O1; do procs $c "$L" 1 2 tag=ev1 infl=1 E=HETEROMEGA_STAGE_EVENTS=@D/ev; done
            procs O1 "$L" 1 2 tag=tm E=HETEROMEGA_FFN_TIMERS=@D/tm
            procs O1 "$L" 1 2 tag=tms E=HETEROMEGA_FFN_TIMERS=@D/tm E=HETEROMEGA_FFN_SERIAL_GPU=1 ;;
        abl-loo-1024) for c in HLs HLg OLs OLg O1nU; do procs $c 1024 3 5; done ;;
        abl-*) L=${STAGE#abl-}; for c in GA1 G1F HA1 OA1 OA2; do procs $c "$L" 3 5; done ;;
        t2-ref) for L in 1024 2048 4096; do procs GS $L 6 5; done; for L in 1024 2048; do procs HS $L 6 5; done ;;
        t2-o0rerun)  # O0 at a new p* (after the full off sweep) where the main O0 cell used another p
            for L in 1024 2048 4096; do p=$(bestp_or_die $L off) || exit 2
                ls -d "$RES"/main-$L/O0p$p-$L-s*/DONE >/dev/null 2>&1 || procs O0p$p $L 6 5; done ;;
        # ---- v5 (design/eval_plan_v5.md, 11-15): one row = one author entry; inside a row only the FFN split differs; GPU-only G1 in the same stage
        v5smoke) procs HS1 2048 1 1 tag=ours_gu cfg=hso_2048.json; procs HS1 4096 1 1 tag=ours_gu cfg=hso_4096.json ;;   # 1x1 smokes of the new ours cells
        m4-2048) procs_i 4 HT1 2048 6 5; procs_i 4 H1 2048 6 5; procs_i 1 G1 2048 6 5 ;;   # row B: 512 x 4, 4 in flight; HT1 = author's entry, H1 = 512/512/0 x4
        m2b-*) L=${STAGE#m2b-}   # rows C (2048 = 1024 x 2) / D (4096 = 2048 x 2): author's 2-in-flight entry as the runtime selects it (no --inflight);
            procs HS1 "$L" 6 5; procs HS1 "$L" 6 5 tag=ours_gu cfg=hso_$L.json; procs_i 1 G1 "$L" 6 5 ;;   # ours = same group, gate/up whole micro-batch on NPU, down on GPU
        abl1-1024|abl1s-1024)   # 11-15 user: split unit x in flight at 1024; every cell its own tag (plabel has no infl/cfg); smoke = 1x1
            n=6; r=5; [ "$STAGE" = abl1s-1024 ] && { n=1; r=1; }
            for i in 1 2; do procs_i $i OK1p5120 1024 $n $r tag=ch_i$i; procs_i $i H1 1024 $n $r tag=A_i$i; procs_i $i H1 1024 $n $r tag=B_i$i cfg=hp_g0u0d512.json; done ;;
        v7smoke-*) L=${STAGE#v7smoke-}; procs HS1 "$L" 1 1; procs HS1 "$L" 1 1 tag=ours_gu cfg=hso_$L.json; procs_i 1 G1 "$L" 1 1 ;;   # 8192/16384: 1x1 of all three cells
        *) echo "unknown stage $STAGE" >&2; exit 2 ;;
    esac
}

inflight_seen() { # effective in-flight count(s) of the process from its result log: "pipeline enabled with N" lines, "serial chunk execution" = 1
    { grep -ho 'pipeline enabled with [0-9]* inflight' "$1"/*.result.log 2>/dev/null | awk '{print $4}'
      grep -qh 'serial chunk execution' "$1"/*.result.log 2>/dev/null && echo 1; } | sort -u | paste -sd, -
}

plabel() { local c=$1 L=$2 k=$3 reps=$4 o tag=""; shift 4; for o in "$@"; do case $o in tag=*) tag=${o#tag=} ;; esac; done; echo "$c${tag:+.$tag}-$L-s$k"; }

attempt() { # CELL L K REPS opts: one process; 0 done, 1 recorded OOM, 2 other failure
    local cell=$1 L=$2 k=$3 reps=$4; shift 4
    local c=$cell p="" tag="" nt=64 infl="" cfgo="" envs=() o D METHOD BUILD CHUNK INFL CFG="" SW GRP=PK src="" want="" T=$SRC
    for o in "$@"; do case $o in tag=*) tag=${o#tag=} ;; nt=*) nt=${o#nt=} ;; infl=*) infl=${o#infl=} ;; E=*) envs+=("${o#E=}") ;; cfg=*) cfgo=${o#cfg=} ;;
                                 src=*) src=${o#src=} ;; want=*) want=${o#want=} ;; esac; done
    [ -n "$src" ] && T=/notebooks/hm-$src   # the cell's tree: cd, PYTHONPATH, HETEROMOSAIC_ROOT, build dir, ioctl counter, merged-FFN artifact
    [ -d "$T" ] || { echo "no tree $T"; return 2; }
    if [[ $c =~ ^(O[A-Za-z0-9]*)p([0-9]+)$ ]]; then c=${BASH_REMATCH[1]}; p=${BASH_REMATCH[2]}; fi
    cell_switches "$c" || return 2
    BUILD=build; CHUNK=512; INFL=1
    case $c in
        G0|GA1|G1F|GKM) METHOD=gpu_original ;;  GS) METHOD=gpu_original; CHUNK=2048 ;;  G1) METHOD=gpu_ffn_all; BUILD=build-gpuffn ;;
        H*) METHOD=heteromosaic; INFL=2; CFG=$CFGDIR/hm_$L.json
            case $c in
                HS|HS0|HS1) CFG=$CFGDIR/hs.json; INFL="" ;;  HR) CFG=$CFGDIR/hr.json ;;
                HK*) CFG=$CFGDIR/hm_$L.shipped.json; INFL=1 ;;   # kab1: the author's per-length entry (1024: 256/256/0) at 1 in flight
                HP0) CFG=$CFGDIR/hm1o_$L.json; INFL=1 ;;  HP*) CFG=$CFGDIR/hm1_$L.json; INFL=1 ;;  HT*) CFG=$CFGDIR/hm_$L.shipped.json ;;  HB*) CFG=$CFGDIR/hb_$L.json ;;
            esac ;;
        O*) METHOD=merged_ffn; INFL=2 ;;
    esac
    [ -n "$infl" ] && INFL=$infl
    [ -n "$cfgo" ] && CFG=$CFGDIR/$cfgo
    case $c in GA1|G1F|HA1|HA2|OA1|OA2|HLs|HLg|H1nU|OLs|OLg|O1nU|OK1) GRP=K ;; HR|GS|HS|HS0|HS1|O1F|O1FnU|HP*|HT*|HB*) GRP=P ;; esac
    case $STAGE in sweep*|gates) GRP=P ;; kab1*) GRP=K ;; esac
    [ -z "$CFG" ] || [ -s "$CFG" ] || { echo "missing config $CFG for $STAGE/$cell $L (run the probe/pick stage first)"; return 2; }
    D=$SD/$(plabel "$cell" "$L" "$k" "$reps" "$@")
    rm -rf "$D"; mkdir -p "$D"
    { echo "stage=$STAGE"; echo "cell=$cell"; echo "base=$c"; echo "tag=$tag"; echo "L=$L"; echo "k=$k"; echo "reps=$reps"; echo "new_tokens=$nt"
      echo "p=$p"; echo "group=$GRP"; echo "method=$METHOD"; echo "build=$BUILD"; echo "chunk=$CHUNK"; echo "inflight=$INFL"
      echo "config=${CFG##*/}"; echo "switches=$SW ${envs[*]:-}"; echo "src=$T"; echo "want=$want"; echo "cfgdir=$CFGDIR"; } > "$D/case.txt"
    local args=(--model "$MODEL" --build "$BUILD" --out "$D" --ref "$REF" --gpu-chunk-size "$CHUNK" --prompt-tokens "$L" --rounds 1
                --reps "$reps" --new-tokens "$nt" --methods "$METHOD")
    [ -n "$INFL" ] && args+=(--inflight "$INFL")
    [ -n "$CFG" ] && args+=(--config "$CFG")
    [ "$METHOD" = merged_ffn ] && args+=(--merged-ffn-config "$T/deployment-results/deployment-p$p.json")
    (   exec 9> "$LOCK"; flock 9
        cd "$T" || exit 2; export HETEROMOSAIC_ROOT="$T"
        clear_switches
        local pair; for pair in $SW "${envs[@]:-}"; do [ -n "$pair" ] && export "${pair//@D/$D}"; done
        env | grep '^HETEROMEGA_' | sort > "$D/env.txt"
        export PYTHONPATH="$T/$BUILD/py:$T/$BUILD/py/unified_llm_w4a16:$T"
        snap > "$D/temp_before.txt"
        gtt=$(ls /sys/class/drm/card*/device/mem_info_gtt_used | head -1)
        ( while :; do echo "$(($(cat "$gtt") / 1048576))"; sleep 0.5; done ) > "$D/gtt.txt" & sampler=$!
        LD_PRELOAD=$T/deployment-results/count_ioctls.so timeout -k 30 1800 python3 kernels/gpu/tools/evaluate_prefill.py "${args[@]}"
        rc=$?; kill $sampler 2>/dev/null; snap > "$D/temp_after.txt"; exit $rc
    ) > "$D/run.log" 2>&1 < /dev/null
    local rc=$? peak ioctl fb sel verdict seen
    peak=$(sort -n "$D/gtt.txt" | tail -1)
    ioctl=$(grep -h IOCTL_COUNTS "$D"/*.log | awk '{split($3,a,"="); if (a[2]+0 >= m) {m=a[2]+0; l=$0}} END{print l}')
    fb=$(cat "$D"/*.log | grep -c UNCACHED_FALLBACK)
    sel=$(grep -h 'Using grouped kernels_gemm_chunked' "$D"/*.result.log 2>/dev/null | head -1)
    seen=$(inflight_seen "$D")
    verdict=$(awk -F, 'NR==2{print $18}' "$D/summary.csv" 2>/dev/null)
    { echo "commit=$(git -C "$T" rev-parse HEAD)"; echo "build_dir=$T/$BUILD"; echo "peak_gtt_mib=$peak"
      echo "temp_sclk_before=$(cat "$D/temp_before.txt")"; echo "temp_sclk_after=$(cat "$D/temp_after.txt" 2>/dev/null)"
      echo "ioctl=$ioctl"; echo "uncached_fallback=$fb"; echo "hetero_gpu_gemm=$(grep -h HETERO_GPU_GEMM "$D"/*.log | tail -2 | tr '\n' '|')"
      echo "merged_ffn_verdict=$verdict"; echo "selection=$sel"; echo "inflight_seen=$seen"
      echo "chunk_schedule=$(grep -h 'Prefill chunk schedule' "$D"/*.result.log 2>/dev/null | head -1)"; } > "$D/info.txt"
    if [ "$rc" -ne 0 ] || [ ! -s "$D/summary.csv" ]; then
        grep -hiE 'out of memory|bad_alloc|hipError|Traceback|Error' "$D"/*.log | sort | uniq -c | sort -rn | head -5 | cut -c1-220 > "$D/error.txt"
        echo "$(date -u +%H:%M:%S) $STAGE/$cell $L s$k FAILED rc=$rc peakGTT=$peak"; cat "$D/error.txt"
        if grep -qiE 'out of memory|bad_alloc|hipErrorOutOfMemory' "$D"/*.log; then touch "$D/FAILED"; return 1; fi
        return 2
    fi
    [ -z "$INFL" ] || [ "$seen" = "$INFL" ] || echo "BAD_INFLIGHT: case says $INFL, log says '$seen'" | tee "$D/BAD_INFLIGHT"
    case $c in H0|HA1|HA2|H1|H1i1|H1nU|HLs|HLg|HP*|HT*|HB*|HK*)   # the config must select the 512-row group of this length (guards a wrong table group)
        local ok=0 sch
        if [[ $sel =~ chunk_size=([0-9]+),\ chunk_schedule=\[([^]]*)\],\ inflight=([0-9]+),\ prompt_len=([0-9]+) ]]; then
            sch=${BASH_REMATCH[2]//512/}; sch=${sch//[, ]/}
            [ "${BASH_REMATCH[1]}" = 512 ] && [ -z "$sch" ] && [ "${BASH_REMATCH[3]}" = "$INFL" ] && [ "${BASH_REMATCH[4]}" = "$L" ] && ok=1
        fi
        [ $ok = 1 ] || { echo "BAD_SELECTION: $sel" | tee "$D/BAD_SELECTION"; } ;;
    esac
    if [ -n "$src" ] && ! python3 "$JOBS/rk_check.py" "$D" > "$D/check.txt" 2>&1; then   # cell gate: not DONE, the stage goes on
        echo "$(date -u +%H:%M:%S) $STAGE/$cell $L s$k BAD_CONFIG: $(head -c 600 "$D/check.txt" | tr '\n' ';')" | tee "$D/BAD_CONFIG"; return 2
    fi
    echo "$(date -u +%H:%M:%S) $STAGE/$cell $L s$k median,min,max $(tail -1 "$D/summary.csv" | cut -d, -f5,6,7 | cut -c1-34) peakGTT=$peak fb=$fb"
    touch "$D/DONE"; return 0
}

run_proc() { # CELL L K REPS opts: skip when DONE; on a recorded OOM run the labelled -U/-F fallback
    local D rc fb
    D=$SD/$(plabel "$@")
    [ -e "$D/DONE" ] && return 0
    if [ ! -e "$D/FAILED" ] || [ -n "${RETRY_FAILED:-}" ]; then
        past_deadline && { echo "deadline $STOP reached before $D"; exit 75; }
        attempt "$@"; rc=$?
        [ $rc = 2 ] && { status=1; return; }
        [ $rc = 0 ] && return 0
    fi
    local c=$1 p=""; shift
    if [[ $c =~ ^(O[A-Za-z0-9]*)p([0-9]+)$ ]]; then c=${BASH_REMATCH[1]}; p=p${BASH_REMATCH[2]}; fi
    fb=$(fallback_of "$c")
    if [ -n "$fb" ]; then echo "OOM: $D, fallback $fb$p"; run_proc "$fb$p" "$@"; else status=1; fi
}

stage_header() {
    mkdir -p "$SD"
    { echo "commit $(git -C "$SRC" rev-parse HEAD) SRC=$SRC"; cat "$JOBS/trees.txt" 2>/dev/null; date -u; echo "NOU=${NOU:-}"; snap
      command -v xrt-smi > /dev/null && timeout 20 xrt-smi examine -r platform 2>&1 | head -20; } >> "$SD/stage.log" 2>&1
}

cmake_build() { # DIR [extra cmake flags]: as jobs/build.sh and jobs/build_gpuffn.sh, on $SRC
    local dir=$1; shift
    cmake -S . -B "$dir" -DROCM_PATH="$ROCM_PATH" -DCMAKE_HIP_COMPILER="$ROCM_PATH/lib/llvm/bin/clang++" -DCMAKE_HIP_ARCHITECTURES=gfx1150 \
      -DCMAKE_PREFIX_PATH="$ROCM_PATH" -DPython_EXECUTABLE="$(command -v python)" -Dpybind11_DIR="$(python -m pybind11 --cmakedir)" \
      -DCMAKE_CXX_FLAGS="-isystem $ROCM_PATH/include" -DCMAKE_HIP_FLAGS="-isystem $ROCM_PATH/include --hip-path=$ROCM_PATH --rocm-path=$ROCM_PATH" \
      -DCMAKE_EXE_LINKER_FLAGS="-L$ROCM_PATH/lib -Wl,-rpath,$ROCM_PATH/lib" -DCMAKE_SHARED_LINKER_FLAGS="-L$ROCM_PATH/lib -Wl,-rpath,$ROCM_PATH/lib" \
      -DCMAKE_MODULE_LINKER_FLAGS="-L$ROCM_PATH/lib -Wl,-rpath,$ROCM_PATH/lib" -DHETEROMEGA_MERGED_FFN=ON "$@" \
      -DHETEROMEGA_TORCH_COMPAT_HEADER="$PWD/docs/runs/2026-10-12-aup/torch211-hip-compat.hpp" 2>&1 | tail -2
    cmake --build "$dir" -j4 --target unified_llm_w4a16_hetero_libtorch 2>&1 | grep -E ' error|Built target unified' | tail -3
    ! readelf -d "$dir"/py/unified_llm_w4a16/*.so | grep -q 'libamdhip64.so.5' || { echo "error: $dir links HIP 5.7"; exit 1; }
}

case $STAGE in
    build)  # frozen checkout $SRC: `build` (MERGED_FFN) with the FFN deploy target, `build-gpuffn` (+GPU_FFN), the ioctl counter
        env_setup; clear_switches; mkdir -p deployment-results; echo "HEAD $(git rev-parse HEAD)"
        export MAX_JOBS=4
        cmake_build build; cmake --build build -j4 --target heteromega_ffn_deploy 2>&1 | grep -E ' error|Built target' | tail -3
        cmake_build build-gpuffn -DHETEROMEGA_GPU_FFN=ON
        gcc -shared -fPIC -O2 -I"$HOME_LIBS/xdna-driver-05-19-25/src/include/uapi/drm_local" -I/usr/include/libdrm \
            docs/runs/2026-10-31-ffn-deploy/deployment-results/count_ioctls.c -ldl -o deployment-results/count_ioctls.so && echo "built count_ioctls.so"
        touch "$RES/build.done"; exit 0 ;;
    compile)  # the 8 merged artifacts p=1024..8192 (CPU only, ~14 s each); an existing deployment-p<p>.json is kept
        env_setup; clear_switches; export PYTHONPATH="$PWD/build/py:$PWD/build/py/unified_llm_w4a16:$PWD"; mkdir -p "$SD"
        for p in 1024 2048 3072 4096 5120 6144 7168 8192; do
            if [ -s "deployment-results/deployment-p$p.json" ]; then echo "p$p exists"; continue; fi
            past_deadline && { echo "deadline"; exit 75; }
            python -m experiments.ffn_deploy.prepare --build --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
                --artifact-dir "$PWD/deployment-results/artifact-p$p" --m 512 --hidden 4096 --intermediate 14336 --npu-channels "$p" \
                --output "$PWD/deployment-results/deployment-p$p.json" > "$SD/p$p.log" 2>&1 || { echo "p$p FAILED"; status=1; }
        done
        exit $status ;;
esac

[ "$STAGE" = hprobe-1024 ] && { mkdir -p "$CFGDIR"; [ -s "$CFGDIR/hp_g0u0d512.json" ] || python3 "$JOBS/hm_ratio.py" "$CFGDIR" probe; }
[ "$MODE" = --list ] && { emit; exit $?; }   # print the unshuffled process list, run nothing
env_setup
case $STAGE in   # config files a stage needs, written before its schedule is made
    hprobe1-*) python3 "$JOBS/hm_ratio.py" "$CFGDIR" probe1 "$LEN" ;;
    hbcheck-*) python3 "$JOBS/hm_ratio.py" "$CFGDIR" hbprobe "$LEN" ;;
    main2-1024) [ -s "$CFGDIR/hb_1024.json" ] || python3 "$JOBS/hm_ratio.py" "$CFGDIR" hbprobe 1024 ;;
    pmb1-*) python3 "$JOBS/hm_ratio.py" "$CFGDIR" pmb_mid "$LEN" ;;
    r1u-*) python3 "$JOBS/hm_ratio.py" "$CFGDIR" r1u "$LEN" ;;
    pmb2-*) [ -s "$SD/schedule.txt" ] || python3 "$JOBS/hm_ratio.py" "$CFGDIR" pmb_ends "$LEN" $([ "$LEN" = 1024 ] || echo "$RES/pmb1-$LEN") | tee "$SD.ends.txt" ;;
    pmbc-*) [ -s "$SD/schedule.txt" ] || python3 "$JOBS/hm_ratio.py" "$CFGDIR" pmb_top "$LEN" "$RES/pmb1-$LEN" "$RES/pmb2-$LEN" | tee "$SD.top.txt" ;;
esac
ours_pm() { local f; for f in "$CFGDIR"/pm_*_"$1".json; do [[ $f == *.ours.json ]] || python3 "$HMB" config "$f" "${f%.json}.ours.json" > /dev/null || exit 2; done; }
case $STAGE in rk[1-4]-*|rk[1-4]s-*|apmb*)   # 11-16 stages: rk configs (also the AFTER author entry of apmbc)
    python3 "$JOBS/make_rk_configs.py" "$CFGDIR" "$HMB" > "$CFGDIR/rk_summary.txt" || { echo "make_rk_configs failed"; exit 2; } ;; esac
case $STAGE in   # pm_*.ours.json = pm configs with our binaries (hm_bins.py config)
    apmb1-*|apmbs-*) python3 "$JOBS/hm_ratio.py" "$CFGDIR" pmb_mid "$LEN" && python3 "$JOBS/hm_ratio.py" "$CFGDIR" pats "$LEN" "$(printf "B%.0s" $(seq $((LEN / 512))))" && ours_pm "$LEN" ;;
    apmb2-*) [ -s "$SD/schedule.txt" ] || { python3 "$JOBS/hm_ratio.py" "$CFGDIR" pmb_ends "$LEN" "$RES/apmb1-$LEN" | tee "$SD.ends.txt"; ours_pm "$LEN"; } ;;
    apmbc-*) [ -s "$SD/schedule.txt" ] || { python3 "$JOBS/hm_ratio.py" "$CFGDIR" pmb_top "$LEN" "$RES/apmb1-$LEN" "$RES/apmb2-$LEN" | tee "$SD.top.txt"; ours_pm "$LEN"; } ;;
esac
dry_line() { # CELL L K REPS opts: one line of the effective config (no run)
    local c=$1 L=$2 reps=$4 o src="" cfg="" want="" infl="" tag="" b eff="-"; shift 4
    for o in "$@"; do case $o in src=*) src=${o#src=} ;; cfg=*) cfg=${o#cfg=} ;; want=*) want=${o#want=} ;; infl=*) infl=${o#infl=} ;; tag=*) tag=${o#tag=} ;; esac; done
    b=$c; [[ $b =~ ^(O[A-Za-z0-9]*)p[0-9]+$ ]] && b=${BASH_REMATCH[1]}
    cell_switches "$b" > /dev/null
    [ -n "$cfg" ] && eff=$(python3 "$JOBS/rk_check.py" dry "$CFGDIR/$cfg" "/notebooks/hm-$src" "$L" ${want:+"$CFGDIR/$want"} 2>&1)
    echo "$c${tag:+.$tag} L=$L reps=$reps tree=hm-$src switches=[$(echo $SW | sed 's/HETEROMEGA_//g')] --inflight=${infl:-none} config=${cfg:--} :: $eff"
}
[ "$MODE" = --dry ] && { emit | while read -r line; do dry_line $line; done | sort | uniq -c; exit 0; }
sched=$SD/schedule.txt
if [ ! -s "$sched" ]; then   # generated once; a resume reuses it
    emit > "$SD.list" || exit 2
    mkdir -p "$SD"; SEED=${SEED:-$RANDOM$RANDOM}
    { echo "# seed=$SEED $(date -u)"; awk -v s="$SEED" 'BEGIN{srand(s)}{printf "%.9f\t%s\n", rand(), $0}' "$SD.list" | sort -n | cut -f2-; } > "$sched.tmp" && mv "$sched.tmp" "$sched"
fi
if [ "$MODE" = --remaining ]; then
    while read -r line; do [[ $line == \#* ]] && continue; set -- $line; [ -e "$SD/$(plabel "$@")/DONE" ] || [ -e "$SD/$(plabel "$@")/FAILED" ] || echo "$STAGE: $line"; done < "$sched"
    exit 0
fi
stage_header
while read -r line; do
    [[ $line == \#* ]] && continue
    run_proc $line
done < "$sched"
case $STAGE in
    sweep-*|sweep-rest) python3 "$JOBS/aggregate.py" "$RES" --write-best-p ;;
    hprobe-1024) python3 "$JOBS/hm_ratio.py" "$CFGDIR" pick "$SD" | tee "$SD/pick.txt" ;;
    sweep1-*|sweep1lo-*) python3 "$JOBS/aggregate.py" "$RES" --write-best-p --inflight 1 ;;   # -> best_p1.txt only
    hprobe1-1024) python3 "$JOBS/hm_ratio.py" "$CFGDIR" rank1 1024 "$SD" | tee "$SD/rank1.txt" ;;      # screen -> hm_rank1.txt; hprobe1b-1024 follows
    hprobe1b-1024) python3 "$JOBS/hm_ratio.py" "$CFGDIR" pick1 1024 "$RES/hprobe1-1024" "$SD" | tee "$SD/pick1.txt" ;;
    hprobe1-*) python3 "$JOBS/hm_ratio.py" "$CFGDIR" pick1 "$LEN" "$SD" | tee "$SD/pick1.txt" ;;
    hbcheck-*) python3 "$JOBS/hm_ratio.py" "$CFGDIR" hbpick "$LEN" "$SD" | tee "$SD/hbpick.txt" ;;
    uprobe1) n=0; ok=yes   # HP1 + UNCACHED fits at 1024 and 4096 (both DONE, no UNCACHED_FALLBACK) -> HP1 uses it from now on
        for D in "$SD"/HP1U-*; do n=$((n + 1)); { [ -e "$D/DONE" ] && grep -qx 'uncached_fallback=0' "$D/info.txt"; } || ok=no; done
        [ $n = 2 ] || ok=no; echo $ok > "$RES/hp1_u.txt"; echo "hp1_u=$ok" ;;
esac
echo "stage $STAGE done status=$status"
exit $status
