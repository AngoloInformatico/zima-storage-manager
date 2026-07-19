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

class MountRunner:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def run(self, args, check=False, timeout=30):
        self.calls.append(args)
        if not self.responses:
            return Result(args, 0, "", "")
        return self.responses.pop(0)


def test_unmount_device_skips_umount_when_already_unmounted(monkeypatch):
    monkeypatch.delenv("ZSM_HOST_NAMESPACE", raising=False)
    runner = MountRunner([Result([], 1, "", "")])
    inspector = SystemInspector(runner)
    assert inspector.unmount_device("/dev/sde1") == []
    assert not any(call and call[0] == "umount" for call in runner.calls)


def test_unmount_device_uses_only_findmnt_targets(monkeypatch):
    monkeypatch.delenv("ZSM_HOST_NAMESPACE", raising=False)
    runner = MountRunner([
        Result([], 0, "/media/NAS4\n/DATA/.media/NAS4\n", ""),
        Result([], 0, "", ""),
        Result([], 0, "", ""),
        Result([], 1, "", ""),
    ])
    inspector = SystemInspector(runner)
    assert inspector.unmount_device("/dev/sde1") == ["/DATA/.media/NAS4", "/media/NAS4"]
    umount_calls = [call for call in runner.calls if call and call[0] == "umount"]
    assert umount_calls == [["umount", "/DATA/.media/NAS4"], ["umount", "/media/NAS4"]]


def test_busy_processes_uses_compatible_fuser_flags(monkeypatch):
    monkeypatch.delenv("ZSM_HOST_NAMESPACE", raising=False)
    runner = MountRunner([Result([], 0, "1234", "")])
    inspector = SystemInspector(runner)
    assert inspector.busy_processes("/media/NAS4") == "1234"
    assert runner.calls[0] == ["fuser", "-m", "/media/NAS4"]
