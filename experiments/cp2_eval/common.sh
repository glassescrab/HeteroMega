# Shared by eval3.sh and quality.sh (source it). One frozen checkout SRC; results under RES; everything GPU/NPU runs under gpu.lock.
SRC=${SRC:-/notebooks/hm-cp2b}   # v4: hm-cp2 + p<=13312 patch (v3 results used /notebooks/hm-cp2)
JOBS=/notebooks/hm-jobs/cp2
RES=${RES:-/notebooks/hm-results/cp2}
LOCK=${LOCK:-/notebooks/hm-jobs/gpu.lock}
MODEL=/notebooks/hm-model/Meta-Llama-3.1-8B-Instruct-AWQ-INT4
PROMPTS=${PROMPTS:-/notebooks/hm-jobs/prompts}
REF=$PROMPTS/sampled-4160.json
CFGDIR=$RES/configs
COUNT=$SRC/deployment-results/count_ioctls.so
STOP=${STOP_LONG_AFTER_UTC:-2026-11-15T19:30Z}   # no new process starts after this (resume later or read remaining.txt)
GEN="HETEROMEGA_GEMM=fast HETEROMEGA_SDPA=fast"; SD="HETEROMEGA_SDPA=fast"; GM="HETEROMEGA_GEMM=fast"
U="HETEROMEGA_GEMM_UNCACHED=1"; FU="HETEROMEGA_FFN_FUSE=1"; RN="HETEROMEGA_RESIDUAL_NORM=1"; SB="HETEROMEGA_FFN_SLOT_BO=2"

env_setup() {
    cd "$SRC" || exit 2
    source /notebooks/heteromosaic-venv/bin/activate
    unset HSA_OVERRIDE_GFX_VERSION PYTHONPATH
    export HOME_LIBS=/notebooks/hm-libs HETEROMOSAIC_ROOT="$PWD" ROCM_PATH=/opt/rocm-7.2.0
    export LD_LIBRARY_PATH="$ROCM_PATH/lib:/opt/xilinx/xrt/lib:${LD_LIBRARY_PATH:-}"
    export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
    mkdir -p "$RES" "$CFGDIR"
    [ -s "$CFGDIR/hm_4096.json" ] || python3 "$JOBS/make_hm_configs.py" "$SRC/py/unified_llm_w4a16/configs/configs_strixP_llama3_8b.json5" "$CFGDIR" > "$CFGDIR/summary.txt" || { echo "make_hm_configs failed"; exit 2; }
}

# Every HETEROMEGA_* variable of the shell is dropped before a case sets its own: no switch leaks between methods.
clear_switches() { local v; for v in $(compgen -e | grep '^HETEROMEGA_'); do unset "$v"; done; export HETEROMEGA_FFN_FINITE_CHECK=sampled; }

past_deadline() { [ -n "$STOP" ] && [[ $(date -u +%Y-%m-%dT%H:%MZ) > $STOP ]]; }

bestp() { # LENGTH on|off: env P_ON_<L> / P_OFF_<L> (manual override) first, then $BESTP_FILE (default best_p.txt = the v3 2-in-flight sweep; v4 stages set best_p1.txt)
    local up; up=$(echo "$2" | tr a-z A-Z); local var=P_${up}_$1
    if [ -n "${!var:-}" ]; then echo "${!var}"; else awk -v L="$1" -v S="$2" '$1==L && $2==S {p=$3} END{print p}' "$RES/${BESTP_FILE:-best_p.txt}" 2>/dev/null; fi
}

hp1_uses_u() { grep -qx yes "$RES/hp1_u.txt" 2>/dev/null; }   # written by stage uprobe1: HP1 + UNCACHED fits at 1024 and 4096 (plan v4 section 10.4)

snap() { rocm-smi --showtemp --showclocks 2>/dev/null | grep -E 'Sensor|sclk' | tr -s ' ' | tr '\n' ';'; echo; }

# Switch set of a cell (ours/GPU/HeteroMosaic ladder rungs, see eval_plan_v3; v4 cells see eval_plan_v4 section 1); sets SW.
# Cells: G0 GA1 G1F G1 GS | H0 HA1 HA2 H1 HLs HLg H1nU HS HR | O0 OA1 OA2 O1F O1 OLs OLg O1nU | v4: HP0 HP1 (best 1-in-flight config) HT0 HT1 (shipped token split)
#   HB0 HB1 (best token split) HS0 HS1 (shipped chunking) H1i1 HT1i1 (regime-2 configs run at 1 in flight) HP1U (HP1 + UNCACHED probe) OK1 (ours, comparable bundle) O1FnU
cell_switches() {
    case $1 in
        G0|GS|H0|HS|HS0|HR|O0|HP0|HT0|HB0) SW="" ;;
        GA1|HA1|OA1) SW=$SD ;;
        G1F|HA2) SW=$GEN ;;
        G1) SW="$GEN $FU" ;;
        H1|HT1|HB1|HS1|H1i1|HT1i1) SW=$GEN ;;  HLs) SW=$GM ;;  HLg) SW=$SD ;;  H1nU) SW=$GEN ;;   # H1 without UNCACHED: OOM at 1024/4096, thrashes at 2048 (port agent, 11-15)
        GKM) SW=$GM ;;  HK0) SW="" ;;  HKM) SW=$GM ;;  HK1) SW=$GEN ;;  HKU) SW="$GEN $U" ;;  HKUnU) SW=$GEN ;;  OKM) SW="$GM $RN" ;;   # kab1 ladder rungs (11-15)
        HP1) SW=$GEN; hp1_uses_u && SW="$GEN $U" ;;  HP1U) SW="$GEN $U" ;;  HP1nU) SW=$GEN ;;   # HP1nU: labelled OOM fallback of HP1 (11-15, 4096)
        OA2) SW="$GEN $RN" ;;  O1F) SW="$GEN $U $RN" ;;  O1) SW="$GEN $U $FU $RN" ;;  OK1) SW="$GEN $RN" ;;   # ours with its internal fixes (RESIDUAL_NORM, SLOT_BO), no UNCACHED, no fusion; ladder OK1 -> O1F (+U) -> O1 (+FU)
        OLs) SW="$GM $U $FU $RN" ;;  OLg) SW="$SD $U" ;;  O1nU) SW="$GEN $FU $RN" ;;  O1FnU) SW="$GEN $RN" ;;
        *) echo "unknown cell $1"; return 1 ;;
    esac
    case $1 in O0|OA1|OLg|OA2|O1F|O1|OK1|OKM|OLs|O1nU|O1FnU) SW="$SW $SB" ;; esac   # SLOT_BO always on for ours
}
fallback_of() { case $1 in O1) echo O1nU ;; O1F) echo O1FnU ;; H1) echo H1nU ;; HP1) echo HP1nU ;; HKU) echo HKUnU ;; G1) echo G1F ;; esac; }   # OOM fallbacks, labelled
