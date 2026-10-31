import hashlib
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from .prepare import main, package


class PackageTests(unittest.TestCase):
    def fixture(self, root, instructions=b'\x01\x00\x00\x00'):
        artifact = root / 'artifact'
        artifact.mkdir()
        manifest = dict(kind='w4a16_upstream_merged', mode='merged')
        for name, field, data in (('final.xclbin', 'xclbin_sha256', b'test fixture, not a real XCLBIN'),
                                  ('insts.bin', 'insts_sha256', instructions)):
            (artifact / name).write_bytes(data)
            manifest[field] = hashlib.sha256(data).hexdigest()
        (artifact / 'final.xclbin.json').write_text(json.dumps(manifest))
        return artifact

    def test_package_checks_hashes_and_does_not_modify_binaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = self.fixture(root)
            before = {p.name: p.read_bytes() for p in artifact.iterdir()}
            result = package(artifact, root / 'deploy.json')
            self.assertEqual(result['artifact_dir'], str(artifact.resolve()))
            self.assertEqual(result['accuracy_policy'], 'report')
            self.assertEqual(before, {p.name: p.read_bytes() for p in artifact.iterdir()})

    def test_tampered_artifact_is_rejected_before_config_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = self.fixture(root)
            (artifact / 'insts.bin').write_bytes(b'changed!')
            with self.assertRaisesRegex(ValueError, 'mismatched'):
                package(artifact, root / 'deploy.json')
            self.assertFalse((root / 'deploy.json').exists())

    def test_unaligned_instructions_rejected_even_with_matching_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = self.fixture(root, b'123')
            with self.assertRaisesRegex(ValueError, 'whole uint32'):
                package(artifact, root / 'deploy.json')

    def test_wrong_graph_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); artifact = self.fixture(root)
            path = artifact / 'final.xclbin.json'
            manifest = json.loads(path.read_text()); manifest['kind'] = 'w4a16_upstream_merged_gate_up'
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'complete merged'):
                package(artifact, root / 'deploy.json')

    def test_build_keeps_the_supplied_virtualenv_python_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = self.fixture(root)
            target = root / 'system-python'
            target.write_text('fixture; compiler invocation is mocked')
            alias = root / 'venv-python'
            try:
                os.symlink(target, alias)
            except OSError as exc:
                self.skipTest(f'symlinks unavailable: {exc}')
            argv = ['prepare', '--build', '--iron-python', str(alias),
                    '--artifact-dir', str(artifact), '--output', str(root / 'deploy.json')]
            with patch.object(sys, 'argv', argv), patch('subprocess.run') as compile_call:
                with contextlib.redirect_stdout(io.StringIO()):
                    main()
            executable = compile_call.call_args.args[0][0]
            self.assertEqual(executable, str(alias.absolute()))
            self.assertNotEqual(executable, str(target.resolve()))


if __name__ == '__main__':
    unittest.main()
