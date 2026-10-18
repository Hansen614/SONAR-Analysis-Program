"""One-time native Windows acknowledgement of bundled Microsoft runtime terms."""
from pathlib import Path
import hashlib
import json
import os
import sys


def ensure_runtime_terms(directory, resource_root=None, ask=None, open_document=None):
    root = resource_root or Path(getattr(sys, '_MEIPASS', Path(__file__).parents[1]))
    terms = root / 'THIRD_PARTY_NOTICES/supplemental/Microsoft-WebView2-Fixed-Runtime.html'
    if not terms.is_file():
        raise RuntimeError('The bundled WebView2 license is missing. Please re-extract the complete SAP package.')
    digest = hashlib.sha256(terms.read_bytes()).hexdigest()
    accepted = directory / 'webview2-terms.json'
    try:
        if json.loads(accepted.read_text(encoding='utf-8')).get('sha256') == digest:
            return True
    except (OSError, ValueError, AttributeError):
        pass
    if ask is None:
        import ctypes
        def ask(message):
            # Yes = agree; No = exit; Cancel = open the original full terms.
            return ctypes.windll.user32.MessageBoxW(None, message, 'SAP — Microsoft WebView2 terms', 0x03 | 0x20 | 0x100)
    open_document = open_document or os.startfile
    message = ('SAP uses Microsoft WebView2 Fixed Runtime, which has separate Microsoft license terms. '
               'SAP source code remains MIT licensed.\n\n'
               'The Runtime includes Microsoft Defender SmartScreen and may collect and send information '
               'to Microsoft. Privacy: https://aka.ms/privacy\n'
               'SmartScreen: https://learn.microsoft.com/en-us/microsoft-edge/privacy-whitepaper#smartscreen\n\n'
               'Yes: agree to the Microsoft Runtime terms and continue.\n'
               'No: exit SAP.\n'
               'Cancel: open the full terms, then return to this dialog.')
    while True:
        answer = ask(message)
        if answer == 6:
            accepted.write_text(json.dumps({'sha256': digest, 'accepted': True}), encoding='utf-8')
            return True
        if answer != 2:
            return False
        open_document(str(terms))
