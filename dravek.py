import os
import json
import time
import random
import requests
from datetime import datetime
from pytrends.request import TrendReq

AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "ranktuga-21")
DATA_FILE = "dravek_data.json"

CATEGORIES = {
    "Air Fryers": [
        "air fryer", "fritadeira sem oleo", "airfryer philips",
        "air fryer lidl", "melhor air fryer", "air fryer cosori",
        "air fryer tefal", "air fryer ninja", "air fryer barata",
        "air fryer portugal"
    ],
    "Aspiradores Robo": [
        "aspirador robo", "roomba", "aspirador robot xiaomi",
        "aspirador robot lidl", "melhor aspirador robo",
        "aspirador robot barato", "aspirador robot portugal",
        "robot aspirador conga", "aspirador robo 2024",
        "aspirador robot com mopa"
    ],
    "Robots de Cozinha": [
        "robot de cozinha", "bimby", "monsieur cuisine",
        "robot cozinha lidl", "melhor robot cozinha",
        "robot cozinha barato", "robot cozinha portugal",
        "thermomix", "robot cozinha moulinex",
        "robot cozinha tefal"
    ],
    "Produtos para Bebe": [
        "carrinho bebe", "cadeirinha auto bebe", "berco bebe",
        "monitor bebe", "banheira bebe", "chupeta bebe",
        "fraldas bebe", "roupa bebe", "brinquedos bebe",
        "mochila bebe"
    ],
    "Racoes para Animais": [
        "racao cao", "racao gato", "melhor racao cao",
        "racao cao barata", "comida humida gato",
        "snacks cao", "racao cachorro",
        "racao gato castrado", "racao cao adulto",
        "racao peixe aquario"
    ]
}

def get_trends(category_name, keywords):
    try:
        pytrends = TrendReq(hl='pt-PT', tz=0, timeout=(10, 25), retries=2, backoff_factor=0.5)
        results = []
        chunks = [keywords[i:i+5] for i in range(0, len(keywords), 5)]

        for chunk in chunks:
            try:
                pytrends.build_payload(chunk, timeframe='today 3-m', geo='PT')
                df = pytrends.interest_over_time()
                if df.empty:
                    continue
                for kw in chunk:
                    if kw in df.columns:
                        avg = int(df[kw].mean())
                        if avg > 0:
                            results.append({
                                "keyword": kw,
                                "interest": avg,
                                "category": category_name,
                                "url": f"https://www.amazon.es/s?k={kw.replace(' ', '+')}&tag={AFFILIATE_ID}",
                                "date": datetime.now().strftime("%Y-%m-%d")
                            })
                time.sleep(random.uniform(3, 6))
            except Exception as e:
                print(f"Erro chunk {chunk}: {e}")
                continue

        results.sort(key=lambda x: x["interest"], reverse=True)
        for i, r in enumerate(results):
            r["rank"] = i + 1
        return results[:20]

    except Exception as e:
        print(f"Erro Trends {category_name}: {e}")
        return []

def run_all():
    print(f"Dravek a pesquisar... {datetime.now()}")
    previous = load_data()
    current = {}
    total = 0

    for category, keywords in CATEGORIES.items():
        print(f"  -> {category}")
        results = get_trends(category, keywords)
        current[category] = results
        total += len(results)
        time.sleep(random.uniform(8, 15))

    save_data(current)
    print(f"Dravek concluiu. Total: {total}")
    return current, previous, total

def run_category(name):
    keywords = CATEGORIES.get(name, [])
    if not keywords:
        return []
    return get_trends(name, keywords)

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
    lines = [f"*Dravek — Google Trends PT | {now}*\n"]

    if total == 0:
        lines.append("Sem dados. Possivel limite Google Trends.")
        return "\n".join(lines)

    lines.append(f"Total analisado: *{total} pesquisas*\n")

    for category, results in current.items():
        if not results:
            lines.append(f"\n *{category}* — Sem dados")
            continue

        prev_kws = {r["keyword"] for r in previous.get(category, [])}
        new = [r for r in results if r["keyword"] not in prev_kws]
        new_tag = f" +{len(new)} novos" if new and previous else ""

        lines.append(f"\n*{category}*{new_tag}")
        for r in results[:5]:
            bar = "█" * (r["interest"] // 20)
            lines.append(f"  {r['rank']}. {r['keyword']} {bar} ({r['interest']}/100)")
        top = results[0]["keyword"]
        lines.append(f"  Sugestao de artigo: '{top}'")

    return "\n".join(lines)

def get_context():
    data = load_data()
    total = sum(len(v) for v in data.values())
    if not data:
        return "Sem dados do Dravek ainda."
    context = "Dados Google Trends PT:\n"
    for cat, results in data.items():
        if results:
            top3 = ", ".join([r["keyword"] for r in results[:3]])
            context += f"- {cat}: {top3}\n"
    context += f"Total: {total} palavras-chave"
    return context
