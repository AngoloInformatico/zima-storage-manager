# Zima Storage Manager

Zima Storage Manager permette di rinominare in modo semplice il punto di montaggio di un disco su ZimaOS.

Non serve conoscere Python, SQLite o i comandi interni di ZimaOS. Dopo l'installazione si usa dal browser.

## Installazione semplice

Apri il terminale SSH di ZimaOS e incolla:

```bash
git clone https://github.com/AngoloInformatico/zima-storage-manager.git
cd zima-storage-manager
sudo bash install.sh
```

Al termine verranno mostrati:

- l'indirizzo da aprire nel browser, normalmente `http://IP_ZIMAOS:8765`;
- un codice di accesso personale.

## Utilizzo

1. Apri l'indirizzo mostrato dall'installer.
2. Seleziona il disco dall'elenco.
3. Scrivi il nuovo nome, per esempio `NAS3`.
4. Inserisci il codice di accesso.
5. Premi **Rinomina disco**.
6. Riavvia ZimaOS o scollega e ricollega il disco se il nuovo nome non appare subito.

ZSM crea automaticamente un backup del database prima di ogni modifica. Non formatta il disco e non cancella i file.

## Aggiornamento

```bash
cd zima-storage-manager
git pull
sudo bash install.sh
```

## Disinstallazione

```bash
cd zima-storage-manager
sudo bash uninstall.sh
```

Backup e configurazione vengono conservati.

## Sicurezza

Il servizio gira come root perché deve modificare il database di sistema di ZimaOS. È protetto da un codice generato durante l'installazione. Non esporre la porta `8765` direttamente su Internet.

Per visualizzare nuovamente il codice:

```bash
sudo cat /etc/zsm/zsm.env
```

## Compatibilità

Il progetto è stato progettato per ZimaOS e usa il database:

```text
/var/lib/casaos/db/local-storage.db
```

Prima di usarlo su versioni nuove di ZimaOS, verifica sempre che il database esista.
