# Foresight Facilitator

Interfaccia agente per sessioni di **Strategic Foresight** con facilitazione AI in tempo reale.

## Funzionalità

- **Horizon Scanning** — i partecipanti votano (ranking) trend e fenomeni in modo individuale
- **Dashboard Facilitatore** — monitoraggio live dei voti, approvazione fenomeni aggiunti dai partecipanti
- **Transizione** — selezione dei 2 driver principali, definizione assi, creazione gruppi
- **Scenario Planning** — l'agente AI guida ogni gruppo (4 persone) attraverso la costruzione dello scenario
- **Report finale** — export HTML/PDF con tutti gli scenari, minacce e opportunità

## Stack

- [Next.js 16](https://nextjs.org/) + TypeScript + Tailwind CSS
- [Socket.io](https://socket.io/) per comunicazione in tempo reale
- [Prisma](https://prisma.io/) + SQLite come database
- [Claude API (Anthropic)](https://anthropic.com/) per l'agente AI

## Setup

### 1. Clona il repository

```bash
git clone https://github.com/tuo-username/foresight-facilitator.git
cd foresight-facilitator
```

### 2. Installa le dipendenze

```bash
npm install
```

### 3. Configura le variabili d'ambiente

```bash
cp .env.example .env
```

Apri `.env` e inserisci la tua API key di Anthropic:

```
ANTHROPIC_API_KEY="sk-ant-..."
DATABASE_URL="file:./prisma/dev.db"
```

### 4. Inizializza il database

```bash
npx prisma migrate dev
```

### 5. Avvia il server

```bash
npm run dev
```

L'app sarà disponibile su [http://localhost:3000](http://localhost:3000).

## Struttura sessione

```
Setup Facilitatore
  → Crea sessione (domanda di ricerca, orizzonte temporale, fenomeni, key points)
  → Condivide il codice sessione con i partecipanti

Fase 1: Horizon Scanning (individuale)
  → I partecipanti accedono con il codice e il proprio nome
  → Ordinano i fenomeni per priorità (drag & drop)
  → Possono aggiungere nuovi fenomeni
  → Il facilitatore vede il ranking aggregato in tempo reale

Transizione
  → Il facilitatore seleziona i 2 driver principali
  → Definisce le polarità degli assi
  → Assegna i partecipanti ai 4 gruppi

Fase 2: Scenario Planning (gruppi di 4)
  → L'agente AI introduce il quadrante e guida il gruppo
  → Esplora i key points, genera narrativa, raccoglie titolo, minacce e opportunità
  → Il facilitatore monitora l'avanzamento di tutti i gruppi

Output finale
  → Report con i 4 scenari completi
  → Dashboard con matrice 2x2
```

## Licenza

MIT
