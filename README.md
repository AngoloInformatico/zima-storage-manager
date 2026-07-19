# Zima Storage Manager

Interfaccia web per gestire in sicurezza i nomi dei dischi e i punti di montaggio utilizzati da ZimaOS.

![Versione](https://img.shields.io/badge/version-v3.0.0--rc5-blue)
![ZimaOS](https://img.shields.io/badge/ZimaOS-1.6.2-blue)
![Docker](https://img.shields.io/badge/Docker-amd64%20%7C%20arm64-blue)
![Licenza](https://img.shields.io/badge/license-BSD--3--Clause-green)

## Anteprima

![Dashboard di Zima Storage Manager](./img/zima-storage-manager-dashboard.png)

> Zima Storage Manager modifica il nome con cui ZimaOS registra e monta il disco, mantenendo coerenti il database Local Storage e i percorsi di montaggio.

## Funzioni principali

- rilevamento dei dischi registrati in ZimaOS;
- rinomina sicura dei dischi e dei punti di montaggio;
- backup automatico prima di ogni modifica;
- backup manuali e ripristino del database;
- controllo dell'integrità SQLite;
- cronologia e report delle operazioni;
- autenticazione web e protezione CSRF;
- diagnostica del database, del servizio e dei mount;
- supporto container ZimaOS con namespace host;
- persistenza di backup, report, log e cronologia;
- immagini Docker `linux/amd64` e `linux/arm64`.

## Compatibilità verificata

La release `v3.0.0-rc9` è progettata e verificata per:

```text
ZimaOS 1.6.2
Database: /var/lib/casaos/db/local-storage.db
Servizio: zimaos-local-storage.service
Porta Web: 8787
```

## Installazione e aggiornamento ZimaOS con un solo comando

Per installare o aggiornare una precedente RC:

```bash
curl -fsSL https://raw.githubusercontent.com/AngoloInformatico/zima-storage-manager/v3.0.0-rc9/scripts/install-zimaos.sh | sudo bash
```

Lo script ufficiale:

1. individua il container precedente;
2. copia sull'host eventuali backup, report e log rimasti nel container;
3. salva il Compose installato;
4. scarica il Compose dal tag GitHub della release;
5. conserva la password esistente oppure ne genera una sicura;
6. crea le cartelle persistenti;
7. scarica e avvia l'immagine corretta da GHCR;
8. verifica healthcheck, versione e mount;
9. esegue il rollback automatico in caso di errore.

Non è necessario modificare manualmente file YAML con `nano` o `sed`.

## Catena di distribuzione

La sorgente ufficiale segue sempre questo percorso:

```text
Cartella locale completa
        ↓
GitHub / main
        ↓
Tag v3.0.0-rc9
        ↓
GitHub Actions
        ↓
Immagine GHCR v3.0.0-rc9
        ↓
Updater ZimaOS
        ↓
Container verificato
```

Il file `VERSION` è la sorgente della versione. La CI impedisce la pubblicazione quando `VERSION`, pacchetto Python, Compose, README, Dockerfile e tag GitHub non coincidono.

## Immagine Docker

```text
ghcr.io/angoloinformatico/zima-storage-manager:v3.0.0-rc9
```

## Dati persistenti

I dati rimangono sull'host anche quando il container viene ricreato:

```text
/DATA/AppData/zima-storage-manager/backups
/DATA/AppData/zima-storage-manager/reports
/DATA/AppData/zima-storage-manager/logs
```

Montati nel container come:

```text
/var/lib/zsm/backups
/var/lib/zsm/reports
/var/log/zsm
```

## Controlli manuali dopo l'installazione

```bash
sudo docker ps --filter name=zima-storage-manager
```

```bash
ZSM_CONTAINER=$(sudo docker ps --filter name=zima-storage-manager --format '{{.Names}}' | head -n 1)
sudo docker exec "$ZSM_CONTAINER" python -c "import zsm; print(zsm.__version__)"
```

Il risultato atteso è:

```text
3.0.0-rc9
```

## Installazione nativa systemd

Rimane disponibile per ambienti che non utilizzano il container ZimaOS:

```bash
curl -fsSL https://raw.githubusercontent.com/AngoloInformatico/zima-storage-manager/main/install.sh | sudo bash
```

## Sicurezza

Prima di applicare una modifica, ZSM crea e verifica un backup, arresta temporaneamente il servizio Local Storage, aggiorna il database, controlla il risultato e ripristina il backup in caso di errore.

Non esporre direttamente la porta `8787` su Internet. Per l'accesso remoto è consigliata una VPN privata come Tailscale.

## Documentazione

- [Guida Docker](docs/DOCKER.md)
- [Installazione come app ZimaOS](docs/ZIMAOS_APPSTORE.md)
- [Guida utente](docs/USER_GUIDE.md)
- [Risoluzione problemi](docs/TROUBLESHOOTING.md)
- [Architettura](docs/ARCHITECTURE.md)

## Autore

**Created by Alex Lignola**

- GitHub: [AngoloInformatico](https://github.com/AngoloInformatico)
- YouTube: [Angolo Informatico](https://www.youtube.com/@AngoloInformatico)

## Licenza

BSD 3-Clause. Consulta [LICENSE](LICENSE).
