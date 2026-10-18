"""Desktop lifecycle around the unchanged local SAP application."""
from __future__ import annotations
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import threading


def user_directory():
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'SAP'
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/SAP'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'SAP'


class InstanceLock:
    """OS-owned lock: automatically released even if an application crashes."""
    def __init__(self, directory):
        self.file = (directory / 'desktop.lock').open('a+b')
        try:
            if sys.platform == 'win32':
                import msvcrt
                self.file.seek(0)
                if not self.file.read(1):
                    self.file.write(b'0'); self.file.flush()
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError('SAP is already running. Please return to its open window.')

    def close(self):
        self.file.close()


def native_error(message):
    if sys.platform == 'darwin':
        from AppKit import NSAlert, NSApplication
        NSApplication.sharedApplication()
        alert = NSAlert.alloc().init()
        alert.setMessageText_('SONAR Analysis Program')
        alert.setInformativeText_(message)
        alert.runModal()
    elif sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, 'SONAR Analysis Program', 0x10)
    elif sys.stderr:
        print(message, file=sys.stderr)


def smoke_test(platform, destination):
    """Exercise real bundled FCS, source identity, API and exports in the frozen binary."""
    import math
    import urllib.request
    from .experiments import Experiments
    from .server import create_server
    from . import pipeline
    from .backend import sha, write_json
    e = Experiments(platform)
    result = e.example('complete')
    sample = result['result']['samples'][0]
    assert math.isclose(sample['RAS']['ras'], .9562602659677872, rel_tol=1e-12)
    assert math.isclose(sample['RES']['model_estimate_res_mass_fraction'], .7454898213131971, rel_tol=1e-12)
    assert sample['RES']['res_mass_fraction'] is None
    assert result['Theta']['pipeline_sha256'] == sha(Path(pipeline.__file__))
    assert result['result']['workflow']['theta_reused_without_refit']
    assert e.export(result['experiment_id']).startswith(b'PK')
    server = create_server(platform, 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    try:
        base = f'http://127.0.0.1:{server.server_port}'
        routes = ['/', '/api/session', '/api/overview', '/brand/sonar-compact.svg',
                  '/reporter-engine.js', '/reporter-designer.js', '/fonts/Manrope-Variable.ttf',
                  '/downloads/Universal_Reporter_CDS.gb', '/downloads/Universal_Reporter_Plasmid.gb',
                  '/downloads/RP02_Target_Reporter_Construction_by_Golden_Gate_Assembly.pdf']
        for route in routes:
            with urllib.request.urlopen(base + route) as response:
                assert response.status == 200 and response.read()
    finally:
        server.shutdown(); server.server_close(); worker.join()
    status = {'status': 'PASS', 'frozen': bool(getattr(sys, 'frozen', False)),
              'integrity': platform.verify_release(), 'pipeline_sha256': sha(Path(pipeline.__file__)),
              'RAS': sample['RAS']['ras'], 'RES_model_estimate': sample['RES']['model_estimate_res_mass_fraction'],
              'qualified_RES': sample['RES']['res_mass_fraction'], 'api_routes': len(routes),
              'dependencies': platform.dependency_status(), 'python': sys.version,
              'platform': sys.platform}
    assert all(d['matches'] for d in status['dependencies']), status['dependencies']
    write_json(destination / 'self-test.json', status)
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', type=Path, metavar='OUTPUT_DIRECTORY')
    args = parser.parse_args()
    directory = args.self_test.resolve() if args.self_test else user_directory()
    directory.mkdir(parents=True, exist_ok=True)
    logs = directory / 'logs'; logs.mkdir(exist_ok=True)
    handler = RotatingFileHandler(logs / 'SAP.log', maxBytes=2_000_000, backupCount=3, encoding='utf-8')
    logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(asctime)s %(levelname)s %(message)s')
    # Preserve scientific source bytes while preventing writes into the app bundle.
    sys.dont_write_bytecode = True
    os.environ['MPLBACKEND'] = 'Agg'
    guard = server = None
    try:
        guard = InstanceLock(directory)
        from .backend import Platform
        platform = Platform(workspace=directory / 'workspace')
        if args.self_test:
            smoke_test(platform, directory)
            return 0
        import webview
        from .server import create_server
        webview.settings['ALLOW_DOWNLOADS'] = True
        webview.settings['ALLOW_FILE_URLS'] = False
        if sys.platform == 'win32':
            runtime = Path(getattr(sys, '_MEIPASS', Path(__file__).parents[1])) / 'WebView2'
            if runtime.is_dir():
                webview.settings['WEBVIEW2_RUNTIME_PATH'] = str(runtime)
        port_file = directory / 'desktop-port.json'
        try:
            port = int(json.loads(port_file.read_text())['port'])
            if not 1024 <= port <= 65535:
                port = 0
        except (OSError, ValueError, KeyError, TypeError):
            port = 0
        try:
            server = create_server(platform, port)
        except OSError:
            server = create_server(platform, 0)
        port_file.write_text(json.dumps({'port':server.server_port}), encoding='utf-8')
        threading.Thread(target=server.serve_forever, daemon=True).start()
        window = webview.create_window('SONAR Analysis Program',
            f'http://127.0.0.1:{server.server_port}/#home', width=1280, height=850,
            min_size=(900, 650), text_select=True, background_color='#F5F7FA')
        def closing():
            if server.sap_operation_lock.locked():
                window.create_confirmation_dialog('Calculation in progress',
                    'Please wait for the current operation to finish before closing SAP.')
                return False
        window.events.closing += closing
        webview.start(gui='edgechromium' if sys.platform == 'win32' else 'cocoa',
                      private_mode=False, storage_path=str(directory / 'webview'))
        return 0
    except Exception as exc:
        logging.exception('SAP failed')
        if args.self_test:
            (directory / 'FAILED.txt').write_text(str(exc), encoding='utf-8')
        else:
            native_error(f'{exc}\n\nDiagnostic log: {logs / "SAP.log"}')
        return 1
    finally:
        if server:
            server.shutdown(); server.server_close()
        if guard:
            guard.close()
