"""Finder-friendly local startup; reuse an already-running SONAR instance."""
from pathlib import Path
import json
import os
import urllib.request
import webbrowser
from sonar_app import __version__

os.chdir(Path(__file__).resolve().parent)
url='http://127.0.0.1:8765'
try:
    with urllib.request.urlopen(url+'/api/overview',timeout=2) as response:
        info=json.load(response)
    if info.get('app_version')==__version__ and info.get('release_id')=='sonar-science-v1.0-s7s10':
        webbrowser.open(url+'/#home')
        print('SONAR 已在运行：'+url)
        raise SystemExit(0)
except (OSError,ValueError):
    pass

from sonar_app.backend import Platform
from sonar_app.server import serve
serve(Platform(),8765,True)
