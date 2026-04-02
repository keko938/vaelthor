import os
import anthropic
import requests
import json
import time
import random
import re
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# ============================================================
# CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")
AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "ranktuga-21")
DATA_FILE = "dravek_data.json"

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

CATEGORIES = {
    "Air Fryers": "air+fryer",
    "Aspiradores Robô": "aspiradora+robot",
    "Robots de Cozinha": "robot+cocina",
    "Produtos para Bebé": "productos+bebe",
    "Rações para Animais": "pienso+perro+gato"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

VAELTHOR_PROMPT = """És o Vaelthor, o bot CEO do projeto de site de afiliados ranktuga.
Geres uma equipa de bots subordinados:
- Dravek: pesquisa produtos na Amazon
- Sylvorn: cria artigos (ainda não instalado)
- Tharnek: monitoriza preços (ainda não instalado)
- Myrondis: analisa SEO (ainda não instalado)
- Kaelvris: publica em redes sociais (ainda não instalado)

Respondes sempre em português de Portugal, de forma direta e clara.
Quando o utilizador pede pesquisas, reportas os dados que o Dravek recolheu.
Quando não tens dados, dizes isso honestamente."""

# ============================================================
# TELEGRAM
# ============================================================
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        try:
            requests.post(url, json={
                "chat_id": CHAT_ID,
                "text": chunk,
                "parse_mode": "Markdown"
            })
            time.sleep(0.3)
        except Exception as e:
            print(f"Erro Telegram: {e}")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        return requests.get(url, params=params).json()
    except:
        return {"result": []}

# ============================================================
# DRAVEK — MÓDULO INTERNO DE PESQUISA
# ============================================================
def dravek_get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "es-ES,es;q=0.9,pt;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

def dravek_search(keyword, category_name, max_results=20):
    url = f"https://www.amazon.es/s?k={keyword}&tag={AFFILIATE_ID}"
    try:
        session = requests.Session()
        session.get("https://www.amazon.es", headers=dravek_get_headers(), timeout=10)
        time.sleep(random.uniform(2, 4))
        response = session.get(url, headers=dravek_get_headers(), timeout=15)
        if response.status_code != 200:
            return []
        return dravek_parse(response.text, category_name, max_results)
    except Exception as e:
        print(f"Dravek erro em {category_name}: {e}")
        return []

def dravek_parse(html, category_name, max_results=20):
    products = []
    try:
        asins = list(dict.fromkeys([
            a for a in re.findall(r'data-asin="([A-Z0-9]{10})"', html) if a
        ]))

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
        prices = [f"{price_wholes[i]},{price_decs[i] if i < len(price_decs) else '00'}€"
                  for i in range(len(price_wholes))]
        ratings = re.findall(r'(\d+[,.]\d+)\s*de\s*5\s*estrellas?', html)

        for i, asin in enumerate(asins[:max_results]):
            products.append({
                "rank": i + 1,
                "asin": asin,
                "title": (titles[i] if i < len(titles) else f"Produto {asin}")[:80],
                "price": prices[i] if i < len(prices) else "N/D",
                "rating": ratings[i] if i < len(ratings) else "N/D",
                "url": f"https://www.amazon.es/dp/{asin}?tag={AFFILIATE_ID}",
                "category": category_name,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
    except Exception as e:
        print(f"Parse erro: {e}")
    return products

def dravek_run_all():
    """Corre pesquisa completa em todas as categorias."""
    print(f"🔍 Dravek a pesquisar... {datetime.now()}")
    previous = load_data()
    current = {}
    total = 0

    for category, keyword in CATEGORIES.items():
        print(f"  → {category}")
        products = dravek_search(keyword, category)
        current[category] = products
        total += len(products)
        time.sleep(random.uniform(5, 10))

    save_data(current)
    print(f"✅ Dravek concluiu. Total: {total} produtos.")
    return current, previous, total

def dravek_run_category(category_name):
    """Pesquisa só uma categoria específica."""
    keyword = CATEGORIES.get(category_name)
    if not keyword:
        return []
    return dravek_search(keyword, category_name)

# ============================================================
# BASE DE DADOS
# ============================================================
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
        print(f"Erro ao guardar: {e}")

def get_system_context():
    data = load_data()
    total_products = sum(len(v) for v in data.values()) if data else 0
    last_search = "Ainda não feita"
    if data:
        for cat, products in data.items():
            if products:
                last_search = products[0].get("date", "Desconhecida")
                break

    categories_status = ""
    for cat in CATEGORIES:
        count = len(data.get(cat, []))
        categories_status += f"- {cat}: {count} produtos\n"

    return f"""
Data/hora atual: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Última pesquisa Dravek: {last_search}
Total produtos em base de dados: {total_products}
Categorias:
{categories_status}
Bots instalados: Vaelthor (CEO), Dravek (pesquisa - integrado)
Bots por instalar: Sylvorn, Tharnek, Myrondis, Kaelvris
Site: Ainda em configuração (ranktuga.com por comprar)
ID Afiliado Amazon: {AFFILIATE_ID}
"""

# ============================================================
# CLAUDE — VAELTHOR
# ============================================================
def ask_vaelthor(user_message, extra_context=""):
    try:
        context = get_system_context()
        full_context = context + "\n" + extra_context if extra_context else context
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=VAELTHOR_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Contexto do sistema:\n{full_context}\n\nMensagem: {user_message}"
            }]
        )
        return message.content[0].text
    except Exception as e:
        return f"Erro ao contactar Claude: {e}"

