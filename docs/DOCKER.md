# Guida Docker — v3.0.0-rc10

Questa guida è destinata a chi vuole avviare Zima Storage Manager con Docker Compose senza usare lo script automatico di ZimaOS.

## Immagine

```text
ghcr.io/angoloinformatico/zima-storage-manager:v3.0.0-rc10
```

Sono disponibili immagini per `amd64` e `arm64`.

## Avvio con Docker Compose

Scarica il file `docker-compose.yml` della release e posizionalo in una cartella dedicata.

Crea le cartelle persistenti:

```bash
sudo mkdir -p /DATA/AppData/zima-storage-manager/{backups,reports,logs}
```

Crea un file `.env` nella stessa cartella del Compose:

```dotenv
ZSM_PASSWORD=scegli-una-password-sicura
TZ=Europe/Rome
```

Avvia il container:

```bash
sudo docker compose pull
sudo docker compose up -d
```

Apri:

```text
http://IP_DEL_SERVER:8787
```

## Controlli

```bash
sudo docker compose ps
sudo docker logs --tail=200 zima-storage-manager
curl -i http://127.0.0.1:8787/health
```

Lo stato finale deve essere `healthy`.

## Aggiornamento

Modifica il tag dell'immagine nel Compose, poi esegui:

```bash
sudo docker compose pull
sudo docker compose up -d --force-recreate --remove-orphans
```

## Arresto

```bash
sudo docker compose down
```

I backup, i report e i log restano nelle cartelle persistenti dell'host.

## Nota di sicurezza

Il container usa `privileged: true` e `pid: host` perché deve interagire con i dispositivi e con il servizio Local Storage dell'host. Non pubblicare la porta 8787 su Internet.
