# Run with the isolated desktop environment from the project root.
from pathlib import Path
import sys
import os
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

ROOT = Path(SPECPATH).parent
REFERENCE = ROOT / 'scientific_reference'
science_modules = [p.stem for p in (REFERENCE / 'src').glob('*.py')]
datas = [(str(ROOT / 'LICENSE'), '.'),
         (str(ROOT / '_work/third-party-notices'), 'THIRD_PARTY_NOTICES')]
# Only manifest-registered scientific files plus its manifest. No caches or user workspace.
import json
manifest = json.loads((REFERENCE / 'RELEASE_MANIFEST.json').read_text())
for relative in [r['path'] for r in manifest['files']] + ['RELEASE_MANIFEST.json']:
    path = REFERENCE / relative
    datas.append((str(path), str(Path('scientific_reference') / Path(relative).parent)))
datas += [(str(ROOT / 'sonar_app/static'), 'sonar_app/static'),
          (str(ROOT / 'sonar_app/english_messages.json'), 'sonar_app')]
for line in (REFERENCE / 'environment/requirements.lock.txt').read_text().splitlines():
    datas += copy_metadata(line.split('==')[0])
for name in ['pywebview', 'proxy_tools', 'bottle', 'typing_extensions']:
    datas += copy_metadata(name)
datas += collect_data_files('tzdata')
# Python files are executed from source, preserving __file__ identity and existing hashes.
collection_mode = {'sonar_app': 'py', **{name: 'py' for name in science_modules}}
hidden = ['science_api', 'core', 'reporter_calibration', 'inverse_calibration',
          'flowio', 'numpy', 'pandas', 'matplotlib.backends.backend_agg',
          'openpyxl', 'PIL.Image']
if sys.platform == 'win32':
    runtime = os.environ.get('SAP_WEBVIEW2_RUNTIME')
    if not runtime or not (Path(runtime) / 'msedgewebview2.exe').is_file():
        raise SystemExit('Set SAP_WEBVIEW2_RUNTIME to an extracted Microsoft WebView2 Fixed Runtime directory.')
    datas.append((runtime, 'WebView2'))
a = Analysis([str(ROOT / 'desktop_entry.py')], pathex=[str(ROOT), str(REFERENCE / 'src')],
    binaries=[], datas=datas, hiddenimports=hidden, hookspath=[], runtime_hooks=[],
    excludes=['PyQt5','PyQt6','PySide2','PySide6','tkinter','IPython','notebook','pillow_heif','_pillow_heif'],
    module_collection_mode=collection_mode)
pyz = PYZ(a.pure)
icon = str(ROOT / 'packaging/icons' / ('SAP.icns' if sys.platform == 'darwin' else 'SAP.ico'))
exe = EXE(pyz, a.scripts, [("X utf8", None, "OPTION")], exclude_binaries=True, name='SAP', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    icon=icon, codesign_identity=os.environ.get('SAP_CODESIGN_IDENTITY'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='SAP')
if sys.platform == 'darwin':
    app = BUNDLE(coll, name='SAP.app', icon=icon, bundle_identifier='org.sustech-igem.sap',
        info_plist={'CFBundleShortVersionString':'1.4.0', 'CFBundleVersion':'14001',
                    'LSMinimumSystemVersion':'14.0', 'NSHighResolutionCapable':True, 'NSHumanReadableCopyright':'SUSTech-BIO 2026 iGEM Team',
                    'NSAppTransportSecurity': {'NSAllowsLocalNetworking':True}})
