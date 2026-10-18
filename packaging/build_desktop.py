"""Build on the target OS using an isolated Python 3.13 environment."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sonar_app import __version__
from sonar_app.backend import Platform, sha


def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def main():
    if sys.prefix == sys.base_prefix:
        raise SystemExit('Build inside an isolated virtual environment.')
    cfg = Path(sys.prefix, 'pyvenv.cfg').read_text().lower()
    if 'include-system-site-packages = true' in cfg:
        raise SystemExit('System site packages must be disabled.')
    if sys.platform not in ('darwin', 'win32'):
        raise SystemExit('Supported build hosts: macOS and Windows.')
    os.environ['PYINSTALLER_CONFIG_DIR'] = str(ROOT / '_work/pyinstaller-cache')
    work = ROOT / '_work/desktop-build-check'
    p = Platform(workspace=work)
    p.verify_release()
    assert all(x['matches'] for x in p.dependency_status())
    run(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--distpath', 'desktop-dist',
        '--workpath', '_work/desktop-build', 'packaging/SAP.spec')
    out = ROOT / 'desktop-dist'
    binary = out / ('SAP.app/Contents/MacOS/SAP' if sys.platform == 'darwin' else 'SAP/SAP.exe')
    report = ROOT / '_work/frozen-self-test'
    run(binary, '--self-test', report)
    result = json.loads((report / 'self-test.json').read_text())
    assert result['status'] == 'PASS' and result['frozen']
    machine = platform.machine().lower()
    arch = 'arm64' if machine in ('arm64','aarch64') else 'x64'
    stem = f'SAP-{__version__}-{"macos" if sys.platform == "darwin" else "windows"}-{arch}'
    if sys.platform == 'darwin':
        stage = ROOT / '_work/dmg-stage'
        if stage.exists(): shutil.rmtree(stage)
        stage.mkdir()
        run('ditto', out / 'SAP.app', stage / 'SAP.app')
        (stage / 'Applications').symlink_to('/Applications')
        shutil.copyfile(ROOT / 'packaging/INSTALL.md', stage / 'INSTALL.md')
        artifact = out / (stem + '.dmg')
        run('hdiutil', 'create', '-volname', 'SAP', '-srcfolder', stage,
            '-ov', '-format', 'UDZO', artifact)
    else:
        shutil.copyfile(ROOT / 'packaging/INSTALL.md', out / 'SAP/INSTALL.md')
        artifact = Path(shutil.make_archive(str(out / (stem + '-portable')), 'zip', out, 'SAP'))
    manifest = {'app_version': __version__, 'platform': sys.platform, 'architecture': arch,
                'python': sys.version, 'pyinstaller': importlib.metadata.version('pyinstaller'),
                'pywebview': importlib.metadata.version('pywebview'),
                'scientific_manifest_sha256': sha(ROOT / 'scientific_reference/RELEASE_MANIFEST.json'),
                'artifact': artifact.name, 'artifact_sha256': sha(artifact),
                'self_test': result, 'public_release_ready': False,
                'signing': ('Ad-hoc signed; not Developer ID signed or notarized' if sys.platform == 'darwin' else 'Unsigned Windows candidate'),
                'sources': {str(f.relative_to(ROOT)):sha(f) for f in (ROOT/'sonar_app').rglob('*')
                    if f.is_file() and '__pycache__' not in f.parts}}
    (out / 'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (out / 'SHA256SUMS.txt').write_text(f'{sha(artifact)}  {artifact.name}\n',encoding='utf-8')
    print(artifact)

if __name__ == '__main__': main()
