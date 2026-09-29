#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET

# Architettura delle fonti RSS esclusive per categoria (no news locali nei primi 5)
SOURCES = {
    "Nazionale": [
        "https://www.ansa.it/sito/ansait_rss.xml",
        "https://xml2.corriere.it/rss/homepage.xml",
        "https://www.tgcom24.mediaset.it/rss/homepage.xml"
    ],
    "Internazionale": [
        "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
    ],
    "Tecnologia": [
        "https://www.wired.it/feed/rss",
        "https://www.tomshw.it/feed",
        "https://macitynet.it/feed/"
    ],
    "Soldi": [
        "https://www.ilsole24ore.com/rss/economia.xml",
        "https://www.ilsole24ore.com/rss/finanza.xml",
        "https://www.milanofinanza.it/rss/rss_finanza.xml"
    ],
    "Diplomazia": [
        "https://www.ispionline.it/it/rss",
        "https://it.insideover.com/feed",
        "https://www.affarainternazionali.it/feed/"
    ],
    "Local": [  # Esclusivamente Provincia e Città di Latina (LT)
        "https://www.latinatoday.it/rss",
        "https://www.latinaoggi.eu/rss",
        "https://www.ilmessaggero.it/rss/latina.xml"
    ]
}

ARCHIVE_FILE = "archive.json"
HTML_OUTPUT = "notizie.html"

def clean_html_tags(raw_text):
    """Rimuove eventuali tag HTML dalle descrizioni o titoli RSS."""
    if not raw_text:
        return ""
    clean = re.sub(r'<[^>]+>', '', raw_text)
    return clean.strip().replace('\n', ' ')

def fetch_feed_items(url, max_items=6):
    """Scarica ed estrae titolo, link e sintesi da un feed RSS."""
    items = []
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Supporto standard RSS 2.0 e Atom
            channel = root.find('channel')
            elements = channel.findall('item') if channel is not None else root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for elem in elements:
                title_elem = elem.find('title') if elem.find('title') is not None else elem.find('{http://www.w3.org/2005/Atom}title')
                link_elem = elem.find('link') if elem.find('link') is not None else elem.find('{http://www.w3.org/2005/Atom}link')
                desc_elem = elem.find('description') if elem.find('description') is not None else elem.find('{http://www.w3.org/2005/Atom}summary')
                
                title = clean_html_tags(title_elem.text) if title_elem is not None and title_elem.text else ""
                
                # Estrazione link
                if link_elem is not None:
                    link = link_elem.text if link_elem.text else link_elem.attrib.get('href', '#')
                else:
                    link = '#'
                
                summary = clean_html_tags(desc_elem.text) if desc_elem is not None and desc_elem.text else ""
                if len(summary) > 140:
                    summary = summary[:137] + "..."
                
                if title and link != '#':
                    items.append({
                        "title": title,
                        "summary": summary,
                        "link": link
                    })
                if len(items) >= max_items:
                    break
    except Exception as e:
        print(f"[-] Errore nel recupero feed da {url}: {e}")
    return items

def get_daily_news():
    """Raccoglie 6 notizie per ciascuno dei 6 topic."""
    today_news = {}
    for topic, urls in SOURCES.items():
        topic_articles = []
        seen_titles = set()
        
        for url in urls:
            fetched = fetch_feed_items(url, max_items=6)
            for item in fetched:
                # Evita notizie duplicate confrontando i titoli
                norm_title = item['title'].lower()
                if norm_title not in seen_titles:
                    seen_titles.add(norm_title)
                    topic_articles.append(item)
                if len(topic_articles) == 6:
                    break
            if len(topic_articles) == 6:
                break
                
        # Se la fonte RSS non fornisce 6 notizie, riempie i segnaposto in modo fluido
        while len(topic_articles) < 6:
            idx = len(topic_articles) + 1
            topic_articles.append({
                "title": f"Notizia {idx} - {topic}",
                "summary": "Aggiornamento in attesa di sincro dal feed principale.",
                "link": "https://www.ansa.it"
            })
            
        today_news[topic] = topic_articles
    return today_news

