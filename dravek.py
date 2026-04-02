import os
import json
import time
import random
import requests
import re
from datetime import datetime

AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "ranktuga-21")
DATA_FILE = "dravek_data.json"

CATEGORY_FEEDS = {
    "Air Fryers": "https://www.amazon.es/gp/bestsellers/kitchen/3638504031/ref=zg_bs_pg_1?ie=UTF8&pg=1",
    "Aspiradores Robo": "https://www.amazon.es/gp/bestsellers/kitchen/3638455031/ref=zg_bs_pg_1?ie=UTF8&pg=1",
    "Robots de Cozinha": "https://www.amazon.es/gp/bestsellers/kitchen/3638552031/ref=zg_bs_pg_1?ie=UTF8&pg=1",
    "Produtos para Bebe": "https://www.amazon.es/gp/bestsellers/baby/ref=zg_bs_baby_sm?ie=UTF8&pg=1",
    "Racoes para Animais": "https://www.amazon.es/gp/bestsellers/pet-supplies/ref=zg_bs_pet-supplies_sm?ie=UTF8&pg=1"
}

CATEGORY_SEARCH = {
    "Air Fryers": "air+fryer",
    "Aspiradores Robo": "aspiradora+robot",
    "Robots de Cozinha": "robot+cocina+multifuncion",
    "Produtos para Bebe": "productos+bebe",
    "Racoes para Animais": "pienso+perros+gatos"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "es-ES,es;q=0.9,pt;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def extract_titles(html):
    """Tenta múltiplos padrões para extrair títulos — Amazon muda os seletores frequentemente."""
    titles = []

    patterns = [
        # Padrão atual bestsellers 2024/2025
        r'class="[^"]*p13n-sc-css-line-clamp[^"]*"[^>]*>\s*(.*?)\s*</span>',
        # Padrão alternativo
        r'class="[^"]*p13n-sc-truncate[^"]*"[^>]*>\s*(.*?)\s*</div>',
        # aria-label dos links de produto
        r'<a[^>]+class="[^"]*a-link-normal[^"]*"[^>]+aria-label="([^"]{10,150})"',
        # Alt text das imagens de produto
        r'<img[^>]+alt="([^"]{10,150})"[^>]+class="[^"]*p13n[^"]*"',
        # Títulos em spans genéricos dentro de células de bestsellers
        r'<span[^>]+class="[^"]*a-size-small[^"]*"[^>]*>(.*?)</span>',
        # JSON-LD structured data
        r'"name"\s*:\s*"([^"]{10,150})"',
    ]

    for pattern in patterns:
        found = re.findall(pattern, html, re.DOTALL)
        found = [re.sub(r'<[^>]+>', '', t).strip() for t in found]
        found = [t for t in found if 10 < len(t) < 200 and not t.startswith('{')]
        if len(found) >= 3:
            titles = found
            break

    return titles

def extract_prices(html):
    """Extrai preços do HTML."""
    prices = []

    # Preços em páginas de bestsellers
    patterns = [
        r'<span class="p13n-sc-price">(.*?)</span>',
        r'<span class="a-price-whole">(\d+)',
    ]

    for pattern in patterns:
        found = re.findall(pattern, html)
        if found:
            prices = [re.sub(r'<[^>]+>', '', p).strip() for p in found]
            break

    return prices

def extract_ratings(html):
    """Extrai avaliações do HTML."""
    ratings = re.findall(r'(\d+[,.]\d+)\s*de\s*5', html)
    return ratings

def scrape_page(category_name, url):
    """Faz scraping de uma página Amazon."""
    try:
        session = requests.Session()
        session.get("https://www.amazon.es", headers=get_headers(), timeout=10)
        time.sleep(random.uniform(2, 4))

        response = session.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            print(f"  Status {response.status_code} para {category_name}")
            return []

        html = response.text

        # Verifica se foi bloqueado (CAPTCHA)
        if "robot" in html.lower() or "captcha" in html.lower():
            print(f"  CAPTCHA detetado para {category_name}")
            return []

        asins = list(dict.fromkeys([
            a for a in re.findall(r'data-asin="([A-Z0-9]{10})"', html) if a
        ]))

        if not asins:
            print(f"  Sem ASINs para {category_name}")
            return []

        titles = extract_titles(html)
        prices = extract_prices(html)
        ratings = extract_ratings(html)

        products = []
        for i, asin in enumerate(asins[:20]):
            title = titles[i] if i < len(titles) else None
            # Se não temos título, tenta buscar da página individual
            if not title or len(title) < 5:
                title = f"Ver produto {asin}"

            products.append({
                "rank": i + 1,
                "asin": asin,
                "title": title[:100],
                "price": prices[i] if i < len(prices) else "N/D",
                "rating": ratings[i] if i < len(ratings) else "N/D",
                "url": f"https://www.amazon.es/dp/{asin}?tag={AFFILIATE_ID}",
                "category": category_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Amazon Bestsellers"
            })

        return products

    except Exception as e:
        print(f"  Erro scraping {category_name}: {e}")
        return []

def search_fallback(category_name, keyword):
    """Pesquisa alternativa por palavra-chave."""
    try:
        url = f"https://www.amazon.es/s?k={keyword}&tag={AFFILIATE_ID}"
        session = requests.Session()
        session.get("https://www.amazon.es", headers=get_headers(), timeout=10)
        time.sleep(random.uniform(2, 4))

        response = session.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return []

        html = response.text

        if "robot" in html.lower() or "captcha" in html.lower():
            return []

        asins = list(dict.fromkeys([
            a for a in re.findall(r'data-asin="([A-Z0-9]{10})"', html) if a
        ]))

        # Títulos de páginas de pesquisa (seletores diferentes)
        titles = []
        for pattern in [
            r'<span class="a-size-medium a-color-base a-text-normal">(.*?)</span>',
            r'<span class="a-size-base-plus a-color-base a-text-normal">(.*?)</span>',
            r'<h2[^>]*><a[^>]*><span>(.*?)</span>',
        ]:
            found = re.findall(pattern, html, re.DOTALL)
            found = [re.sub(r'<[^>]+>', '', t).strip() for t in found if t.strip()]
            if len(found) >= 3:
                titles = found
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
                "title": (titles[i] if i < len(titles) else f"Produto {asin}")[:100],
                "price": prices[i] if i < len(prices) else "N/D",
                "rating": ratings[i] if i < len(ratings) else "N/D",
                "url": f"https://www.amazon.es/dp/{asin}?tag={AFFILIATE_ID}",
                "category": category_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Amazon Search"
            })

        return products

    except Exception as e:
        print(f"  Erro fallback {category_name}: {e}")
        return []

