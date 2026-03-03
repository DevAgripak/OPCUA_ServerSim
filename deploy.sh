#!/bin/bash

# Script di deploy per Ubuntu 24.04
# Target: /app/OPCUA_ServerSim/

APP_DIR="/app/OPCUA_ServerSim"
VENV_DIR="$APP_DIR/venv"

# Crea directory se non esiste
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copia i file (questo script assume che i file siano già nella directory corrente)
cp -r . $APP_DIR/

cd $APP_DIR

# Crea ambiente virtuale
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install --upgrade pip
pip install -r requirements.txt

# Configura il servizio systemd
cat <<EOF | sudo tee /etc/systemd/system/OPCUA_ServerSim.service
[Unit]
Description=OPC-UA Simulator Agripak
After=network.target

[Service]
Type=simple
User=agksrvadmin
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/python $APP_DIR/opcuasim_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Ricarica systemd e avvia il servizio
sudo systemctl daemon-reload
sudo systemctl enable opcuasim.service
sudo systemctl start opcuasim.service

echo "Deploy completato. Verifica lo stato con: sudo systemctl status opcuasim.service"
