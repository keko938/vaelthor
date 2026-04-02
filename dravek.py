import os
import json
import time
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "ranktuga-21")
DATA_FILE = "dravek_data.json"

# RSS feeds de bestsellers da Amazon.es por categoria
CATEGORY_FEEDS = {
    "Air Fryers": "https://www.amazon.es/gp/bestsellers/kitchen/3638504031/ref=zg_bs_pg_1_kitchen?ie=UTF8&pg=1",
    "Aspiradores Robo": "https://www.amazon.es/gp/bestsellers/kitchen/3638455031/ref=zg_bs_pg_1?ie=UTF8&pg=1",
    "Robots de Cozinha": "https://www.amazon.es/gp/bestsellers/kitchen/3638552031/ref=zg_bs_pg_1?ie=UTF8&pg=1",
    "Produtos para Bebe": "https://www.amazon.es/gp/bestsellers/baby/ref=zg_bs_baby_sm?ie=UTF8&pg=1",
    "Racoes para Animais": "https://www.amazon.es/gp/bestsellers/pet-supplies/ref=zg_bs_pet-supplies_sm?ie=UTF8&pg=1"
}

# Keywords de pesquisa para cada categoria (fallback)
CATEGORY_SEARCH = {
    "Air Fryers": "air+fryer",
    "Aspiradores Robo": "aspiradora+robot",
    "Robots de Cozinha": "robot+cocina+multifuncion",
    "Produtos para Bebe": "productos+bebe+recien+nacido",
    "Racoes para Animais": "pienso+perros+gatos"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,pt;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def scrape_bestsellers(category_name, url):
    """Extrai bestsellers da página da Amazon."""
    import re
    try:
        session = requests.Session()
        # Cookie inicial
        session.get("https://www.amazon.es", headers=HEADERS, timeout=10)
        time.sleep(random.uniform(2, 4))

        response = session.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return []

        html = response.text
        products = []

        # Extrai ASINs da página de bestsellers
        asins = list(dict.fromkeys(re.findall(r'data-asin="([A-Z0-9]{10})"', html)))

        # Extrai títulos
        titles = re.findall(
            r'<div class="p13n-sc-truncate[^"]*"[^>]*>\s*(.*?)\s*</div>',
            html, re.DOTALL
        )
        titles = [re.sub(r'<[^>]+>', '', t).strip() for t in titles if t.strip()]

        # Extrai preços
        prices = re.findall(r'<span class="p13n-sc-price">(.*?)</span>', html)

        # Extrai avaliações
        ratings = re.findall(r'(\d+[,.]\d+)\s*de\s*5', html)

        for i, asin in enumerate(asins[:20]):
            title = titles[i] if i < len(titles) else f"Produto #{i+1}"
            price = prices[i].strip() if i < len(prices) else "N/D"
            rating = ratings[i] if i < len(ratings) else "N/D"

            products.append({
                "rank": i + 1,
                "asin": asin,
                "title": title[:80],
                "price": price,
                "rating": rating,
                "url": f"https://www.amazon.es/dp/{asin}?tag={AFFILIATE_ID}",
                "category": category_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Amazon Bestsellers"
            })

        return products

    except Exception as e:
        print(f"Erro bestsellers {category_name}: {e}")
        return []

def search_fallback(category_name, keyword):
    """Pesquisa alternativa se bestsellers falhar."""
    import re
    try:
        url = f"https://www.amazon.es/s?k={keyword}&tag={AFFILIATE_ID}"
        session = requests.Session()
        session.get("https://www.amazon.es", headers=HEADERS, timeout=10)
        time.sleep(random.uniform(2, 4))

        response = session.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return []

        html = response.text
        asins = list(dict.fromkeys(re.findall(r'data-asin="([A-Z0-9]{10})"', html)))

        titles = []
        for pattern in [
            r'<span class="a-size-medium a-color-base a-text-normal">(.*?)</span>',
            r'<span class="a-size-base-plus a-color-base a-text-normal">(.*?)</span>',
        ]:
            found = re.findall(pattern, html)
            if found:
                titles = [re.sub(r'<[^>]+>', '', t).strip() for t in found]
                break

        price_wholes = re.findall(r'<span class="a-price-whole">(\d+)', html)
        price_decs = re.findall(r'<span class="a-price-decimal"[^>]*>(\d+)', html)
        prices = [
            f"{price_wholes[i]},{price_decs[i] if i < len(price_decs) else '00'}€"
            for i in range(len(price_wholes))
        ]
        ratings = re.findall(r'(\d+[,.]\d+)\s*de\s*5\s*estrellas?', html)

        products = []
        for i, asin in enumerate(asins[:20]):
            products.append({
                "rank": i + 1,
                "asin": asin,
                "title": (titles[i] if i < len(titles) else f"Produto {asin}")[:80],
                "price": prices[i] if i < len(prices) else "N/D",
                "rating": ratings[i] if i < len(ratings) else "N/D",
                "url": f"https://www.amazon.es/dp/{asin}?tag={AFFILIATE_ID}",
                "category": category_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Amazon Search"
            })

        return products

    except Exception as e:
        print(f"Erro fallback {category_name}: {e}")
        return []

def run_all():
    print(f"Dravek v5 a pesquisar... {datetime.now()}")
    previous = load_data()
    current = {}
    total = 0

    for category, url in CATEGORY_FEEDS.items():
        print(f"  -> {category} (bestsellers)...")
        products = scrape_bestsellers(category, url)

        # Se bestsellers falhar, tenta pesquisa normal
        if not products:
            print(f"     Bestsellers falhou, a tentar pesquisa...")
            keyword = CATEGORY_SEARCH.get(category, category)
            products = search_fallback(category, keyword)

        current[category] = products
        total += len(products)
        status = "OK" if products else "SEM DADOS"
        print(f"     {status}: {len(products)} produtos")
        time.sleep(random.uniform(6, 12))

    save_data(current)
    print(f"Dravek v5 concluiu. Total: {total}")
    return current, previous, total

def run_category(name):
    url = CATEGORY_FEEDS.get(name)
    keyword = CATEGORY_SEARCH.get(name, name)
    if url:
        products = scrape_bestsellers(name, url)
        if products:
            return products
    return search_fallback(name, keyword)

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro guardar: {e}")

def format_report(current, previous, total):
    now = datetime.now().strftime("%d/%m %H:%M")
    lines = [f"*Dravek v5 — Amazon Bestsellers ES | {now}*\n"]

    if total == 0:
        lines.append(
            "Sem dados — Amazon bloqueou todas as pesquisas.\n"
            "Isto e normal em servidores partilhados.\n"
            "Os dados serao obtidos quando o bloqueio levantar."
        )
        return "\n".join(lines)

    lines.append(f"Total encontrado: *{total} produtos*\n")

    for category, products in current.items():
        if not products:
            lines.append(f"\n *{category}* — Bloqueado")
            continue

        prev_asins = {p["asin"] for p in previous.get(category, [])}
        new = [p for p in products if p["asin"] not in prev_asins]
        new_tag = f" +{len(new)} novos" if new and previous else ""
        source = products[0].get("source", "Amazon") if products else ""

        lines.append(f"\n*{category}* ({len(products)}) {new_tag}")
        lines.append(f"_Fonte: {source}_")
        for p in products[:5]:
            stars = f"  {p['rating']}" if p['rating'] != 'N/D' else ""
            lines.append(f"  {p['rank']}. {p['title'][:40]}... {p['price']}{stars}")

    return "\n".join(lines)

def get_context():
    data = load_data()
    total = sum(len(v) for v in data.values())
    if not data or total == 0:
        return "Sem dados do Dravek ainda."
    context = f"Dravek tem {total} produtos em base de dados:\n"
    for cat, products in data.items():
        if products:
            top3 = ", ".join([p['title'][:30] for p in products[:3]])
            context += f"- {cat}: {top3}...\n"
    return context
