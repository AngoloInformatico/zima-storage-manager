from __future__ import annotations
import subprocess
from dataclasses import dataclass

@dataclass(slots=True)
class Result:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str

class CommandRunner:
    def run(self, args: list[str], check: bool = False, timeout: int = 30) -> Result:
        try:
            p = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        except FileNotFoundError as exc:
            return Result(args, 127, "", str(exc))
        result = Result(args, p.returncode, p.stdout.strip(), p.stderr.strip())
        if check and result.returncode != 0:
            raise RuntimeError(
                f"Command failed ({result.returncode}): {' '.join(args)}\n{result.stderr}"
            )
        return result
