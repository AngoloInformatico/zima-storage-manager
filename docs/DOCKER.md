# Docker su ZimaOS

## Stato

Il pacchetto Docker è disponibile come modalità sperimentale. ZSM deve modificare il database di ZimaOS e controllare servizi dell'host, quindi il contenitore richiede privilegi elevati. L'installazione nativa con systemd resta la modalità raccomandata per il primo test.

## Installazione con immagine GHCR

Crea una cartella di lavoro e copia al suo interno:

- `docker-compose.yml`
- `config.example.json`
- `.env.example`, rinominandolo in `.env`

Modifica `.env` e imposta una password robusta:

```dotenv
ZSM_PASSWORD=una-password-lunga-e-unica
```

Avvia:

```bash
docker compose pull
docker compose up -d
```

Apri:

```text
http://IP_ZIMAOS:8787
```

## Build locale

Nel `docker-compose.yml`, commenta la riga `image:` e abilita:

```yaml
build: .
```

Poi esegui:

```bash
docker compose up -d --build
```

## Aggiornamento

```bash
docker compose pull
docker compose up -d
```

## Diagnostica

```bash
docker compose ps
docker compose logs --tail=200 zima-storage-manager
```

## Sicurezza

Il contenitore usa `privileged: true` e `pid: host` per accedere ai namespace dell'host. Non esporre la porta 8787 su Internet; usala solo in LAN o tramite VPN, ad esempio Tailscale.


Per l’importazione grafica in ZimaOS vedere [ZIMAOS_APPSTORE.md](ZIMAOS_APPSTORE.md).