def run_all():
    print(f"Dravek v6 a pesquisar... {datetime.now()}")
    previous = load_data()
    current = {}
    total = 0

    for category, url in CATEGORY_FEEDS.items():
        print(f"  -> {category}")
        products = scrape_page(category, url)

        if not products:
            print(f"     Bestsellers falhou, a tentar pesquisa...")
            keyword = CATEGORY_SEARCH.get(category, category)
            products = search_fallback(category, keyword)

        current[category] = products
        total += len(products)
        print(f"     {'OK' if products else 'SEM DADOS'}: {len(products)} produtos")
        time.sleep(random.uniform(6, 12))

    save_data(current)
    print(f"Dravek v6 concluiu. Total: {total}")
    return current, previous, total

def run_category(name):
    url = CATEGORY_FEEDS.get(name)
    keyword = CATEGORY_SEARCH.get(name, name)
    if url:
        products = scrape_page(name, url)
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
    lines = [f"*Dravek v6 — {now}*\n"]

    if total == 0:
        lines.append("Sem dados — Amazon bloqueou todas as pesquisas.")
        return "\n".join(lines)

    lines.append(f"Total: *{total} produtos*\n")

    for category, products in current.items():
        if not products:
            lines.append(f"\n *{category}* — Bloqueado")
            continue

        prev_asins = {p["asin"] for p in previous.get(category, [])}
        new = [p for p in products if p["asin"] not in prev_asins]
        new_tag = f" +{len(new)} novos" if new and previous else ""
        source = products[0].get("source", "") if products else ""

        lines.append(f"\n*{category}* ({len(products)}){new_tag}")
        lines.append(f"_Fonte: {source}_")
        for p in products[:5]:
            stars = f" {p['rating']}" if p['rating'] != 'N/D' else ""
            price = p['price'] if p['price'] != 'N/D' else "ver link"
            lines.append(f"  {p['rank']}. {p['title'][:50]} | {price}{stars}")

    return "\n".join(lines)

def get_context():
    data = load_data()
    total = sum(len(v) for v in data.values())
    if not data or total == 0:
        return "Sem dados do Dravek ainda."
    context = f"Dravek tem {total} produtos:\n"
    for cat, products in data.items():
        if products:
            top3 = ", ".join([p['title'][:30] for p in products[:3]])
            context += f"- {cat}: {top3}...\n"
    return context
