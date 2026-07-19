# Changelog

## 3.0.0-rc8

- Usa `findmnt -S <device>` come unica fonte dei mount reali prima della rinomina.
- Salta correttamente `umount` quando il dispositivo è già smontato.
- Non passa più al comando `umount` i percorsi obsoleti memorizzati nel database.
- Sostituisce `fuser -vm` con il più compatibile `fuser -m`.
- Verifica nuovamente la tabella mount dopo ogni smontaggio e prima della modifica della LABEL.

## 3.0.0-rc7

- Consente rinomine ripetute anche quando il volume USB è già montato.
- Arresta Local Storage, smonta in modo controllato tutti i mount del volume e segnala i processi che lo tengono occupato.
- Modifica realmente la LABEL del filesystem, aggiorna `o_disk` e attende il rimontaggio sul nuovo percorso.
- Esegue `udevadm settle` e verifica LABEL e mountpoint prima di dichiarare successo.
- Rimuove le cartelle vuote associate al vecchio nome e nasconde i record database non più presenti.
- Rollback di database e LABEL in caso di errore.

## v3.0.0-rc7

- introdotto il file unico `VERSION`;
- aggiunto controllo automatico di coerenza della versione;
- aggiunto installer/updater ZimaOS a un solo comando;
- migrazione automatica di backup, report e log dai container precedenti;
- aggiunto rollback automatico durante l'aggiornamento;
- verifiche automatiche di healthcheck, versione e mount persistenti;
- Compose completo con metadati ZimaOS per i volumi persistenti;
- README completo con anteprima dashboard;
- pipeline limitata al ramo `main`.

## v3.0.0-rc7 - 2026-07-19

- Resi persistenti i backup tramite `/DATA/AppData/zima-storage-manager/backups`.
- Resi persistenti i report tramite `/DATA/AppData/zima-storage-manager/reports`.
- Resi persistenti log e cronologia tramite `/DATA/AppData/zima-storage-manager/logs`.
- Aggiornato il Compose per l'importazione nell'App Store di ZimaOS.
- Aggiornato il riferimento dell'icona al ramo principale `main`.


## 3.0.0-rc3

- aggiunta installazione come app personalizzata ZimaOS tramite Docker Compose e metadati `x-casaos`;
- aggiunto rilevamento automatico del servizio Local Storage;
- aggiunti override di configurazione tramite variabili d’ambiente;
- aggiunta identificazione della modalità container nella diagnostica;
- aggiunta icona applicazione e guida App Store;
- aggiunti test per configurazione container e rilevamento servizi.

## 3.0.0-rc1

- Pagina diagnostica con stato database, servizio e configurazione attiva.
- Ripristino backup protetto da doppia conferma monouso.
- Conservazione automatica dei backup con soglia configurabile.
- Validazione più rigorosa della configurazione JSON.
- Session store protetto per accessi concorrenti.
- Suite di test ampliata.

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
