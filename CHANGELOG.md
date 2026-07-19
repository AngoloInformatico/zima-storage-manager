# Changelog

## 2.1.0

- Corretta la rinomina per conservare il percorso radice già usato dal record (`/media`, `/DATA/.media` o `/var/lib/casaos_data/.media`).
- Aggiunti controlli sui nomi duplicati e sulle cartelle di destinazione in tutti i mount root configurati.
- Aggiunto un blocco di scrittura per impedire rinomine simultanee.
- Rafforzati backup e ripristino con `PRAGMA quick_check`, conservazione di permessi e proprietario del database.
- Migliorata la gestione di database con UUID duplicati.
- Aggiunto supporto sperimentale Docker con `Dockerfile`, Compose, healthcheck e documentazione dedicata.
- Aggiunto supporto ai namespace host per `systemctl`, `lsblk` e `findmnt` quando eseguito in container.
- Aggiunti test sul mantenimento del mount root e sul rifiuto del nome invariato.
- Versione applicazione aggiornata a 2.1.0.

## 2.0.0

- Nuova interfaccia web mobile-first.
- Dischi mostrati come schede, senza UUID visibili.
- Login tramite codice di accesso.
- Flusso guidato con conferma prima della modifica.
- Installazione come servizio systemd.
