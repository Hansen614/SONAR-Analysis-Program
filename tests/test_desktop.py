"""Desktop lifecycle contracts; numerical regressions stay in pipeline tests."""
import subprocess
import sys
from pathlib import Path

from sonar_app.desktop import InstanceLock, user_directory


def test_second_process_cannot_lock_active_workspace(tmp_path):
    lock = InstanceLock(tmp_path)
    code = ('from pathlib import Path; from sonar_app.desktop import InstanceLock; '
            f'InstanceLock(Path({str(tmp_path)!r}))')
    try:
        blocked = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
        assert blocked.returncode != 0
        assert 'already running' in blocked.stderr
    finally:
        lock.close()
    assert subprocess.run([sys.executable, '-c', code], capture_output=True).returncode == 0


def test_default_workspace_is_outside_application_directory():
    destination = user_directory()
    assert destination.is_absolute()
    assert not destination.is_relative_to(Path(__file__).resolve().parents[1])
