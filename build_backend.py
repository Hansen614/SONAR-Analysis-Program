"""Minimal offline PEP 517 wheel builder; no build-time third-party dependencies."""
import base64
import csv
import hashlib
import io
from pathlib import Path
import zipfile

NAME = 'sonar_platform'
VERSION = '1.4.0rc1'
DIST = f'{NAME}-{VERSION}.dist-info'
ROOT = Path(__file__).resolve().parent


def get_requires_for_build_wheel(config_settings=None):
    return []


def metadata():
    deps = (ROOT/'scientific_reference/environment/requirements.lock.txt').read_text().splitlines()
    return ('Metadata-Version: 2.1\nName: sonar-platform\nVersion: 1.4.0rc1\n'
        'Summary: Local SONAR scientific measurement platform with frozen reference data\n'
        'Requires-Python: >=3.13,<3.14\n' + ''.join(f'Requires-Dist: {d}\n' for d in deps) + '\n')


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    dest=Path(wheel_directory);dest.mkdir(parents=True,exist_ok=True)
    filename=f'{NAME}-{VERSION}-py3-none-any.whl'
    records=[]
    with zipfile.ZipFile(dest/filename,'w',zipfile.ZIP_DEFLATED) as z:
        def add(name,data):
            z.writestr(name,data)
            records.append((name,'sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode(),len(data)))
        for directory in ['sonar_app','scientific_reference']:
            for p in sorted((ROOT/directory).rglob('*')):
                rel=p.relative_to(ROOT)
                if p.is_file() and not any(k in rel.parts for k in ['_work','__pycache__','.pytest_cache']):
                    add(rel.as_posix(),p.read_bytes())
        add('scientific_reference/__init__.py',b'"""Frozen SONAR reference payload; original file bytes preserved."""\n')
        add(f'{DIST}/METADATA',metadata().encode())
        add(f'{DIST}/WHEEL',b'Wheel-Version: 1.0\nGenerator: sonar-local-build\nRoot-Is-Purelib: true\nTag: py3-none-any\n')
        add(f'{DIST}/entry_points.txt',b'[console_scripts]\nsonar = sonar_app.__main__:main\n')
        stream=io.StringIO(newline='');writer=csv.writer(stream);writer.writerows(records);writer.writerow((f'{DIST}/RECORD','',''))
        z.writestr(f'{DIST}/RECORD',stream.getvalue())
    return filename


if __name__=='__main__':
    print(build_wheel(ROOT/'dist'))
