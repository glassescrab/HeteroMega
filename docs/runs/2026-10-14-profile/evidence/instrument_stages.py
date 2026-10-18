"""Temporary cloud-only trace scopes; restored after diagnostic measurements."""
from pathlib import Path

root = Path('/notebooks/HeteroMosaic-baseline')
out = Path('/notebooks/heteromega-profile-2026-10-14')
p = root / 'src/unified_llm_w4a16_hetero/unified_llm_w4a16.cpp'
s = p.read_text()
(out / 'model-before-profiling.cpp').write_text(s)
start = s.index('torch::Tensor UnifiedLLMW4A16Impl::forward_llama3_with_scratch(')
end = s.index('torch::Tensor UnifiedLLMW4A16Impl::forward_', start + 65)
body = s[start:end]

def replace_once(old, new):
    global body
    assert body.count(old) == 1, (old, body.count(old))
    body = body.replace(old, new, 1)

def begin(label):
    return (f'auto detail_{label} = begin_stage_trace(chunk_id, slot_id, i, "{label}", start_pos, seq_len);\n'
            f'        mark_stage_trace_started(detail_{label});\n        ')

def finish(label):
    return f'end_stage_trace(std::move(detail_{label}));\n        '

replace_once('attn_output = attn_output.transpose(1, 2).contiguous().view({bsz, seq_len, hidden_size_});',
             begin('O_projection') + 'attn_output = attn_output.transpose(1, 2).contiguous().view({bsz, seq_len, hidden_size_});')
replace_once('post_attn_norms[i]->forward_out(', finish('O_projection') + begin('FFN_norm') + 'post_attn_norms[i]->forward_out(')
replace_once('auto f_gate = gate_layers[i]->forward(', finish('FFN_norm') + begin('FFN_gate_up') + 'auto f_gate = gate_layers[i]->forward(')
replace_once('torch::silu_(gate_buf);', finish('FFN_gate_up') + begin('FFN_pointwise') + 'torch::silu_(gate_buf);')
replace_once('auto f_down = down_layers[i]->forward(', finish('FFN_pointwise') + begin('FFN_down') + 'auto f_down = down_layers[i]->forward(')
replace_once('end_stage_trace(std::move(g2_trace));', finish('FFN_down') + 'end_stage_trace(std::move(g2_trace));')
updated = s[:start] + body + s[end:]
needle = '<< "\\\"chunk_id\\\":" << row.chunk_id'
assert updated.count(needle) == 1
updated = updated.replace(needle,
    '<< "\\\"clock_origin_ns\\\":" << std::chrono::duration_cast<std::chrono::nanoseconds>(state.t0.time_since_epoch()).count() << "," '
    + needle)
p.write_text(updated)

np = root / 'src/unified_llm_w4a16_hetero/npuSetup.cpp'
ns = np.read_text()
(out / 'npu-before-profiling.cpp').write_text(ns)
start = ns.index('int npuMatmul_zero(')
end = ns.index('uint32_t import_dma_buf_to_xdna(', start)
part = ns[start:end]

def nreplace(old, new):
    global part
    assert part.count(old) == 1, (old, part.count(old))
    part = part.replace(old, new, 1)

nreplace('    struct amdxdna_drm_exec_cmd exec_cmd;', '''    const auto profile_now = []() -> long long {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
    };
    const long long profile_start = profile_now();
    struct amdxdna_drm_exec_cmd exec_cmd;''')
nreplace('    // Wait for input GPU buffers', '    const long long profile_created = profile_now();\n    // Wait for input GPU buffers')
nreplace('    std::lock_guard<std::mutex> lock(npu_mutex);', '''    const long long profile_ready = profile_now();
    std::lock_guard<std::mutex> lock(npu_mutex);
    const long long profile_locked = profile_now();''')
nreplace('    // Wait for the command to complete', '    const long long profile_submitted = profile_now();\n    // Wait for the command to complete')
nreplace('    // lock_guard destructor', '''    const long long profile_done = profile_now();
    static FILE *profile_file = []() -> FILE * {
        const char *path = std::getenv("HETEROMEGA_NPU_TRACE");
        return path ? fopen(path, "w") : nullptr;
    }();
    if (profile_file) {
        fprintf(profile_file, "%lld,%lld,%lld,%lld,%lld,%lld,%d,%d\\n",
                profile_start, profile_created, profile_ready, profile_locked,
                profile_submitted, profile_done, hwctx_numb, instctx_numb);
    }
    // lock_guard destructor''')
ns = '#include <chrono>\n#include <cstdlib>\n' + ns[:start] + part + ns[end:]
np.write_text(ns)
print('Installed diagnostic Llama scopes and NPU host phases; model math unchanged')

