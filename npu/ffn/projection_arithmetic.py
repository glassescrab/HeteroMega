"""CPU-only source and cache identity for W4A16 projection arithmetic.

Both choices preserve the compact BF16/W4/FP32 external kernel ABI. BFP16
changes the internal matrix multiply, not the activation or weight format.
The upstream kernel revision is independent of the graph compiler revision.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path


ARITHMETIC_CHOICES = ('bf16', 'bfp16')
UPSTREAM_KERNEL_COMMIT = '121dd54abc68f84d89a7074372ebf82be2db62d5'
ARITHMETIC_SOURCE_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


@dataclass(frozen=True)
class ProjectionArithmetic:
    arithmetic: str
    source_path: Path
    source: str
    source_sha256: str

    @property
    def stack_size(self):
        # TileFuse reserves 0xD00 for BFP16 conversion spills. Use a full
        # 4 KiB allocation here; leave the measured native BF16 stack intact.
        return 4096 if self.arithmetic == 'bfp16' else 2048

    def compile_flags(self, reuse):
        if reuse not in (1, 2, 4):
            raise ValueError('M reuse must be 1, 2 or 4')
        # Specify both modes before the AIE headers are parsed. Native BF16
        # must not inherit a toolchain-wide BFP16 emulation default.
        emulation = 1 if self.arithmetic == 'bfp16' else 0
        return [f'-DHETEROMEGA_M_REUSE={reuse}',
                f'-DAIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16={emulation}']

    def object_name(self, reuse):
        self.compile_flags(reuse)  # Validate before creating a cache identity.
        return (f'w4a16_prefill_reuse_{self.arithmetic}_{self.source_sha256}_'
                f'{ARITHMETIC_SOURCE_SHA}_r{reuse}.o')

    def manifest_fields(self):
        return dict(arithmetic=self.arithmetic, compute_format=self.arithmetic,
                    worker_stack_size=self.stack_size,
                    arithmetic_source_sha256=ARITHMETIC_SOURCE_SHA,
                    upstream_kernel_commit=(UPSTREAM_KERNEL_COMMIT
                        if self.arithmetic == 'bfp16' else None))


def projection_arithmetic(arithmetic='bf16'):
    """Select only explicit modes; never silently substitute an arithmetic."""
    if arithmetic not in ARITHMETIC_CHOICES:
        raise ValueError(f'unknown projection arithmetic {arithmetic!r}; '
                         f'expected one of {ARITHMETIC_CHOICES}')
    filename = ('w4a16_prefill_reuse.cc' if arithmetic == 'bf16'
                else 'w4a16_prefill_bfp16.cc')
    path = Path(__file__).with_name(filename)
    source = path.read_text()
    return ProjectionArithmetic(arithmetic, path, source,
                                hashlib.sha256(source.encode()).hexdigest())


def validate_projection_identity(projection, source_sha256, arithmetic_source_sha256):
    if (source_sha256 != projection.source_sha256
            or arithmetic_source_sha256 != ARITHMETIC_SOURCE_SHA):
        raise ValueError('projection arithmetic source hash changed; rebuild the graph '
                         'with the selected source and arithmetic helper hashes')