# ============================================================
# RELATÓRIOS
# ============================================================
def send_daily_summary():
    data = load_data()
    total = sum(len(v) for v in data.values())
    context = get_system_context()
    summary = ask_vaelthor(
        "Gera o relatório matinal diário. Sê direto, usa emojis, "
        "termina com uma sugestão do que fazer hoje.",
        context
    )
    send_message(f"🏰 *Relatório Matinal — Vaelthor*\n\n{summary}")

def format_search_results(current, previous, total):
    lines = [f"📊 *Dravek reporta — {datetime.now().strftime('%d/%m %H:%M')}*\n"]
    lines.append(f"Total encontrado: *{total} produtos*\n")

    for category, products in current.items():
        if not products:
            lines.append(f"\n❌ *{category}* — Amazon bloqueou pesquisa")
            continue

        prev_asins = {p["asin"] for p in previous.get(category, [])}
        new = [p for p in products if p["asin"] not in prev_asins]
        new_tag = f" 🆕 +{len(new)}" if new and previous else ""

        lines.append(f"\n*{category}* ({len(products)}){new_tag}")
        for p in products[:3]:
            stars = f"⭐{p['rating']}" if p['rating'] != 'N/D' else ""
            lines.append(f"  {p['rank']}. {p['title'][:40]}... {p['price']} {stars}")

    return "\n".join(lines)

# ============================================================
# PROCESSADOR DE MENSAGENS
# ============================================================
def process_message(text):
    cmd = text.lower().strip()

    if cmd in ["/start", "olá", "ola", "hi", "hello"]:
        send_message(
            "🏰 *Vaelthor ao teu serviço.*\n\n"
            "Sou o teu CEO. Giro toda a operação e falo com os bots subordinados.\n\n"
            "*Comandos:*\n"
            "/resumo — Estado do projeto\n"
            "/pesquisar — Dravek pesquisa Amazon agora\n"
            "/top — Ver top produtos por categoria\n"
            "/bots — Estado dos bots\n"
            "/ajuda — Todos os comandos\n\n"
            "Ou faz qualquer pergunta em linguagem natural."
        )

    elif cmd in ["/resumo", "/status"]:
        response = ask_vaelthor("Faz um resumo rápido do estado atual do projeto.")
        send_message(f"🏰 *Vaelthor*\n\n{response}")

    elif cmd in ["/pesquisar", "/search"]:
        send_message("🔍 *Vaelthor* — A chamar o Dravek. Pesquisa em curso, aguarda 2-3 minutos...")
        current, previous, total = dravek_run_all()
        report = format_search_results(current, previous, total)
        send_message(report)
        if total > 0:
            send_message("✅ *Dravek concluiu.* Dados guardados. Usa /top para ver os melhores produtos.")

    elif cmd == "/top":
        data = load_data()
        if not data or all(len(v) == 0 for v in data.values()):
            send_message("🔍 Sem dados ainda. Usa /pesquisar primeiro.")
            return
        lines = ["🏆 *Top 3 por categoria (via Dravek):*\n"]
        for cat, products in data.items():
            if products:
                lines.append(f"\n*{cat}*")
                for p in products[:3]:
                    lines.append(f"  {p['rank']}. {p['title'][:45]}... {p['price']}")
                    lines.append(f"     [Ver na Amazon]({p['url']})")
        send_message("\n".join(lines))

    elif cmd == "/bots":
        data = load_data()
        total = sum(len(v) for v in data.values())
        send_message(
            "⚙️ *Estado dos Bots*\n\n"
            f"🟢 Vaelthor (CEO) — Online\n"
            f"🟢 Dravek (Pesquisa) — Integrado | {total} produtos em base de dados\n"
            "🔴 Sylvorn (Conteúdo) — Por instalar\n"
            "🔴 Tharnek (Preços) — Por instalar\n"
            "🔴 Myrondis (SEO) — Por instalar\n"
            "🔴 Kaelvris (Redes) — Por instalar"
        )

    elif cmd in ["/ajuda", "/help"]:
        send_message(
            "📋 *Comandos do Vaelthor*\n\n"
            "/resumo — Estado do projeto\n"
            "/pesquisar — Pesquisa Amazon via Dravek\n"
            "/top — Top produtos por categoria\n"
            "/bots — Estado de todos os bots\n"
            "/ajuda — Esta mensagem\n\n"
            "_Podes também fazer qualquer pergunta em linguagem natural._"
        )

    else:
        # Resposta livre via Claude
        response = ask_vaelthor(text)
        send_message(f"🏰 *Vaelthor*\n\n{response}")

# ============================================================
# MAIN
# ============================================================
def main():
    print("🏰 Vaelthor (com Dravek integrado) a iniciar...")

    scheduler = BackgroundScheduler()
    # Resumo diário às 8h
    scheduler.add_job(send_daily_summary, 'cron', hour=8, minute=0)
    # Pesquisa Dravek todos os dias às 7h
    scheduler.add_job(dravek_run_all, 'cron', hour=7, minute=0)
    scheduler.start()

    send_message(
        "🏰 *Vaelthor online — Sistema atualizado*\n\n"
        "O Dravek está agora integrado. Fala só comigo e eu trato do resto.\n\n"
        "Usa /pesquisar para o Dravek pesquisar a Amazon agora."
    )

    print("✅ Sistema online.")

    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates.get("result", []):
            offset = update["update_id"] + 1
            if "message" not in update:
                continue
            msg = update["message"]
            if str(msg["chat"]["id"]) != str(CHAT_ID):
                continue
            text = msg.get("text", "")
            if text:
                print(f"Mensagem: {text}")
                process_message(text)
        time.sleep(1)

if __name__ == "__main__":
    main()
