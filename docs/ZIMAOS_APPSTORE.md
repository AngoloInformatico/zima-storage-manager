# Installazione manuale in ZimaOS App Store

## Immagine

- Immagine Docker: `ghcr.io/angoloinformatico/zima-storage-manager`
- Tag: `v3.0.0-rc4`
- Titolo: `Zima Storage Manager`
- Web UI: `http://IP_ZIMAOS:8787/`
- Rete: `bridge`
- Modalità privilegiata: attiva
- PID namespace: `host`
- Politica di riavvio: `unless-stopped`

## Porta

- Host: `8787`
- Container: `8787`
- Protocollo: TCP

## Variabili d'ambiente

| Nome | Valore |
|---|---|
| `ZSM_HOST` | `0.0.0.0` |
| `ZSM_PORT` | `8787` |
| `ZSM_CONTAINER_MODE` | `true` |
| `ZSM_HOST_NAMESPACE` | `1` |
| `ZSM_SERVICE_NAME` | `auto` |
| `ZSM_DATABASE_PATH` | `/var/lib/casaos/db/local-storage.db` |
| `ZSM_BACKUP_DIR` | `/var/lib/zsm/backups` |
| `ZSM_REPORT_DIR` | `/var/lib/zsm/reports` |
| `ZSM_LOG_DIR` | `/var/log/zsm` |
| `TZ` | `Europe/Rome` |

Inserire soltanto il valore, senza prefissi come `Valore:` e senza spazi iniziali.

## Volumi

| Host | Container | Modalità |
|---|---|---|
| `/var/lib/casaos` | `/var/lib/casaos` | lettura/scrittura |
| `/media` | `/media` | lettura/scrittura |
| `/DATA/.media` | `/DATA/.media` | lettura/scrittura |
| `/var/lib/casaos_data` | `/var/lib/casaos_data` | lettura/scrittura |
| `/dev` | `/dev` | lettura/scrittura |
| `/run/udev` | `/run/udev` | sola lettura |
| `/run/dbus/system_bus_socket` | `/run/dbus/system_bus_socket` | lettura/scrittura |
| `/DATA/AppData/zima-storage-manager/data` | `/var/lib/zsm` | lettura/scrittura |
| `/DATA/AppData/zima-storage-manager/logs` | `/var/log/zsm` | lettura/scrittura |

Prima dell'installazione si possono creare le directory persistenti da SSH:

```bash
sudo mkdir -p /DATA/AppData/zima-storage-manager/{data,logs}
```

## Controlli

```bash
sudo docker ps --filter name=zima-storage-manager
sudo docker logs --tail=100 zima-storage-manager
curl -i http://127.0.0.1:8787/health
```

Lo stato deve passare da `health: starting` a `healthy`.
