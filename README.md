# Zima Storage Manager

Una semplice interfaccia web per cambiare il **nome del punto di montaggio usato da ZimaOS**.

> ZSM non cambia l'etichetta interna BTRFS/EXT4 del filesystem. Cambia il nome con cui ZimaOS registra e monta il disco, per esempio da `NAS2` a `NAS3`.

## Installazione con un solo comando

Apri il terminale SSH di ZimaOS e incolla:

```bash
curl -fsSL https://raw.githubusercontent.com/AngoloInformatico/zima-storage-manager/main/install.sh | sudo bash
```

Se `curl` non è disponibile:

```bash
wget -qO- https://raw.githubusercontent.com/AngoloInformatico/zima-storage-manager/main/install.sh | sudo bash
```

Alla fine dell'installazione compariranno l'indirizzo dell'app e il codice di accesso.

## Utilizzo

1. Apri dal browser l'indirizzo mostrato dall'installer.
2. Inserisci il codice di accesso.
3. Scegli il disco dalla schermata.
4. Premi **Cambia nome**.
5. Scrivi il nuovo nome.
6. Conferma.

Non è necessario conoscere UUID, SQLite, Python o comandi Linux.

## Sicurezza

Prima di ogni modifica ZSM:

- crea una copia di sicurezza del database;
- ferma temporaneamente il servizio di archiviazione;
- verifica la modifica;
- ripristina il database in caso di errore.

Il servizio è protetto da un codice di accesso generato durante l'installazione. Non esporre la porta `8765` direttamente su Internet.

Per rivedere il codice:

```bash
sudo grep ZSM_PASSWORD /etc/zsm/zsm.env
```

## Aggiornamento

```bash
sudo zsm-update
```

## Stato del servizio

```bash
sudo systemctl status zima-storage-manager
```

## Disinstallazione

Dal repository:

```bash
sudo bash uninstall.sh
```

Backup e configurazione non vengono cancellati automaticamente.

## Requisiti

- ZimaOS con `systemd`
- Python 3.10 o successivo
- modulo `python3-venv`
- `curl` oppure `wget`

## Nota importante

Il progetto interviene sul database di archiviazione di ZimaOS. Usalo solo dopo aver verificato che il percorso configurato in `/etc/zsm/config.json` corrisponda alla tua versione di ZimaOS.

## Pacchetto Docker sperimentale

È incluso anche un `Dockerfile` con `docker-compose.yml`. Tuttavia ZSM deve modificare il database dell'host e controllare un servizio systemd dell'host; per questo il contenitore richiede privilegi elevati, `pid: host` e bind mount delle directory ZimaOS.

La modalità Docker è quindi disponibile per test e futura integrazione nello store, ma **l'installazione nativa tramite systemd resta quella consigliata**.

Istruzioni complete: [`docs/DOCKER.md`](docs/DOCKER.md).

## Verifiche eseguite sulla release 2.1.0

- compilazione dei moduli Python;
- installazione del pacchetto in ambiente virtuale pulito;
- suite automatica: 9 test superati;
- verifica dei file Docker e Compose a livello statico.

Il test finale sul server ZimaOS reale è comunque necessario, perché versioni diverse di ZimaOS possono usare percorsi del database o nomi del servizio differenti.

## Docker e GitHub Container Registry

Le immagini dei tag di release vengono pubblicate automaticamente per `linux/amd64` e `linux/arm64` su GitHub Container Registry. La configurazione completa è descritta in `docs/DOCKER.md`.


## Funzioni Web v3 alpha2

La Web UI include gestione dischi, backup manuali, ripristino controllato e cronologia delle operazioni. Tutte le azioni di scrittura richiedono autenticazione, token CSRF e una conferma esplicita.
