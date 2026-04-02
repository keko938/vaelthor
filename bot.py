import os
import time
import requests
import anthropic
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import dravek
import sylvorn

# ============================================================
# CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

VAELTHOR_PROMPT = """Es o Vaelthor, o bot CEO do projeto ranktuga — site de afiliados Amazon em Portugal.
Geres estes bots subordinados:
- Dravek: recolhe top 20 produtos por categoria (ativo)
- Sylvorn: cria artigos SEO em portugues europeu (ativo)
- Tharnek: monitoriza precos (por instalar)
- Myrondis: analisa SEO (por instalar)
- Kaelvris: publica em redes sociais (por instalar)

Respondes sempre em portugues de Portugal, direto e claro.
Quando o utilizador pede artigos, chamas o Sylvorn.
Quando pede pesquisas, chamas o Dravek.
O objetivo e ter um site com artigos de comparacao de produtos que geram comissoes Amazon."""

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
            time.sleep(0.5)
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
# CONTEXTO DO SISTEMA
# ============================================================
def get_system_context():
    dravek_ctx = dravek.get_context()
    articles = sylvorn.load_articles()
    total_articles = len(articles)
    data = dravek.load_data()
    total_products = sum(len(v) for v in data.values()) if data else 100

    return (
        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Bots: Vaelthor OK | Dravek OK | Sylvorn OK | Tharnek/Myrondis/Kaelvris por instalar\n"
        f"Produtos em base: {total_products}\n"
        f"Artigos criados: {total_articles}\n"
        f"Site: ranktuga.com (por comprar, ~44€/ano)\n"
        f"Afiliado Amazon ID: ranktuga-21\n"
        f"{dravek_ctx}"
    )