def build_html_canvas(archive_data):
    """Genera il codice HTML responsive con stile e-ink e selettore data/topic."""
    
    archive_json_str = json.dumps(archive_data, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News 'trottolose' quotidiane</title>
    <style>
        :root {{
            --bg-paper: #f4f1ea;
            --text-ink: #111111;
            --border-ink: #222222;
            --muted-ink: #555555;
            --active-bg: #111111;
            --active-text: #f4f1ea;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-paper);
            color: var(--text-ink);
            font-family: "Georgia", "Merriweather", "Times New Roman", serif;
            padding: 2rem 1rem;
            display: flex;
            justify-content: center;
        }}

        .ebook-container {{
            width: 100%;
            max-width: 680px;
            background-color: var(--bg-paper);
            border: 2px solid var(--border-ink);
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border-radius: 4px;
        }}

        /* Prima Riga: Titolo + Dropdown Data */
        .header-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-ink);
            padding-bottom: 1rem;
            margin-bottom: 1.2rem;
            gap: 1rem;
        }}

        .title {{
            font-size: 1.4rem;
            font-weight: bold;
            letter-spacing: -0.5px;
        }}

        .date-select {{
            background: var(--bg-paper);
            color: var(--text-ink);
            border: 1px solid var(--border-ink);
            font-family: inherit;
            font-size: 0.95rem;
            padding: 0.3rem 0.5rem;
            border-radius: 2px;
            cursor: pointer;
        }}

        /* Seconda Riga: Topic Selezionabili */
        .topics-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            border-bottom: 1px solid var(--border-ink);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }}

        .topic-btn {{
            background: transparent;
            color: var(--text-ink);
            border: 1px solid var(--border-ink);
            padding: 0.4rem 0.7rem;
            font-family: inherit;
            font-size: 0.85rem;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-radius: 2px;
            transition: all 0.1s ease;
        }}

        .topic-btn.active {{
            background: var(--active-bg);
            color: var(--active-text);
        }}

        /* Sezione Notizie */
        .news-list {{
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }}

        .news-item {{
            border-bottom: 1px dashed var(--border-ink);
            padding-bottom: 1rem;
        }}

        .news-item:last-child {{
            border-bottom: none;
        }}

        .news-header {{
            font-size: 1.05rem;
            font-weight: bold;
            line-height: 1.35;
            margin-bottom: 0.4rem;
        }}

        .news-summary {{
            font-size: 0.9rem;
            color: var(--muted-ink);
            line-height: 1.4;
            margin-bottom: 0.5rem;
        }}

        .news-link {{
            display: inline-block;
            color: var(--text-ink);
            font-size: 0.85rem;
            font-weight: bold;
            text-decoration: underline;
        }}

        .news-link:hover {{
            background-color: var(--text-ink);
            color: var(--bg-paper);
        }}

        footer {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-ink);
            text-align: center;
            font-size: 0.75rem;
            color: var(--muted-ink);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
    </style>
</head>
<body>

<div class="ebook-container">
    <!-- Prima Riga: Titolo & Menù a tendina date -->
    <div class="header-row">
        <h1 class="title">News 'trottolose' quotidiane</h1>
        <select id="dateSelect" class="date-select" onchange="onDateChange()"></select>
    </div>

    <!-- Seconda Riga: 6 Topic Selezionabili -->
    <div class="topics-row" id="topicsContainer"></div>

    <!-- Elenco delle 6 Notizie -->
    <div class="news-list" id="newsContainer"></div>

    <footer>E-Ink Reader • Archivio Quotidiano Automobilizzato</footer>
</div>

<script>
    const archive = {archive_json_str};
    let currentDate = "";
    let currentTopic = "Nazionale";

    const dateSelect = document.getElementById('dateSelect');
    const topicsContainer = document.getElementById('topicsContainer');
    const newsContainer = document.getElementById('newsContainer');

    function init() {{
        const dates = Object.keys(archive).reverse();
        if (dates.length === 0) return;

        // Popola il menu a tendina delle date
        dateSelect.innerHTML = "";
        dates.forEach(date => {{
            const opt = document.createElement('option');
            opt.value = date;
            opt.textContent = date;
            dateSelect.appendChild(opt);
        }});

        currentDate = dates[0]; // La data più recente
        renderTopics();
        renderNews();
    }}

    function renderTopics() {{
        const topics = Object.keys(archive[currentDate] || {{}});
        topicsContainer.innerHTML = "";

        topics.forEach(topic => {{
            const btn = document.createElement('button');
            btn.className = `topic-btn ${{topic === currentTopic ? 'active' : ''}}`;
            btn.textContent = topic;
            btn.onclick = () => {{
                currentTopic = topic;
                renderTopics();
                renderNews();
            }};
            topicsContainer.appendChild(btn);
        }});
    }}

    function renderNews() {{
        newsContainer.innerHTML = "";
        const articles = archive[currentDate]?.[currentTopic] || [];

        articles.forEach((item, index) => {{
            const card = document.createElement('article');
            card.className = "news-item";
            card.innerHTML = `
                <div class="news-header">${{index + 1}}. ${{item.title}}</div>
                <div class="news-summary">${{item.summary}}</div>
                <a href="${{item.link}}" class="news-link" target="_blank" rel="noopener">Leggi articolo originale →</a>
            `;
            newsContainer.appendChild(card);
        }});
    }}

    function onDateChange() {{
        currentDate = dateSelect.value;
        renderTopics();
        renderNews();
    }}

    document.addEventListener("DOMContentLoaded", init);
</script>

</body>
</html>
"""
    return html_content

def main():
    today_str = datetime.now().strftime("%d/%m/%Y")
    print(f"[*] Avvio aggiornamento notizie per il {today_str}...")

    # Carica l'archivio esistente per non perdere i giorni precedenti
    archive_data = {}
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                archive_data = json.load(f)
        except Exception as e:
            print(f"[!] Errore nella lettura di {ARCHIVE_FILE}: {e}")

    # Recupera le nuove notizie
    new_daily_news = get_daily_news()
    archive_data[today_str] = new_daily_news

    # Salva il file JSON aggiornato
    with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(archive_data, f, ensure_ascii=False, indent=2)
    print(f"[+] {ARCHIVE_FILE} aggiornato correttamente.")

    # Rigenera il file HTML
    html_code = build_html_canvas(archive_data)
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_code)
    print(f"[+] {HTML_OUTPUT} generato con successo!")

if __name__ == "__main__":
    main()