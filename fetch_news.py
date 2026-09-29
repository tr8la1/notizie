#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime
import urllib.request
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

# Fonti RSS diversificate per garantire 6 fonti/domini differenti per topic
SOURCES = {
    "Nazionale": [
        "https://www.ansa.it/sito/ansait_rss.xml",
        "https://xml2.corriere.it/rss/homepage.xml",
        "https://www.repubblica.it/rss/homepage/rss2.0.xml",
        "https://www.tgcom24.mediaset.it/rss/homepage.xml",
        "https://www.ilfattoquotidiano.it/feed/",
        "https://www.agtw.it/rss/news.xml",
        "https://www.adnkronos.com/rss/ultimora.xml"
    ],
    "Internazionale": [
        "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.euronews.com/rss?format=xml",
        "https://www.repubblica.it/rss/esteri/rss2.0.xml",
        "https://www.corriere.it/rss/esteri.xml"
    ],
    "Tecnologia": [
        "https://www.wired.it/feed/rss",
        "https://www.tomshw.it/feed",
        "https://macitynet.it/feed/",
        "https://www.ansa.it/sito/notizie/tecnologia/tecnologia_rss.xml",
        "https://www.punto-informatico.it/feed/",
        "https://www.hdblog.it/feed/"
    ],
    "Soldi": [
        "https://www.ilsole24ore.com/rss/economia.xml",
        "https://www.milanofinanza.it/rss/rss_finanza.xml",
        "https://www.ansa.it/sito/notizie/economia/economia_rss.xml",
        "https://www.corriere.it/rss/economia.xml",
        "https://www.repubblica.it/rss/economia/rss2.0.xml",
        "https://www.wallstreetitalia.com/feed/"
    ],
    "Diplomazia": [
        "https://www.ispionline.it/it/rss",
        "https://it.insideover.com/feed",
        "https://www.affarainternazionali.it/feed/",
        "https://www.limesonline.com/feed",
        "https://www.geopolitica.info/feed/",
        "https://www.ansa.it/sito/notizie/politica/politica_rss.xml"
    ],
    "Local": [  # Esclusivamente fonti locali per Provincia e Città di Latina (LT)
        "https://www.latinatoday.it/rss",
        "https://www.latinaoggi.eu/rss",
        "https://www.ilmessaggero.it/rss/latina.xml",
        "https://www.h24notizie.com/feed/",
        "https://www.latinacorriere.it/feed/",
        "https://www.lunanotizie.it/site/feed/"
    ]
}

ARCHIVE_FILE = "archive.json"
HTML_OUTPUT = "notizie.html"

def clean_html_tags(raw_text):
    """Rimuove tag HTML residui da descrizioni o titoli RSS."""
    if not raw_text:
        return ""
    clean = re.sub(r'<[^>]+>', '', raw_text)
    return clean.strip().replace('\n', ' ')

def get_domain_key(url):
    """Estrae il dominio di base per evitare di usare la stessa fonte più di una volta per topic."""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc

def fetch_feed_items(url, max_items=2):
    """Scarica ed estrae notizie da un feed RSS."""
    items = []
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            channel = root.find('channel')
            elements = channel.findall('item') if channel is not None else root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for elem in elements:
                title_elem = elem.find('title') if elem.find('title') is not None else elem.find('{http://www.w3.org/2005/Atom}title')
                link_elem = elem.find('link') if elem.find('link') is not None else elem.find('{http://www.w3.org/2005/Atom}link')
                desc_elem = elem.find('description') if elem.find('description') is not None else elem.find('{http://www.w3.org/2005/Atom}summary')
                
                title = clean_html_tags(title_elem.text) if title_elem is not None and title_elem.text else ""
                
                if link_elem is not None:
                    link = link_elem.text if link_elem.text else link_elem.attrib.get('href', '#')
                else:
                    link = '#'
                
                summary = clean_html_tags(desc_elem.text) if desc_elem is not None and desc_elem.text else ""
                if len(summary) > 130:
                    summary = summary[:127] + "..."
                
                if title and link != '#':
                    items.append({
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "domain": get_domain_key(link)
                    })
                if len(items) >= max_items:
                    break
    except Exception as e:
        print(f"[-] Errore su feed {url}: {e}")
    return items

def get_daily_news():
    """Raccoglie 6 notizie per ciascuno dei 6 topic (max 1 per fonte/dominio)."""
    today_news = {}
    for topic, urls in SOURCES.items():
        topic_articles = []
        seen_domains = set()
        seen_titles = set()
        
        for url in urls:
            fetched = fetch_feed_items(url, max_items=2)
            for item in fetched:
                domain = item['domain']
                norm_title = item['title'].lower()
                
                # REGOLA: Max 1 notizia per dominio/fonte per ciascun topic
                if domain not in seen_domains and norm_title not in seen_titles:
                    seen_domains.add(domain)
                    seen_titles.add(norm_title)
                    topic_articles.append(item)
                    
                if len(topic_articles) == 6:
                    break
            if len(topic_articles) == 6:
                break
                
        # Se i feed non bastano, riempie fino a 6
        while len(topic_articles) < 6:
            idx = len(topic_articles) + 1
            topic_articles.append({
                "title": f"Notizia {idx} - {topic}",
                "summary": "Aggiornamento in attesa di sincronizzazione.",
                "link": "https://www.ansa.it",
                "domain": "ansa.it"
            })
            
        today_news[topic] = topic_articles[:6]
    return today_news

