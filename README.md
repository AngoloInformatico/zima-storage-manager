# Zima Storage Manager

Interfaccia web per gestire in modo sicuro i nomi dei dischi e i punti di montaggio utilizzati da ZimaOS.

![Versione](https://img.shields.io/badge/version-v3.0.0--rc3-blue)
![ZimaOS](https://img.shields.io/badge/ZimaOS-1.6.2-blue)
![Docker](https://img.shields.io/badge/Docker-amd64%20%7C%20arm64-blue)
![License](https://img.shields.io/badge/license-BSD--3--Clause-green)

## Anteprima

![Zima Storage Manager su ZimaOS](img/zima-storage-manager-dashboard.png)

> Zima Storage Manager non modifica necessariamente l'etichetta interna del filesystem.  
> Modifica il nome con cui ZimaOS registra e monta il disco, mantenendo il percorso coerente nel database Local Storage.

## Funzioni principali

- rilevamento automatico dei dischi registrati in ZimaOS;
- rinomina dei dischi e dei relativi punti di montaggio;
- mantenimento e aggiornamento dei percorsi nel database;
- backup automatico prima di ogni modifica;
- creazione di backup manuali;
- ripristino del database;
- verifica dell'integrità SQLite;
- cronologia delle operazioni;
- autenticazione web;
- protezione CSRF;
- conferma delle operazioni critiche;
- pagina di diagnostica;
- rilevamento automatico del servizio Local Storage;
- supporto installazione nativa con systemd;
- supporto Docker e ZimaOS App Store;
- immagini container per `amd64` e `arm64`;
- aggiornamenti automatici tramite GitHub Actions.

## Compatibilità verificata

La release candidate `v3.0.0-rc3` è stata provata su:

```text
ZimaOS 1.6.2
Database: /var/lib/casaos/db/local-storage.db
Servizio: zimaos-local-storage.service
Architettura: amd64