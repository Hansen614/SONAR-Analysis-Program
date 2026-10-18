"""English presentation for legacy pipeline messages; never alters scientific values."""
import json
import re
from pathlib import Path
_MESSAGES = json.loads(Path(__file__).with_name('english_messages.json').read_text())
_PATTERN = re.compile('|'.join(re.escape(k) for k in sorted(_MESSAGES, key=len, reverse=True)))
def english_message(value):
    return _PATTERN.sub(lambda match: _MESSAGES[match.group()], str(value))