def build_html_canvas(archive_data):
    """Genera l'HTML e-ink ottimizzato per smartphone con hyperlink visibili."""
    
    archive_json_str = json.dumps(archive_data, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>News 'trottolose' quotidiane</title>
    <style>
        :root {{
            --bg-paper: #f4f1ea;
            --text-ink: #111111;
            --border-ink: #222222;
            --muted-ink: #444444;
            --active-bg: #111111;
            --active-text: #f4f1ea;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}

        body {{
            background-color: var(--bg-paper);
            color: var(--text-ink);
            font-family: -apple-system, BlinkMacSystemFont, "Georgia", "Segoe UI", serif;
            padding: 0.8rem 0.5rem;
            display: flex;
            justify-content: center;
        }}

        /* Contenitore ottimizzato per mobile/e-reader */
        .ebook-container {{
            width: 100%;
            max-width: 600px;
            background-color: var(--bg-paper);
            border: 2px solid var(--border-ink);
            padding: 1rem 0.8rem;
            border-radius: 3px;
        }}

        /* Prima Riga: Titolo + Dropdown Data */
        .header-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-ink);
            padding-bottom: 0.8rem;
            margin-bottom: 0.8rem;
            gap: 0.5rem;
        }}

        .title {{
            font-size: 1.15rem;
            font-weight: bold;
            letter-spacing: -0.3px;
            line-height: 1.2;
        }}

        .date-select {{
            background: var(--bg-paper);
            color: var(--text-ink);
            border: 1.5px solid var(--border-ink);
            font-family: inherit;
            font-size: 0.85rem;
            font-weight: bold;
            padding: 0.3rem 0.4rem;
            border-radius: 2px;
            cursor: pointer;
        }}

        /* Seconda Riga: Topic Selezionabili (Responsive Grid) */
        .topics-row {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.4rem;
            border-bottom: 1.5px solid var(--border-ink);
            padding-bottom: 0.8rem;
            margin-bottom: 1rem;
        }}

        .topic-btn {{
            background: transparent;
            color: var(--text-ink);
            border: 1px solid var(--border-ink);
            padding: 0.5rem 0.2rem;
            font-family: inherit;
            font-size: 0.8rem;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            border-radius: 2px;
            min-height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .topic-btn.active {{
            background: var(--active-bg);
            color: var(--active-text);
        }}

        /* Elenco Notizie */
        .news-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .news-item {{
            border-bottom: 1px dashed var(--border-ink);
            padding-bottom: 0.8rem;
        }}

        .news-item:last-child {{
            border-bottom: none;
        }}

        .news-title {{
            font-size: 0.98rem;
            font-weight: 700;
            line-height: 1.3;
            margin-bottom: 0.3rem;
        }}

        .news-summary {{
            font-size: 0.88rem;
            color: var(--muted-ink);
            line-height: 1.35;
            margin-bottom: 0.4rem;
        }}

        /* Hyperlink diretto visibile e sottolineato */
        .news-link {{
            display: inline-block;
            color: var(--text-ink);
            font-size: 0.82rem;
            font-weight: 600;
            text-decoration: underline;
            word-break: break-all;
            line-height: 1.2;
            margin-top: 0.1rem;
        }}

        .news-link:active {{
            background-color: var(--text-ink);
            color: var(--bg-paper);
        }}

        footer {{
            margin-top: 1.5rem;
            padding-top: 0.8rem;
            border-top: 1px solid var(--border-ink);
            text-align: center;
            font-size: 0.7rem;
            color: var(--muted-ink);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    </style>
</head>
<body>

<div class="ebook-container">
    <!-- Prima Riga: Titolo e Menu Date -->
    <div class="header-row">
        <h1 class="title">News 'trottolose' quotidiane</h1>
        <select id="dateSelect" class="date-select" onchange="onDateChange()"></select>
    </div>

    <!-- Seconda Riga: Topic Selezionabili -->
    <div class="topics-row" id="topicsContainer"></div>

    <!-- Elenco delle 6 Notizie -->
    <div class="news-list" id="newsContainer"></div>

    <footer>Paper Reader • 6 Notizie per Topic</footer>
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

        dateSelect.innerHTML = "";
        dates.forEach(date => {{
            const opt = document.createElement('option');
            opt.value = date;
            opt.textContent = date;
            dateSelect.appendChild(opt);
        }});

        currentDate = dates[0];
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
            
            // Hyperlink diretto visibile
            const displayUrl = item.link;

            card.innerHTML = `
                <div class="news-title">${{index + 1}}. ${{item.title}}</div>
                <div class="news-summary">${{item.summary}}</div>
                <a href="${{item.link}}" class="news-link" target="_blank" rel="noopener">${{displayUrl}}</a>
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
    print(f"[*] Recupero notizie per il {today_str}...")

    archive_data = {}
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                archive_data = json.load(f)
        except Exception as e:
            print(f"[!] Errore lettura {ARCHIVE_FILE}: {e}")

    new_daily_news = get_daily_news()
    archive_data[today_str] = new_daily_news

    with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(archive_data, f, ensure_ascii=False, indent=2)

    html_code = build_html_canvas(archive_data)
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_code)
        
    print(f"[+] Aggiornamento completato con successo!")

if __name__ == "__main__":
    main()