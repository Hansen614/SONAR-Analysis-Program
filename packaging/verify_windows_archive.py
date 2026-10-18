"""Validate a Windows candidate before attaching it to a draft public release."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import zipfile


def verify(folder):
    manifest = json.loads((folder / 'BUILD_MANIFEST.json').read_text(encoding='utf-8-sig'))
    name = manifest['artifact']
    if Path(name).name != name:
        raise ValueError('Invalid artifact filename')
    archive = folder / name
    assert hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest() == manifest['artifact_sha256']
    assert manifest['self_test']['status'] == 'PASS' and manifest['self_test']['frozen']
    assert manifest['gui_self_test']['status'] == 'PASS'
    assert manifest['gui_self_test']['bundled_webview2_process_verified']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        names = set(z.namelist())
        for path in ['SAP/SAP.exe', 'SAP/_internal/python313.dll', 'SAP/_internal/WebView2/msedgewebview2.exe',
                     'SAP/LICENSE', 'SAP/THIRD_PARTY_NOTICES/packages.json',
                     'SAP/_internal/sonar_app/desktop_terms.py',
                     'SAP/_internal/THIRD_PARTY_NOTICES/supplemental/Microsoft-WebView2-Fixed-Runtime.html']:
            assert path in names, path
        forbidden = [name for name in names if any(k in Path(name).name.lower() for k in ('libheif', 'libde265', 'libx265', '_pillow_heif'))]
        assert not forbidden, forbidden
        pe = z.read('SAP/SAP.exe')
        offset = struct.unpack_from('<I', pe, 0x3c)[0]
        assert pe[:2] == b'MZ' and pe[offset:offset+4] == b'PE\0\0'
        assert struct.unpack_from('<H', pe, offset+4)[0] == 0x8664
        assert struct.unpack_from('<H', pe, offset+24+68)[0] == 2
        reference = json.loads(z.read('SAP/_internal/scientific_reference/RELEASE_MANIFEST.json'))
        for row in reference['files']:
            assert hashlib.sha256(z.read('SAP/_internal/scientific_reference/' + row['path'])).hexdigest() == row['sha256']
        assert len(reference['files']) == 883
        for path, digest in manifest['sources'].items():
            # The source manifest also records the CLI-only entry point. The desktop
            # executable has its own entry point, so PyInstaller does not collect it.
            if path == 'sonar_app/__main__.py' and 'SAP/_internal/' + path not in names:
                continue
            assert hashlib.sha256(z.read('SAP/_internal/' + path)).hexdigest() == digest, path
    return {'status':'PASS', 'archive':name, 'bytes':archive.stat().st_size,
            'sha256':manifest['artifact_sha256'], 'source_commit':manifest['source_commit'],
            'reference_files_verified':883, 'gui_and_fcs_tests':'PASS', 'heic_codec_binaries':'excluded'}

if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1])), indent=2))
