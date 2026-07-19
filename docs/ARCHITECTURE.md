# Architettura — v3.0.0-rc10

Zima Storage Manager è un'applicazione Python eseguita in un container Docker con accesso controllato alle risorse di ZimaOS.

## Componenti principali

- `zsm/web.py`: interfaccia web, autenticazione, conferme e navigazione;
- `zsm/config.py`: configurazione da file e variabili d'ambiente;
- `zsm/core/database.py`: accesso SQLite, backup, verifica e ripristino;
- `zsm/core/system.py`: lettura dei dispositivi, mount e servizi;
- `zsm/core/manager.py`: operazioni transazionali di rinomina e rollback;
- `zsm/core/history.py`: cronologia delle operazioni;
- `zsm/core/audit.py`: controlli diagnostici in sola lettura;
- `zsm/reports/generator.py`: creazione dei report;
- `zsm/cli.py`: comandi da terminale;
- `zsm/gui/`: interfaccia desktop opzionale.

## Flusso della rinomina

```text
Richiesta utente
      ↓
Identificazione del dispositivo tramite UUID
      ↓
Backup del database
      ↓
Controllo dei mount reali
      ↓
Smontaggio controllato, quando necessario
      ↓
Modifica dell'etichetta del filesystem
      ↓
Aggiornamento del database Local Storage
      ↓
Sincronizzazione e rimontaggio
      ↓
Verifica finale
      ↓
Successo oppure rollback
```

## Dati utilizzati

```text
Database ZimaOS: /var/lib/casaos/db/local-storage.db
Backup: /DATA/AppData/zima-storage-manager/backups
Report: /DATA/AppData/zima-storage-manager/reports
Log: /DATA/AppData/zima-storage-manager/logs
```

## Container

Il Compose usa:

- `privileged: true`;
- `pid: host`;
- bind mount di `/dev`, `/media`, `/DATA/.media`, `/var/lib/casaos` e `/var/lib/casaos_data`;
- socket D-Bus dell'host per controllare il servizio Local Storage;
- healthcheck HTTP sulla porta 8787.

Questi privilegi sono necessari perché la rinomina non è una semplice modifica grafica: coinvolge filesystem, mount, database e servizio di sistema.

## Sicurezza applicativa

Le operazioni distruttive richiedono una conferma. Le modifiche passano dal livello `StorageManager`; l'interfaccia web non scrive direttamente nel database SQLite.
