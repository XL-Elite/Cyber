import importlib
import sys
import pathlib

# make local `src/` importable for tests
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))


def test_version_exists():
    mod = importlib.import_module('cyberos')
    assert hasattr(mod, '__version__')


def test_psutil_available():
    import psutil
    cpu = psutil.cpu_percent(interval=0.1)
    assert isinstance(cpu, float) or isinstance(cpu, int)
