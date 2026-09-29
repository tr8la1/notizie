News 'trottolose' quotidiane 📖📰

News 'trottolose' quotidiane è un'applicazione web minimale, automatizzata ed essenziale per la lettura delle notizie del giorno, progettata con un'estetica ispirata ai lettori e-book con schermo e-paper / paper reader.

L'applicazione raccoglie ogni giorno 6 notizie esclusive per 6 differenti macro-categorie, preservando l'archivio dei giorni precedenti e garantendo un'esperienza di lettura pulita, leggibile e priva di distrazioni.

🌟 Caratteristiche Principali

🎨 Design Minimal E-Ink / Paper:

Tavolozza di soli 2-3 colori ad alto contrasto per simulare l'esperienza visiva degli e-reader (Inchiostro su carta / E-Paper).

Ottimizzazione responsive completa per schermi di smartphone, tablet e desktop.

📅 Archivio e Navigazione delle Date:

Prima riga con Titolo principale e menù a tendina sulla destra per la selezione della data di riferimento.

Storico dei giorni precedenti preservato in automatico senza sovrascritture.

🗂️ 6 Topic Selezionabili:

Nazionale (Notizie dall'Italia - escluse fonti locali)

Internazionale (Esteri e notizie dal mondo)

Tecnologia (Informatica, scienza, innovazione e mobile)

Soldi (Economia, finanza e mercati)

Diplomazia (Geopolitica, relazioni internazionali e trattati)

Local (Topic speciale riservato esclusivamente alla Città e Provincia di Latina - LT)

🔗 Trasparenza e Fonti Dirette:

Exact 6 notizie uniche per topic per ciascuna data.

Nessuna duplicazione di notizie o fonti nel medesimo tema.

Hyperlink diretto e visibile all'articolo originale della fonte giornalistica.

🛠️ Architettura e Automazione

Il progetto si aggiorna automaticamente ogni giorno alle 07:00 AM (ora italiana) grazie a GitHub Actions ed è servito via GitHub Pages.

┌────────────────────────┐      ┌─────────────────────────┐      ┌────────────────────────┐
│  GitHub Actions (CRON) │ ───> │     fetch_news.py       │ ───> │      archive.json      │
│  (Ogni giorno ore 7)   │      │ (Fetch RSS e Deduplica) │      │ (Preserva lo storico)  │
└────────────────────────┘      └─────────────────────────┘      └────────────────────────┘
                                                                             │
                                                                             ▼
                                                                 ┌────────────────────────┐
                                                                 │      notizie.html      │
                                                                 │  (Interfaccia E-Paper) │
                                                                 └────────────────────────┘


fetch_news.py: Script Python che estrae le notizie via feed RSS autorevoli (ANSA, Il Sole 24 Ore, Corriere, Wired, LatinaToday, Latina Oggi, ecc.), garantendo la regola di massimo 1 articolo per fonte/dominio all'interno dello stesso topic.

archive.json: Database JSON leggero che accumula lo storico dei giorni.

.github/workflows/daily_news.yml: Automazione GitHub che esegue lo script, salva i dati e aggiorna la pagina web.

🚀 Struttura del Repository

notizie/
├── .github/workflows/
│   └── daily_news.yml      # Workflow di automazione giornaliera
├── fetch_news.py           # Script Python di aggregazione e generazione HTML
├── archive.json            # Archivio storico dati in formato JSON
├── notizie.html            # Interfaccia grafica HTML/CSS/JS E-Ink
└── README.md               # Documentazione di progetto


📄 Licenza

Distribuito sotto licenza MIT. Sentiti libero di riutilizzare il codice per progetti personali.
