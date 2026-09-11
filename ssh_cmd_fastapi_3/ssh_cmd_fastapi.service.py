# /etc/systemd/system/inspect.service
[Unit]
Description=Host Inspection API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/inspect
EnvironmentFile=/opt/inspect/inspect.env
ExecStart=/usr/bin/python3 -m uvicorn ssh_cmd_fastapi:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
User=inspect

[Install]
WantedBy=multi-user.target