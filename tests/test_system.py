import pytest

from zsm.core.runner import Result
from zsm.core.system import SystemInspector, validate_name


def test_valid_names():
    assert validate_name("NAS3") == "NAS3"


@pytest.mark.parametrize("name", ["", "../bad", "bad/name", "a" * 65])
def test_invalid_names(name):
    with pytest.raises(ValueError):
        validate_name(name)


class FakeRunner:
    def __init__(self, loaded: str):
        self.loaded = loaded

    def run(self, args, check=False, timeout=30):
        service = args[-3] if "show" in args else args[-1]
        if "show" in args:
            value = "loaded" if service == self.loaded else "not-found"
            return Result(args, 0, value, "")
        return Result(args, 0, "active", "")


def test_service_auto_detection(monkeypatch):
    monkeypatch.delenv("ZSM_HOST_NAMESPACE", raising=False)
    inspector = SystemInspector(FakeRunner("casaos-local-storage.service"))
    assert inspector.resolve_service("auto") == "casaos-local-storage.service"


def test_explicit_service_is_preserved(monkeypatch):
    monkeypatch.delenv("ZSM_HOST_NAMESPACE", raising=False)
    inspector = SystemInspector(FakeRunner("casaos-local-storage.service"))
    assert inspector.resolve_service("custom.service") == "custom.service"
