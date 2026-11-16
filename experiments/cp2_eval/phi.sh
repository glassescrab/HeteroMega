#!/usr/bin/env bash
# p > 8192 for ours (user request 2026-11-15): checkout hm-cp2b = hm-cp2 + bound patch, build, compile p = 9216..13312,
# bitwise check of p = 8192 against hm-cp2, then per new p: C++ smoke and last-token logits vs G0 (sampled-1, 1024 tokens).
# Every GPU/NPU or heavy CPU step holds gpu.lock, so no timed process of the running evaluation overlaps it.
set -uo pipefail
NEW=/notebooks/hm-cp2b; OLD=/notebooks/hm-cp2; W=/notebooks/hm-results/cp2/phi; mkdir -p "$W"
export SRC=$NEW RES=/notebooks/hm-results/cp2
source /notebooks/hm-jobs/cp2/common.sh
PS="9216 10240 11264 12288 13312"
lock() { ( exec 9> "$LOCK"; flock 9; "$@" ); }
if [ ! -d "$NEW/.git" ] && [ ! -f "$NEW/.git" ]; then
    git -C /notebooks/hm-main worktree add -q "$NEW" "$(git -C $OLD rev-parse HEAD)"
    git -C "$NEW" -c user.name=cp2 -c user.email=cp2@local am -q /notebooks/hm-cp2-patches/0001-CP2-allow-NPU-channels-p-up-to-13312-planner-prepare.patch
fi
echo "HEAD $(git -C $NEW log --oneline -1)"
mkdir -p "$NEW/deployment-results"
for p in 1024 2048 3072 4096 5120 6144 7168 8192; do
    ln -sfn "$OLD/deployment-results/artifact-p$p" "$NEW/deployment-results/artifact-p$p"
    cp -n "$OLD/deployment-results/deployment-p$p.json" "$NEW/deployment-results/"
done
[ -e "$W/build.done" ] || { lock env RES=$W bash /notebooks/hm-jobs/cp2/eval3.sh build > "$W/build.log" 2>&1 && touch "$W/build.done"; tail -4 "$W/build.log"; }
env_setup
export PYTHONPATH="$NEW/build/py:$NEW/build/py/unified_llm_w4a16:$NEW"
for p in $PS; do
    [ -s "$NEW/deployment-results/deployment-p$p.json" ] && continue
    lock python -m experiments.ffn_deploy.prepare --build --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
        --artifact-dir "$NEW/deployment-results/artifact-p$p" --m 512 --hidden 4096 --intermediate 14336 --npu-channels "$p" \
        --output "$NEW/deployment-results/deployment-p$p.json" > "$W/compile-p$p.log" 2>&1 && echo "compiled p$p" || echo "compile p$p FAILED"
done
# bitwise: p = 8192, O1 switches, as quality.sh bitwise; ref = the hm-cp2 run already in gate-bitwise
B=$W/bitwise; mkdir -p "$B"; cp -n "$RES/gate-bitwise/O1-1024-new.npz" "$B/O1-1024-ref.npz"
cell_switches O1
[ -s "$B/O1-1024-new.npz" ] || lock bash -c "cd $NEW; $(declare -f clear_switches); clear_switches; for x in $SW; do export \$x; done
    LD_PRELOAD=$OLD/deployment-results/count_ioctls.so timeout -k 30 900 python3 tools/npu_error_probe/path_logits.py --method merged_ffn --model $MODEL --build build \
    --merged-ffn-config $NEW/deployment-results/deployment-p8192.json --ref $REF --prompt-tokens 1024 --inflight 2 --ppl-tokens 64 --new-tokens 64 \
    --out $B/O1-1024-new.npz" > "$B/O1-new.log" 2>&1
python3 /notebooks/hm-jobs/cp2/bitwise_compare.py logits "$B" | tee "$B/compare.txt"
# per new p: smoke, then logits vs G0
Q=$W/logits; mkdir -p "$Q"; cp -n "$RES/quality-gate/seed1/gpu_original-1024-r0.npz" "$Q/"
for p in $PS; do
    [ -s "$NEW/deployment-results/deployment-p$p.json" ] || continue
    [ -s "$W/smoke-p$p.json" ] || { lock bash -c "cd $NEW; export HETEROMEGA_FFN_FINITE_CHECK=sampled; timeout -k 30 900 python -m experiments.ffn_deploy.smoke --config deployment-results/deployment-p$p.json --iterations 3 --output $W/smoke-p$p.json" > "$W/smoke-p$p.log" 2>&1; echo "smoke p$p rc=$? $(tail -1 $W/smoke-p$p.log | cut -c1-160)"; }
    [ -s "$Q/O1p$p-1024-r0.npz" ] || lock bash -c "cd $NEW; $(declare -f clear_switches); clear_switches; for x in $SW; do export \$x; done
        LD_PRELOAD=$OLD/deployment-results/count_ioctls.so timeout -k 30 900 python3 tools/npu_error_probe/path_logits.py --method merged_ffn --model $MODEL --build build \
        --merged-ffn-config $NEW/deployment-results/deployment-p$p.json --ref $PROMPTS/sampled-1.json --prompt-tokens 1024 --inflight 2 --no-score \
        --out $Q/O1p$p-1024-r0.npz" > "$Q/O1p$p.log" 2>&1 || echo "logits p$p FAILED: $(grep -hE 'Error|error' $Q/O1p$p.log | tail -1 | cut -c1-200)"
done
python3 tools/npu_error_probe/path_logits.py --compare "$Q" 2>&1 | tail -8 | tee "$Q/compare.txt"
echo done
