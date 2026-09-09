#!/usr/bin/env python3
"""Instala PageCraft como serviço systemd do utilizador, com arranque no boot."""
from pathlib import Path
import getpass
import json
import os
import shutil
import subprocess

repo = Path(__file__).resolve().parent.parent
python = repo / '.venv/bin/python'
if not python.is_file():
    raise SystemExit('Executa uv sync --frozen no repositório antes de instalar o serviço.')
unit_dir = Path.home() / '.config/systemd/user'
unit_dir.mkdir(parents=True, exist_ok=True)
codex = shutil.which('codex') or 'codex'
path = str(Path(codex).parent) + ':' + str(Path.home()/'.local/bin') + ':/usr/local/bin:/usr/bin:/bin'
unit = f'''[Unit]
Description=PageCraft Studio e atividades permanentes
After=network-online.target

[Service]
Type=simple
WorkingDirectory={str(repo).replace("%", "%%")}
ExecStart={json.dumps(str(python))} -m uvicorn server.app:app --host 127.0.0.1 --port 8777 --no-proxy-headers
Environment={json.dumps('PATH='+path)}
Environment=PAGECRAFT_PORT=8777
Environment={json.dumps('PAGECRAFT_CODEX_BIN='+codex)}
UMask=0077
Restart=on-failure
RestartSec=5
TimeoutStopSec=30

[Install]
WantedBy=default.target
'''
(unit_dir/'pagecraft.service').write_text(unit)
subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
subprocess.run(['loginctl', 'enable-linger', getpass.getuser()], check=True)
subprocess.run(['systemctl', '--user', 'enable', '--now', 'pagecraft.service'], check=True)
subprocess.run(['systemctl', '--user', 'is-active', 'pagecraft.service'], check=True)
print('Serviço instalado. Atualizar: systemctl --user restart pagecraft.service')
