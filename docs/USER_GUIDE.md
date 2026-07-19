# Guida utente — v3.0.0-rc10

## Accesso

Apri nel browser:

```text
http://IP_DEL_TUO_ZIMAOS:8787
```

Inserisci il codice di accesso configurato durante l'installazione.

## Scheda Dischi

Mostra i dispositivi realmente rilevati dal sistema.

Per rinominare un disco:

1. individua il disco usando nome, UUID, filesystem e percorso;
2. premi **Rinomina disco**;
3. inserisci il nuovo nome;
4. controlla attentamente il riepilogo;
5. conferma e attendi il completamento.

Il tool prova a mantenere coerenti:

- etichetta del filesystem;
- record nel database Local Storage;
- punto di montaggio;
- visualizzazione in ZimaOS.

Prima della modifica viene creato un backup di sicurezza.

## Scheda Backup

Permette di:

- creare un backup manuale;
- ripristinare un backup;
- eliminare un singolo backup;
- eliminare tutti i backup.

Il ripristino sostituisce il database Local Storage attivo. Leggi sempre la conferma prima di procedere.

## Scheda Cronologia

Mostra le operazioni eseguite dal tool.

Il pulsante **Svuota cronologia** elimina gli eventi registrati dopo una conferma obbligatoria.

## Scheda Diagnostica

Controlla:

- disponibilità del database;
- integrità SQLite;
- servizio Local Storage;
- dischi rilevati;
- mount e cartelle persistenti.

## Buone pratiche

- verifica sempre l'UUID prima di rinominare;
- non scollegare il disco durante la modifica;
- arresta le app che stanno usando il disco;
- conserva almeno un backup recente;
- non rinominare dischi di sistema o volumi critici;
- usa il pannello soltanto da LAN o VPN privata.
