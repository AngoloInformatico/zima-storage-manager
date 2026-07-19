# Zima Storage Manager

![Versione](https://img.shields.io/badge/version-v3.0.0--rc10-blue)
![ZimaOS](https://img.shields.io/badge/ZimaOS-1.6.2-blue)
![Docker](https://img.shields.io/badge/Docker-amd64%20%7C%20arm64-blue)
![Licenza](https://img.shields.io/badge/license-Apache--2.0-green)

Zima Storage Manager è un piccolo pannello web per rinominare in sicurezza i dischi collegati a ZimaOS.

L'Idea Nasce, dalla mancanza della funzione di Rinomina dei Dischi collegati al Server con ZimaOs installato,
Quando si collegano HD , SSD , dischi USB ecc. viene assegnata l'etichetta iniziale,
da quel momento non c'è un modo semplice per rinominare le etichette dei vari dischi,
ecco che interviene Zima Storage Manager in modo semplice rinomina i dischi collegati.


Il tool aggiorna l'etichetta reale del filesystem, il database Local Storage e il punto di montaggio. Prima delle operazioni importanti crea un backup e, in caso di errore, prova a ripristinare la situazione precedente.

## Anteprima

![Dashboard di Zima Storage Manager](./img/zima-storage-manager-dashboard.png)

## Cosa permette di fare

- visualizzare i dischi realmente collegati;
- rinominare l'etichetta del filesystem e il nome mostrato da ZimaOS;
- creare, ripristinare ed eliminare i backup;
- consultare e svuotare la cronologia;
- eseguire controlli diagnostici su database, servizio e mount;
- evitare la visualizzazione di vecchi dispositivi non più presenti.

## Requisiti

Questa documentazione si riferisce alla versione **v3.0.0-rc10**, verificata su:

```text
ZimaOS 1.6.2
Docker
Porta web 8787
```

## Installazione facile su ZimaOS

Questa è la procedura consigliata anche per chi non ha esperienza con Linux.

### 1. Apri il terminale di ZimaOS

Accedi a ZimaOS dal browser, apri l'app **Terminale** oppure collegati al server tramite SSH.

### 2. Copia e incolla questo comando

```bash
curl -fsSL https://raw.githubusercontent.com/AngoloInformatico/zima-storage-manager/v3.0.0-rc10/scripts/install-zimaos.sh | sudo bash
```

Quando richiesto, inserisci la password dell'utente amministratore. Durante la digitazione la password potrebbe non essere visibile: è normale.

### 3. Attendi il completamento

Lo script scarica l'app, crea le cartelle necessarie, avvia il container e verifica che funzioni correttamente.

Al termine mostra anche il codice di accesso al pannello web. Conservalo.

### 4. Apri il pannello

Nel browser visita:

```text
http://IP_DEL_TUO_ZIMAOS:8787
```

Esempio:

```text
http://192.168.1.20:8787
```

Inserisci il codice mostrato al termine dell'installazione.

## Aggiornamento

Per aggiornare una versione già installata alla v3.0.0-rc10:

```bash
curl -fsSL https://raw.githubusercontent.com/AngoloInformatico/zima-storage-manager/v3.0.0-rc10/scripts/update-zimaos.sh | sudo bash
```

## Controllo rapido

```bash
sudo docker ps --filter name=zima-storage-manager
```

Il container deve risultare `Up` e `healthy`.

Per controllare la versione:

```bash
sudo docker exec zima-storage-manager python -c 'import zsm; print(zsm.__version__)'
```

Risultato atteso:

```text
3.0.0-rc10
```

## Uso di base

1. Apri la scheda **Dischi**.
2. Seleziona il disco da rinominare.
3. Inserisci il nuovo nome.
4. Leggi la schermata di conferma.
5. Conferma la rinomina e attendi il risultato.

Non spegnere il server e non scollegare il disco durante l'operazione.

Prima di rinominare un disco che contiene file usati da Jellyfin, Navidrome o altre app, arresta temporaneamente quelle app.

## Dati salvati sul server

```text
/DATA/AppData/zima-storage-manager/backups
/DATA/AppData/zima-storage-manager/reports
/DATA/AppData/zima-storage-manager/logs
```

I dati rimangono disponibili anche quando il container viene aggiornato o ricreato.

## Sicurezza

Zima Storage Manager deve accedere ai dischi e al servizio Local Storage di ZimaOS, quindi il container usa privilegi elevati.

Usalo solo nella rete locale o tramite una VPN privata come Tailscale. Non esporre direttamente la porta `8787` su Internet.

## Documentazione

- [Guida Docker](docs/DOCKER.md)
- [Installazione come app ZimaOS](docs/ZIMAOS_APPSTORE.md)
- [Guida utente](docs/USER_GUIDE.md)
- [Risoluzione problemi](docs/TROUBLESHOOTING.md)
- [Architettura](docs/ARCHITECTURE.md)

## ⚠️ Avvertenza importante

Zima Storage Manager interviene direttamente sui dischi, sulle etichette dei filesystem, sui punti di montaggio e sul database di archiviazione di ZimaOS.

Utilizzare il software con la massima attenzione e solo dopo aver effettuato un backup dei dati importanti.

Prima di eseguire una rinomina o un ripristino:

- verificare di aver selezionato il disco corretto;
- chiudere eventuali applicazioni che stanno utilizzando il disco;
- non spegnere o riavviare il server durante l'operazione;
- non scollegare fisicamente il dispositivo durante la modifica;
- controllare sempre il risultato prima di continuare con altre operazioni.

Il software viene fornito senza garanzie. L'autore non è responsabile per perdita di dati, danneggiamento dei filesystem, configurazioni errate o interruzioni dei servizi causate da un utilizzo improprio, da errori hardware o da modifiche non previste dell'ambiente ZimaOS.

L'utilizzo del software avviene sotto la piena responsabilità dell'utente.

## Autore

**Zima Storage Manager è stato creato da Alex Lignola.**

- GitHub: [AngoloInformatico](https://github.com/AngoloInformatico)
- YouTube: [Angolo Informatico](https://www.youtube.com/@AngoloInformatico)

## Licenza

Il progetto è distribuito con licenza **Apache License 2.0**.

Consulta [LICENSE](LICENSE) e [NOTICE](NOTICE). Le redistribuzioni e le opere derivate devono rispettare gli obblighi di licenza e conservare gli avvisi di attribuzione applicabili contenuti nel file `NOTICE`.
