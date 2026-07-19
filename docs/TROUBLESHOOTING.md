# Risoluzione problemi — v3.0.0-rc10

## Il pannello non si apre

Controlla il container:

```bash
sudo docker ps --filter name=zima-storage-manager
```

Leggi i log:

```bash
sudo docker logs --tail=200 zima-storage-manager
```

Verifica che la porta 8787 non sia usata da un'altra applicazione.

## Il container non è healthy

```bash
curl -i http://127.0.0.1:8787/health
```

Se non risponde, riavvia il container:

```bash
sudo docker restart zima-storage-manager
```

## Il disco non appare nel tool

```bash
lsblk -o NAME,PATH,FSTYPE,LABEL,UUID,MOUNTPOINTS
```

Il disco deve avere un filesystem e un UUID validi. I record vecchi presenti soltanto nel database non vengono mostrati nella lista principale.

## Il disco appare nel tool ma non in ZimaOS

Controlla il servizio:

```bash
sudo systemctl status zimaos-local-storage.service
```

Poi riavvialo:

```bash
sudo systemctl restart zimaos-local-storage.service
```

Aggiorna la pagina Archiviazione di ZimaOS dopo alcuni secondi.

## La rinomina viene bloccata perché il disco è occupato

Individua i mount reali:

```bash
findmnt -rn -S /dev/sdX1 -o TARGET
```

Sostituisci `/dev/sdX1` con il dispositivo corretto. Arresta Jellyfin, Navidrome, condivisioni SMB o altre applicazioni che stanno usando quel volume, quindi riprova.

## Controllare l'etichetta reale

```bash
sudo blkid /dev/sdX1
```

oppure:

```bash
lsblk -o NAME,FSTYPE,LABEL,UUID,MOUNTPOINTS
```

## Verificare il database

```bash
sudo sqlite3 /var/lib/casaos/db/local-storage.db \
"SELECT id,uuid,mount_point,is_deleted FROM o_disk ORDER BY id;"
```

Non modificare manualmente il database senza averne prima creato una copia.

## Ripristino da backup

Usa la scheda **Backup** del pannello. Se il pannello non è disponibile, individua i file in:

```text
/DATA/AppData/zima-storage-manager/backups
```

## Aggiornamento non riuscito

Lo script di aggiornamento salva il Compose precedente in:

```text
/DATA/AppData/zima-storage-manager/updater-backups
```

Controlla inoltre:

```bash
sudo docker logs --tail=200 zima-storage-manager
```
