# Esecuzione con Docker su ZimaOS

## Valutazione tecnica

ZSM non è una normale applicazione web: deve leggere e modificare il database host di ZimaOS e fermare/riavviare il servizio `zimaos-local-storage.service` durante la scrittura. Per questo il contenitore richiede:

- accesso in scrittura a `/var/lib/casaos/db`;
- accesso ai percorsi di montaggio;
- `pid: host` e modalità `privileged`;
- `nsenter` per eseguire `systemctl`, `lsblk` e `findmnt` nel namespace dell'host.

Questa configurazione funziona come pacchetto Docker sperimentale, ma concede al contenitore privilegi elevati. L'installazione nativa tramite `systemd` resta la modalità consigliata e più semplice da controllare.

## Avvio

1. Modifica `docker-compose.yml` e sostituisci `CAMBIA_QUESTO_CODICE` con una password robusta.
2. Verifica in `config.example.json` il percorso del database e il nome del servizio della tua versione di ZimaOS.
3. Avvia:

```bash
docker compose up -d --build
```

4. Apri `http://IP_ZIMAOS:8765`.

## Aggiornamento

```bash
git pull
docker compose up -d --build
```

## Arresto

```bash
docker compose down
```

I backup restano nel volume Docker `zsm-data`.

## Avvertenza

Non pubblicare la porta 8765 su Internet. Usala solo nella rete locale o tramite una VPN come Tailscale.
