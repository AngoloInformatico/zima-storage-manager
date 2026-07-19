# Installazione dall'App Store di ZimaOS

Questa modalità usa l'importazione di un'app personalizzata basata su Docker Compose.

## Requisiti

- ZimaOS 1.6.2 o successivo
- architettura amd64 oppure arm64
- immagine pubblicata su GHCR con lo stesso tag indicato nel Compose

## Procedura

1. Apri **App Store** in ZimaOS.
2. Premi **+** e scegli l'installazione di un'app personalizzata.
3. Importa il contenuto di `docker-compose.yml`.
4. Imposta una password sicura in `ZSM_PASSWORD`.
5. Conferma la porta `8765` e avvia l'app.
6. Apri `http://IP-DELLO-ZIMAOS:8765`.

## Permessi

La RC2 usa un container privilegiato con `pid: host` perché deve:

- interrogare i dispositivi a blocchi reali;
- accedere al database Local Storage;
- arrestare e riavviare il servizio storage dell'host;
- verificare i mount esposti da ZimaOS.

Questi permessi sono elevati. Installare solo l'immagine ufficiale del repository e non esporre la porta direttamente su Internet.

## Percorsi host montati

- `/var/lib/casaos/db`
- `/media`
- `/DATA/.media`
- `/var/lib/casaos_data/.media`
- `/dev`
- `/run/udev` in sola lettura

Backup, report e cronologia sono persistenti nei volumi Docker `zsm-data` e `zsm-logs`.

## Servizio Local Storage

Con `ZSM_SERVICE_NAME=auto`, ZSM prova in ordine:

1. `zimaos-local-storage.service`
2. `casaos-local-storage.service`
3. `local-storage.service`

Il servizio effettivamente rilevato viene mostrato nella pagina **Diagnostica**.

## Aggiornamento

Aggiornare il tag dell'immagine nel Compose, quindi ricreare il container. I volumi persistenti non vengono eliminati.
