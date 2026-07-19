# Installazione come app ZimaOS — v3.0.0-rc10

## Metodo consigliato

Per la maggior parte degli utenti è sufficiente aprire il terminale di ZimaOS e incollare:

```bash
curl -fsSL https://raw.githubusercontent.com/AngoloInformatico/zima-storage-manager/v3.0.0-rc10/scripts/install-zimaos.sh | sudo bash
```

Lo script prepara automaticamente la configurazione e verifica l'avvio.

## Importazione manuale del Compose

Usa questa procedura solo se preferisci importare l'app dall'interfaccia grafica di ZimaOS.

1. Apri **App Store**.
2. Seleziona l'opzione per installare o importare un'app personalizzata.
3. Importa il file `docker-compose.yml` presente nella release `v3.0.0-rc10`.
4. Controlla che la porta pubblicata sia `8787`.
5. Imposta una password sicura nella variabile `ZSM_PASSWORD`.
6. Salva e avvia l'app.

## Impostazioni principali

```text
Immagine: ghcr.io/angoloinformatico/zima-storage-manager:v3.0.0-rc10
Container: zima-storage-manager
Porta: 8787 TCP
Riavvio: unless-stopped
Modalità privilegiata: attiva
PID namespace: host
```

## Variabili d'ambiente

| Variabile | Valore consigliato |
|---|---|
| `ZSM_HOST` | `0.0.0.0` |
| `ZSM_PORT` | `8787` |
| `ZSM_PASSWORD` | una password sicura |
| `ZSM_CONTAINER_MODE` | `1` |
| `ZSM_HOST_NAMESPACE` | `1` |
| `ZSM_SERVICE_NAME` | `auto` |
| `ZSM_DATABASE_PATH` | `/var/lib/casaos/db/local-storage.db` |
| `ZSM_BACKUP_DIR` | `/var/lib/zsm/backups` |
| `ZSM_REPORT_DIR` | `/var/lib/zsm/reports` |
| `ZSM_LOG_DIR` | `/var/log/zsm` |
| `TZ` | `Europe/Rome` |

## Cartelle persistenti

```text
/DATA/AppData/zima-storage-manager/backups
/DATA/AppData/zima-storage-manager/reports
/DATA/AppData/zima-storage-manager/logs
```

## Verifica

```bash
sudo docker ps --filter name=zima-storage-manager
sudo docker logs --tail=100 zima-storage-manager
```

Apri quindi:

```text
http://IP_DEL_TUO_ZIMAOS:8787
```
