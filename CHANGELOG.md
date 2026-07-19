# Changelog

## 3.0.0-alpha2

- Aggiunta pagina Web per creare e ripristinare i backup.
- Aggiunta cronologia delle operazioni letta dal timeline JSONL.
- Aggiunta protezione CSRF a tutte le operazioni POST autenticate.
- Aggiunta Content Security Policy e rafforzati gli header HTTP.
- Limitato il ripristino ai soli backup generati nella cartella ZSM.
- Aggiunti test per cronologia e validazione del percorso di ripristino.


## 3.0.0-alpha1

- Avviata la linea 3.0 con pipeline CI per Python 3.10, 3.11 e 3.12.
- Aggiunti controlli automatici Ruff, pytest e compilazione dei moduli.
- Aggiunta build Docker automatica a ogni push e pull request.
- Aggiunta pubblicazione multi-architettura su GitHub Container Registry per tag `v*`.
- Ottimizzato il Dockerfile con build multi-stage e immagine runtime più pulita.
- Aggiornato Docker Compose per usare l'immagine GHCR e richiedere la password tramite `.env`.
- Aggiunto `.env.example` per evitare password predefinite nel repository.

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
