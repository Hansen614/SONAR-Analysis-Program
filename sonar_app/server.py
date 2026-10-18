"""Loopback-only HTTP interface. No cloud calls, uploads or external assets."""
from .localization import english_message
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import threading
from urllib.parse import parse_qs, urlparse
import webbrowser

from .backend import MAX_IMPORT_BYTES
from .export import export_bundle
from .measurement import MeasurementPipeline
from .experiments import Experiments


def create_server(platform, port=8765):
    pipeline = MeasurementPipeline(platform)
    experiments = Experiments(platform)
    token = secrets.token_urlsafe(32)
    lock = threading.Lock()
    assets = Path(__file__).parent / 'static'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def send(self, data, content_type='application/json', status=200, filename=None):
            if isinstance(data, (dict, list)):
                data = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
            elif isinstance(data, str):
                data = data.encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
            if filename:
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers(); self.wfile.write(data)

        def allowed_host(self):
            return self.headers.get('Host', '') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

        def do_GET(self):
            if not self.allowed_host():
                return self.send({'error':'Loopback host required'}, status=403)
            url = urlparse(self.path); q = parse_qs(url.query)
            try:
                if url.path in ('/', '/app.js', '/style.css', '/sonar-theme.css', '/visual-system.css', '/brand-home.css', '/pipeline.js', '/workflow.js', '/reporter-vector.js', '/reporter-engine.js', '/reporter-designer.js', '/reporter-designer.css'):
                    name = 'index.html' if url.path=='/' else url.path[1:]
                    kind = 'text/html; charset=utf-8' if url.path=='/' else ('text/css; charset=utf-8' if url.path.endswith('.css') else 'text/javascript; charset=utf-8')
                    return self.send((assets/name).read_bytes(), kind)
                if url.path == '/fonts/Manrope-Variable.ttf':
                    return self.send((assets/'fonts'/'Manrope-Variable.ttf').read_bytes(), 'font/ttf')
                brand_assets = {
                    '/brand/sonar-compact.svg': 'image/svg+xml; charset=utf-8',
                    '/brand/sonar-symbol.svg': 'image/svg+xml; charset=utf-8',
                    '/brand/sonar-welcome.svg': 'image/svg+xml; charset=utf-8',
                    '/brand/favicon.svg': 'image/svg+xml; charset=utf-8',
                    '/brand/apple-touch-icon.png': 'image/png',
                }
                if url.path in brand_assets:
                    return self.send((assets/url.path[1:]).read_bytes(), brand_assets[url.path])
                construction_downloads = {
                    '/downloads/Universal_Reporter_CDS.gb': ('Universal_Reporter_CDS.gb', 'application/octet-stream'),
                    '/downloads/Universal_Reporter_Plasmid.gb': ('Universal_Reporter_Plasmid.gb', 'application/octet-stream'),
                    '/downloads/Universal_Reporter_CDS.dna': ('Universal_Reporter_CDS.dna', 'application/octet-stream'),
                    '/downloads/Universal_Reporter_Plasmid.dna': ('Universal_Reporter_Plasmid.dna', 'application/octet-stream'),
                    '/downloads/RP02_Target_Reporter_Construction_by_Golden_Gate_Assembly.pdf': ('RP02_Target_Reporter_Construction_by_Golden_Gate_Assembly.pdf', 'application/pdf'),
                }
                if url.path in construction_downloads:
                    filename, kind = construction_downloads[url.path]
                    return self.send((assets/'downloads'/filename).read_bytes(), kind, filename=filename)
                if url.path in ('/reporter-maps/Universal_Reporter_CDS.svg', '/reporter-maps/Universal_Reporter_Plasmid.svg'):
                    return self.send((assets/url.path[1:]).read_bytes(), 'image/svg+xml; charset=utf-8')
                if url.path == '/api/session':
                    return self.send({'token':token})
                if url.path == '/api/overview':
                    with lock:
                        result = platform.overview(q.get('dataset',['reference'])[0], q.get('mode',['research'])[0])
                    return self.send(result)
                if url.path == '/api/analyses':
                    return self.send(pipeline.list_runs())
                if url.path == '/api/analysis':
                    with lock:
                        result=pipeline.load(q.get('id',[''])[0])
                    return self.send(result)
                if url.path == '/api/experiment-config':
                    return self.send(experiments.config())
                if url.path == '/api/experiments':
                    with lock:result=experiments.list()
                    return self.send(result)
                if url.path == '/api/experiment':
                    with lock:result=experiments.snapshot(q.get('id',[''])[0])
                    return self.send(result)
                return self.send({'error':'Not found'}, status=404)
            except (ValueError, KeyError, OSError) as exc:
                self.send({'error':str(exc)}, status=400)

        def do_POST(self):
            if not self.allowed_host() or self.headers.get('X-SONAR-Token') != token:
                return self.send({'error':'Invalid local session. Reload the page.'}, status=403)
            origin = self.headers.get('Origin')
            if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:
                return self.send({'error':'Cross-origin requests are disabled'}, status=403)
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= MAX_IMPORT_BYTES:
                    raise ValueError('Empty request or size limit exceeded.')
                raw = self.rfile.read(length)
                route = urlparse(self.path).path
                if route == '/api/experiment-upload':
                    q = parse_qs(urlparse(self.path).query)
                    with lock:
                        value=experiments.upload(q.get('id',[''])[0],q.get('stage',[''])[0],raw,q.get('name',[''])[0])
                    return self.send(value)
                if route == '/api/upload-fcs':
                    q = parse_qs(urlparse(self.path).query)
                    with lock:
                        value=pipeline.upload(raw,q.get('name',[''])[0])
                    return self.send(value)
                if route == '/api/import':
                    q = parse_qs(urlparse(self.path).query)
                    with lock:
                        value = platform.import_zip(raw, q.get('name',['Imported experiment'])[0])
                    return self.send(value)
                obj = json.loads(raw)
                with lock:
                    if route == '/api/folders':
                        value=experiments.folders(obj.get('path'))
                    elif route == '/api/experiment-example':
                        value=experiments.example(obj.get('stage','mock_upload'))
                    elif route == '/api/experiment-create':
                        value=experiments.create(obj.get('name',''),obj.get('save_parent',''))
                    elif route == '/api/experiment-remove-file':
                        value=experiments.remove_file(obj['experiment_id'],obj['file_id'])
                    elif route == '/api/experiment-revise':
                        value=experiments.revise(obj['experiment_id'],obj['stage'])
                    elif route == '/api/experiment-layer0':
                        value=experiments.analyze_mock(obj['experiment_id'],obj.get('cell_type',''),obj.get('channel_map',{}),obj.get('experiment_notes'))
                    elif route == '/api/experiment-confirm-theta':
                        value=experiments.confirm_theta(obj['experiment_id'])
                    elif route == '/api/experiment-compute':
                        value=experiments.compute(obj['experiment_id'],obj.get('settings',{}))
                    elif route == '/api/experiment-export':
                        return self.send(experiments.export(obj['experiment_id']),'application/zip',filename='SONAR_experiment_report.zip')
                    elif route == '/api/analyze':
                        value = platform.analyze(obj['sample_id'], obj.get('dataset','reference'), obj.get('population','reporter'), obj.get('mode','research'), obj.get('bootstrap',0))
                    elif route == '/api/inverse':
                        value = platform.inverse(obj['ras'], obj.get('mode','research'), obj.get('interval'))
                    elif route == '/api/validate':
                        value = platform.validate_dataset(obj.get('dataset','reference'))
                    elif route == '/api/fit':
                        value = platform.fit_references(obj['csv'], obj.get('name','User reference fit'))
                    elif route == '/api/pipeline':
                        value = pipeline.run(obj)
                    elif route == '/api/pipeline-example':
                        value = pipeline.example(bool(obj.get('full',False)))
                    elif route == '/api/pipeline-export':
                        value=pipeline.export(obj['run_id'])
                        return self.send(value,'application/zip',filename='SONAR_Theta_RAS_RES.zip')
                    elif route == '/api/export':
                        value = export_bundle(platform, obj.get('dataset','reference'), obj.get('mode','research'), obj.get('sample_ids'), obj.get('population','reporter'))
                        return self.send(value,'application/zip',filename='SONAR_measurement_export.zip')
                    else:
                        return self.send({'error':'Not found'},status=404)
                self.send(value)
            except Exception as exc:
                # Errors are visible, explicit and never converted into zero-valued reports.
                self.send({'error':english_message(str(exc)) or type(exc).__name__},status=400)

    server = ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.sap_operation_lock = lock
    server.daemon_threads = True
    return server


def serve(platform, port=8765, open_browser=False):
    server = create_server(platform, port)
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'SONAR ready: {url}',flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
