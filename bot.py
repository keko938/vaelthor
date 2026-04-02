import os
import time
import requests
import anthropic
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import dravek
import sylvorn
import tharnek
import myrondis
import kaelvris

# ============================================================
# CONFIGURACOES
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

VAELTHOR_PROMPT = """Es o Vaelthor, CEO do projeto ranktuga — site de afiliados Amazon em Portugal.
A tua equipa de bots:
- Dravek: recolhe top 20 produtos por categoria (ativo)
- Sylvorn: cria artigos SEO em portugues europeu (ativo)
- Tharnek: monitoriza variacoes de preco (ativo)
- Myrondis: analisa SEO dos artigos (ativo)
- Kaelvris: cria posts para redes sociais (ativo)

Todos os bots estao agora operacionais.
Respondes em portugues de Portugal, direto e claro.
O objetivo final: site ranktuga.com com artigos que geram comissoes Amazon automaticamente."""

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
# CONTEXTO
# ============================================================
def get_system_context():
    data = dravek.load_data()
    total_products = sum(len(v) for v in data.values()) if data else 100
    articles = sylvorn.load_articles()
    posts = kaelvris.load_posts()

    return (
        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Todos os 6 bots operacionais\n"
        f"Produtos em base: {total_products}\n"
        f"Artigos criados: {len(articles)}\n"
        f"Posts redes sociais: {len(posts)}\n"
        f"Site: ranktuga.com (por comprar ~44€)\n"
        f"ID Afiliado: ranktuga-21\n"
        f"{dravek.get_context()}"
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
    summary = ask_vaelthor("Gera o relatorio matinal completo com estado de todos os bots, artigos e proximos passos. Usa emojis.")
    send_message(f"*Relatorio Matinal — Vaelthor*\n\n{summary}")

def daily_search():
    current, previous, total = dravek.run_all()
    report = dravek.format_report(current, previous, total)
    send_message(report)

    # Tharnek verifica precos automaticamente
    if current:
        alerts, changes, monitored = tharnek.monitor_prices(current)
        if alerts:
            send_message(tharnek.format_alerts(alerts))

# ============================================================
# COMANDOS
# ============================================================
def process_message(text):
    cmd = text.lower().strip()

    # ── INICIO ──────────────────────────────────────────────
    if cmd in ["/start", "ola", "olá", "hi", "hello"]:
        send_message(
            "*Vaelthor — Sistema Completo Online*\n\n"
            "*Dravek (Pesquisa):*\n"
            "/pesquisar — Pesquisar top produtos\n"
            "/top — Ver top 5 por categoria\n\n"
            "*Sylvorn (Artigos):*\n"
            "/artigo — Menu de criacao de artigos\n"
            "/artigos — Ver artigos criados\n"
            "/ultimoartigo — Ver ultimo artigo\n\n"
            "*Tharnek (Precos):*\n"
            "/precos — Verificar alteracoes de preco\n\n"
            "*Myrondis (SEO):*\n"
            "/seo — Analisar SEO do ultimo artigo\n"
            "/keywords — Ver palavras-chave por categoria\n\n"
            "*Kaelvris (Redes Sociais):*\n"
            "/posts — Criar posts para redes sociais\n"
            "/verpost — Ver ultimo post criado\n\n"
            "*Geral:*\n"
            "/resumo — Estado completo\n"
            "/bots — Estado dos bots\n"
            "/ajuda — Esta mensagem"
        )

    # ── DRAVEK ──────────────────────────────────────────────
    elif cmd in ["/pesquisar", "/search"]:
        send_message("*Vaelthor* — Dravek a pesquisar...")
        current, previous, total = dravek.run_all()
        report = dravek.format_report(current, previous, total)
        send_message(report)

        # Tharnek verifica precos automaticamente
        if current:
            alerts, changes, monitored = tharnek.monitor_prices(current)
            if alerts:
                send_message(tharnek.format_alerts(alerts))
            else:
                send_message(f"*Tharnek* — Precos estáveis. {monitored} produtos monitorizados.")

    elif cmd == "/top":
        data = dravek.load_data()
        if not data:
            data = dravek.build_curated_products()
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
        send_message(
            "*Sylvorn — Criar artigo*\n\n"
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

    elif cmd == "/artigos":
        send_message(sylvorn.list_articles())

    elif cmd == "/ultimoartigo":
        article = sylvorn.get_latest_article_content()
        if not article:
            send_message("Sem artigos ainda. Usa /artigo.")
            return
        preview = article['content'][:1500] + "\n\n_...artigo completo no servidor_"
        send_message(
            f"*{article['title'][:60]}*\n"
            f"_{article['category']} | {article['word_count']} palavras | {article['created_at']}_\n\n"
            f"{preview}"
        )

    # ── THARNEK ─────────────────────────────────────────────
    elif cmd == "/precos":
        send_message("*Tharnek* — A verificar precos...")
        data = dravek.load_data()
        if not data:
            data = dravek.build_curated_products()
        alerts, changes, monitored = tharnek.monitor_prices(data)
        if alerts:
            send_message(tharnek.format_alerts(alerts))
        else:
            send_message(
                f"*Tharnek*\n\n"
                f"Sem alteracoes significativas.\n"
                f"{monitored} produtos monitorizados.\n"
                f"Alerta quando variacao > {tharnek.ALERT_THRESHOLD}%"
            )

    # ── MYRONDIS ────────────────────────────────────────────
    elif cmd == "/seo":
        article = sylvorn.get_latest_article_content()
        if not article:
            send_message("Sem artigos para analisar. Usa /artigo primeiro.")
            return
        send_message("*Myrondis* — A analisar SEO...")
        analysis = myrondis.analyze_article_seo(article)
        ai_tips = myrondis.get_ai_seo_tips(article)
        report = myrondis.format_seo_report(article, analysis, ai_tips)
        myrondis.save_seo_report(article.get("id", ""), analysis)
        send_message(report)

    elif cmd == "/keywords":
        send_message(
            "*Myrondis — Palavras-chave por categoria*\n\n"
            "Escolhe:\n"
            "/kw_airfryers\n"
            "/kw_aspiradores\n"
            "/kw_robots\n"
            "/kw_bebe\n"
            "/kw_animais"
        )

    elif cmd == "/kw_airfryers":
        _show_keywords("Air Fryers")
    elif cmd == "/kw_aspiradores":
        _show_keywords("Aspiradores Robo")
    elif cmd == "/kw_robots":
        _show_keywords("Robots de Cozinha")
    elif cmd == "/kw_bebe":
        _show_keywords("Produtos para Bebe")
    elif cmd == "/kw_animais":
        _show_keywords("Racoes para Animais")

    # ── KAELVRIS ────────────────────────────────────────────
    elif cmd == "/posts":
        article = sylvorn.get_latest_article_content()
        if not article:
            send_message("Sem artigos. Cria um com /artigo primeiro.")
            return
        send_message("*Kaelvris* — A criar posts para redes sociais...")
        data = dravek.load_data()
        if not data:
            data = dravek.build_curated_products()
        category = article.get("category", "")
        top_product = data.get(category, [{}])[0] if data.get(category) else None
        posts = kaelvris.create_all_posts(article, top_product)
        send_message(kaelvris.format_posts_for_telegram(posts, "pinterest"))
        time.sleep(1)
        send_message(kaelvris.format_posts_for_telegram(posts, "facebook"))

    elif cmd == "/verpost":
        all_posts = kaelvris.load_posts()
        if not all_posts:
            send_message("Sem posts criados. Usa /posts primeiro.")
            return
        last = list(all_posts.values())[-1]
        send_message(kaelvris.format_posts_for_telegram(last))

    # ── GERAL ───────────────────────────────────────────────
    elif cmd in ["/resumo", "/status"]:
        resp = ask_vaelthor("Faz um resumo completo do estado atual do projeto incluindo todos os bots.")
        send_message(f"*Vaelthor*\n\n{resp}")

    elif cmd == "/bots":
        articles = sylvorn.load_articles()
        posts = kaelvris.load_posts()
        data = dravek.load_data()
        products = sum(len(v) for v in data.values()) if data else 100
        prices = tharnek.load_prices()
        send_message(
            "*Estado dos Bots — Sistema Completo*\n\n"
            f"Vaelthor (CEO) — Online\n"
            f"Dravek (Pesquisa) — Ativo | {products} produtos\n"
            f"Sylvorn (Artigos) — Ativo | {len(articles)} artigos\n"
            f"Tharnek (Precos) — Ativo | {len(prices)} produtos monitorizados\n"
            f"Myrondis (SEO) — Ativo | Pronto para analisar\n"
            f"Kaelvris (Redes) — Ativo | {len(posts)} posts criados\n\n"
            "*Proximo passo:* Comprar ranktuga.com + WordPress (~44€/ano)"
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
    send_message(f"*Sylvorn* — A criar artigo: *{category_name}*\nAguarda 2-3 minutos...")
    data = dravek.load_data()
    if not data or category_name not in data:
        data = dravek.build_curated_products()
    products = data.get(category_name, [])
    if not products:
        send_message(f"Sem produtos. Usa /pesquisar primeiro.")
        return

    article, filename = sylvorn.create_category_article(category_name, products)
    if not article:
        send_message("Erro ao criar artigo.")
        return

    # Analise SEO automatica
    analysis = myrondis.analyze_article_seo(article)
    score = analysis["score"]
    emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"

    send_message(
        f"*Sylvorn* — Artigo criado!\n\n"
        f"*{article['title'][:60]}*\n"
        f"_{article['word_count']} palavras | {article['products_count']} produtos_\n\n"
        f"{emoji} *SEO Score: {score}/100* (Myrondis)\n\n"
        f"Usa /seo para analise completa\n"
        f"Usa /posts para criar posts para redes sociais"
    )

def _show_keywords(category):
    kws = myrondis.analyze_keywords(category)
    if not kws:
        send_message("Sem palavras-chave para esta categoria.")
        return
    lines = [f"*Myrondis — Keywords: {category}*\n"]
    for i, kw in enumerate(kws, 1):
        lines.append(f"{i}. `{kw}`")
    lines.append("\n_Usa estas nos titulos e ao longo dos artigos_")
    send_message("\n".join(lines))

# ============================================================
# MAIN
# ============================================================
def main():
    print("Vaelthor — Sistema Completo a iniciar...")

    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_summary, 'cron', hour=8, minute=0)
    scheduler.add_job(daily_search, 'cron', hour=7, minute=0)
    scheduler.start()

    send_message(
        "*Sistema Ranktuga — Totalmente Operacional*\n\n"
        "Todos os 6 bots estao online:\n"
        "Vaelthor Dravek Sylvorn Tharnek Myrondis Kaelvris\n\n"
        "Usa /ajuda para ver todos os comandos."
    )

    print("Sistema completo online.")

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