def ask_vaelthor(message, extra=""):
    try:
        context = get_system_context()
        full = f"Contexto:\n{context}\n{extra}\n\nMensagem: {message}"
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=VAELTHOR_PROMPT,
            messages=[{"role": "user", "content": full}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Erro Claude: {e}"

# ============================================================
# TAREFAS AGENDADAS
# ============================================================
def daily_summary():
    summary = ask_vaelthor(
        "Gera o relatorio matinal. "
        "Inclui: estado dos bots, artigos criados, proximos passos. "
        "Usa emojis. Sê direto."
    )
    send_message(f"*Relatorio Matinal — Vaelthor*\n\n{summary}")

def daily_search():
    current, previous, total = dravek.run_all()
    report = dravek.format_report(current, previous, total)
    send_message(report)

# ============================================================
# COMANDOS
# ============================================================
def process_message(text):
    cmd = text.lower().strip()

    # ── INÍCIO ──────────────────────────────────────────────
    if cmd in ["/start", "ola", "olá", "hi", "hello"]:
        send_message(
            "*Vaelthor ao teu servico.*\n\n"
            "Comandos disponiveis:\n\n"
            "*Dravek (Pesquisa):*\n"
            "/pesquisar — Pesquisar top produtos\n"
            "/top — Ver top 5 por categoria\n\n"
            "*Sylvorn (Artigos):*\n"
            "/artigo — Criar artigo de comparacao\n"
            "/review — Criar review de produto especifico\n"
            "/artigos — Ver artigos criados\n"
            "/ultimoartigo — Ver conteudo do ultimo artigo\n\n"
            "*Geral:*\n"
            "/resumo — Estado do projeto\n"
            "/bots — Estado dos bots\n"
            "/ajuda — Esta mensagem\n\n"
            "_Ou faz qualquer pergunta em linguagem natural._"
        )

    # ── DRAVEK ──────────────────────────────────────────────
    elif cmd in ["/pesquisar", "/search"]:
        send_message("*Vaelthor* — A chamar o Dravek...")
        current, previous, total = dravek.run_all()
        report = dravek.format_report(current, previous, total)
        send_message(report)

    elif cmd == "/top":
        data = dravek.load_data()
        if not data:
            # Usa dados curados se nao ha dados guardados
            curated = dravek.build_curated_products()
            data = curated
        lines = ["*Top 5 por categoria (Dravek):*\n"]
        for cat, products in data.items():
            if products:
                lines.append(f"\n*{cat}*")
                for p in products[:5]:
                    stars = f" ⭐{p['rating']}" if p.get('rating', 'N/D') != 'N/D' else ""
                    lines.append(f"  {p['rank']}. {p['title'][:40]}... {p['price']}{stars}")
        send_message("\n".join(lines))

    # ── SYLVORN ─────────────────────────────────────────────
    elif cmd == "/artigo":
        # Mostra menu de categorias
        send_message(
            "*Sylvorn — Criar artigo*\n\n"
            "Escolhe uma categoria:\n\n"
            "/artigo_airfryers\n"
            "/artigo_aspiradores\n"
            "/artigo_robots\n"
            "/artigo_bebe\n"
            "/artigo_animais"
        )

    elif cmd == "/artigo_airfryers":
        _create_article("Air Fryers")

    elif cmd == "/artigo_aspiradores":
        _create_article("Aspiradores Robo")

    elif cmd == "/artigo_robots":
        _create_article("Robots de Cozinha")

    elif cmd == "/artigo_bebe":
        _create_article("Produtos para Bebe")

    elif cmd == "/artigo_animais":
        _create_article("Racoes para Animais")

    elif cmd == "/review":
        data = dravek.load_data()
        if not data:
            data = dravek.build_curated_products()
        # Mostra os top produtos para escolher
        lines = ["*Sylvorn — Criar review*\n\nEscolhe o produto pelo numero:\n"]
        all_products = []
        count = 1
        for cat, products in data.items():
            for p in products[:3]:
                lines.append(f"/review_{count} — {p['title'][:45]}...")
                all_products.append(p)
                count += 1
        # Guarda lista temporaria
        _save_temp(all_products)
        send_message("\n".join(lines[:25]))

    elif cmd.startswith("/review_"):
        try:
            idx = int(cmd.replace("/review_", "")) - 1
            products = _load_temp()
            if products and 0 <= idx < len(products):
                product = products[idx]
                send_message(f"*Sylvorn* — A escrever review de:\n_{product['title']}_\n\nAguarda 1-2 minutos...")
                article, filename = sylvorn.create_product_review(product)
                if article:
                    send_message(
                        f"*Sylvorn* — Review criada!\n\n"
                        f"*{article['title'][:60]}*\n"
                        f"_{article['word_count']} palavras | {article['category']}_\n\n"
                        f"Usa /ultimoartigo para ver o conteudo completo."
                    )
                else:
                    send_message("Erro ao criar review. Tenta novamente.")
        except (ValueError, IndexError):
            send_message("Numero invalido. Usa /review para ver a lista.")

    elif cmd == "/artigos":
        send_message(sylvorn.list_articles())

    elif cmd == "/ultimoartigo":
        article = sylvorn.get_latest_article_content()
        if not article:
            send_message("Sem artigos ainda. Usa /artigo para criar o primeiro.")
            return
        # Envia metadata + preview do conteudo
        preview = article['content'][:1500] + "\n\n_...continua (artigo completo guardado no servidor)_"
        send_message(
            f"*{article['title'][:60]}*\n"
            f"_{article['category']} | {article['word_count']} palavras | {article['created_at']}_\n\n"
            f"{preview}"
        )

    # ── GERAL ───────────────────────────────────────────────
    elif cmd in ["/resumo", "/status"]:
        resp = ask_vaelthor("Faz um resumo rapido do estado atual do projeto.")
        send_message(f"*Vaelthor*\n\n{resp}")

    elif cmd == "/bots":
        articles = sylvorn.load_articles()
        data = dravek.load_data()
        products = sum(len(v) for v in data.values()) if data else 100
        send_message(
            "*Estado dos Bots*\n\n"
            f"Vaelthor (CEO) — Online\n"
            f"Dravek (Pesquisa) — Ativo | {products} produtos\n"
            f"Sylvorn (Artigos) — Ativo | {len(articles)} artigos criados\n"
            "Tharnek (Precos) — Por instalar\n"
            "Myrondis (SEO) — Por instalar\n"
            "Kaelvris (Redes) — Por instalar\n\n"
            "*Proximo passo:* Comprar ranktuga.com + WordPress (~44€)"
        )

    elif cmd in ["/ajuda", "/help"]:
        process_message("/start")

    else:
        resp = ask_vaelthor(text)
        send_message(f"*Vaelthor*\n\n{resp}")

# ============================================================
# HELPERS
# ============================================================
def _create_article(category_name):
    send_message(f"*Sylvorn* — A criar artigo sobre *{category_name}*...\nAguarda 2-3 minutos.")
    data = dravek.load_data()
    if not data or category_name not in data:
        data = dravek.build_curated_products()
    products = data.get(category_name, [])
    if not products:
        send_message(f"Sem produtos para {category_name}. Usa /pesquisar primeiro.")
        return
    article, filename = sylvorn.create_category_article(category_name, products)
    if article:
        send_message(
            f"*Sylvorn* — Artigo criado!\n\n"
            f"*{article['title'][:60]}*\n"
            f"_{article['word_count']} palavras | {article['products_count']} produtos comparados_\n\n"
            f"Usa /ultimoartigo para ver o conteudo completo."
        )
    else:
        send_message("Erro ao criar artigo. Tenta novamente.")

def _save_temp(data):
    try:
        with open("temp_products.json", "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, ensure_ascii=False)
    except:
        pass

def _load_temp():
    try:
        import json
        with open("temp_products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# ============================================================
# MAIN
# ============================================================
def main():
    print("Vaelthor v8 (com Sylvorn) a iniciar...")

    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_summary, 'cron', hour=8, minute=0)
    scheduler.add_job(daily_search, 'cron', hour=7, minute=0)
    scheduler.start()

    send_message(
        "*Vaelthor v8 online*\n\n"
        "Sylvorn esta agora ativo — posso criar artigos automaticamente.\n\n"
        "Usa /artigo para criar o primeiro artigo agora."
    )

    print("Vaelthor v8 online.")

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
