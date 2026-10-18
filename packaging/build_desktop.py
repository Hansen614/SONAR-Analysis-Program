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
DIST = ROOT / os.environ.get('SAP_DIST_DIR', 'desktop-dist')
sys.path.insert(0, str(ROOT))
from sonar_app import __version__
from sonar_app.backend import Platform, sha


def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True, timeout=1200)


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
    run(sys.executable, 'packaging/collect_notices.py')
    run(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--distpath', DIST,
        '--workpath', '_work/desktop-build', 'packaging/SAP.spec')
    out = DIST
    binary = out / ('SAP.app/Contents/MacOS/SAP' if sys.platform == 'darwin' else 'SAP/SAP.exe')
    report = ROOT / '_work/frozen-self-test'
    run(binary, '--self-test', report)
    result = json.loads((report / 'self-test.json').read_text())
    assert result['status'] == 'PASS' and result['frozen']
    gui_result = None
    if sys.platform in ('win32', 'darwin'):
        gui_report = ROOT / '_work/frozen-gui-test'
        run(binary, '--ui-self-test', gui_report)
        gui_result = json.loads((gui_report / 'gui-self-test.json').read_text())
        assert gui_result['status'] == 'PASS' and gui_result['frozen']
    forbidden = [f for f in out.rglob('*') if f.is_file() and any(x in f.name.lower() for x in ('libheif', 'libde265', 'libx265', '_pillow_heif'))]
    # Inspect only the current application, not archived candidates from another build.
    app_root = out / ('SAP.app' if sys.platform == 'darwin' else 'SAP')
    forbidden = [f for f in forbidden if f.is_relative_to(app_root)]
    if forbidden: raise RuntimeError('Unused HEIC libraries were unexpectedly bundled')
    machine = platform.machine().lower()
    arch = 'arm64' if machine in ('arm64','aarch64') else 'x64'
    stem = f'SAP-{__version__}-{"macos" if sys.platform == "darwin" else "windows"}-{arch}'
    if sys.platform == 'darwin':
        stage = ROOT / '_work/dmg-stage'
        if stage.exists(): shutil.rmtree(stage)
        stage.mkdir()
        run('ditto', out / 'SAP.app', stage / 'SAP.app')
        (stage / 'Applications').symlink_to('/Applications')
        shutil.copyfile(ROOT / 'LICENSE', stage / 'LICENSE')
        shutil.copytree(ROOT / '_work/third-party-notices', stage / 'THIRD_PARTY_NOTICES')
        shutil.copyfile(ROOT / 'packaging/INSTALL.md', stage / 'INSTALL.md')
        artifact = out / (stem + '.dmg')
        run('hdiutil', 'create', '-volname', 'SAP', '-srcfolder', stage,
            '-ov', '-format', 'UDZO', artifact)
    else:
        shutil.copyfile(ROOT / 'packaging/INSTALL.md', out / 'SAP/INSTALL.md')
        shutil.copyfile(ROOT / 'LICENSE', out / 'SAP/LICENSE')
        shutil.copytree(ROOT / '_work/third-party-notices', out / 'SAP/THIRD_PARTY_NOTICES', dirs_exist_ok=True)
        artifact = Path(shutil.make_archive(str(out / (stem + '-portable')), 'zip', out, 'SAP'))
    manifest = {'app_version': __version__, 'platform': sys.platform, 'architecture': arch,
                'python': sys.version, 'pyinstaller': importlib.metadata.version('pyinstaller'),
                'pywebview': importlib.metadata.version('pywebview'),
                'scientific_manifest_sha256': sha(ROOT / 'scientific_reference/RELEASE_MANIFEST.json'),
                'artifact': artifact.name, 'artifact_sha256': sha(artifact),
                'self_test': result, 'gui_self_test': gui_result, 'public_release_ready': False, 'release_channel': 'prerelease',
                'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'excluded_unused_heic_binaries': True,
                'signing': ('Ad-hoc signed; not Developer ID signed or notarized' if sys.platform == 'darwin' else 'Unsigned Windows candidate'),
                'sources': {str(f.relative_to(ROOT)):sha(f) for f in (ROOT/'sonar_app').rglob('*')
                    if f.is_file() and '__pycache__' not in f.parts and f.name != '.DS_Store'}}
    (out / 'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (out / 'SHA256SUMS.txt').write_text(f'{sha(artifact)}  {artifact.name}\n',encoding='utf-8')
    print(artifact)

if __name__ == '__main__': main()
