# Installation

## ZimaOS host

Copy the repository to the server and run:

```bash
chmod +x install.sh uninstall.sh
sudo ./install.sh
```

The installer creates an isolated virtual environment in `/opt/zima-storage-manager`, commands in `/usr/local/bin`, configuration in `/etc/zsm`, and persistent data directories under `/var/lib/zsm` and `/var/log/zsm`.

CustomTkinter requires Tk. If the base image lacks it, install the distribution package providing Python Tk support. On a headless machine use `zsm` through SSH.

## Manual development install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```
