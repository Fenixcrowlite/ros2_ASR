from __future__ import annotations

from pathlib import Path

from asr_launch.launch_env import runtime_python_env


def test_runtime_python_env_includes_virtualenv_site_packages(
    monkeypatch,
    tmp_path: Path,
) -> None:
    venv_root = tmp_path / ".venv"
    site_packages = venv_root / "lib" / "python3.12" / "site-packages"
    cuda_lib = site_packages / "nvidia" / "cublas" / "lib"
    cuda_lib.mkdir(parents=True)

    monkeypatch.setenv("VIRTUAL_ENV", str(venv_root))
    monkeypatch.setenv("PYTHONPATH", "/existing/pythonpath")
    monkeypatch.setenv("LD_LIBRARY_PATH", "/existing/ldpath")

    env = runtime_python_env()

    assert env["PYTHONPATH"].split(":")[0] == str(site_packages)
    assert "/existing/pythonpath" in env["PYTHONPATH"]
    assert env["LD_LIBRARY_PATH"].split(":")[0] == str(cuda_lib)
    assert "/existing/ldpath" in env["LD_LIBRARY_PATH"]
