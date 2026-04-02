import os
import time
import requests
import anthropic
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import dravek

# ============================================================
# CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

VAELTHOR_PROMPT = """Es o Vaelthor, o bot CEO do projeto de site de afiliados ranktuga.
Geres uma equipa de bots:
- Dravek: pesquisa tendencias de produtos em Portugal via Google Trends (ativo)
- Sylvorn: cria artigos automaticamente (por instalar)
- Tharnek: monitoriza precos (por instalar)
- Myrondis: analisa SEO (por instalar)
- Kaelvris: publica em redes sociais (por instalar)

Respondes em portugues de Portugal, de forma direta e clara.
Quando o utilizador pede pesquisas, chamas o Dravek e reportas os resultados.
O objetivo final e ter um site de afiliados Amazon com artigos sobre os produtos
mais pesquisados em Portugal."""

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
# VAELTHOR — CLAUDE
# ============================================================
def get_system_context():
    data = dravek.load_data()
    total = sum(len(v) for v in data.values())
    bots_status = (
        "Vaelthor (CEO): Online\n"
        "Dravek (Tendencias Google Trends PT): Ativo\n"
        "Sylvorn (Artigos): Por instalar\n"
        "Tharnek (Precos): Por instalar\n"
        "Myrondis (SEO): Por instalar\n"
        "Kaelvris (Redes Sociais): Por instalar\n"
    )
    return (
        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Bots:\n{bots_status}"
        f"Dados Dravek: {total} palavras-chave analisadas\n"
        f"Site: ranktuga.com (por comprar)\n"
        f"Afiliado Amazon ID: ranktuga-21\n"
        f"{dravek.get_context()}"
    )

def ask_vaelthor(message, extra=""):
    try:
        context = get_system_context()
        full = f"Contexto:\n{context}\n{extra}\n\nMensagem: {message}"
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
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
    summary = ask_vaelthor("Gera o relatorio matinal. Usa emojis, sê direto, termina com sugestao do que fazer hoje.")
    send_message(f"*Relatorio Matinal — Vaelthor*\n\n{summary}")

def daily_search():
    print("Pesquisa diaria Dravek a iniciar...")
    current, previous, total = dravek.run_all()
    report = dravek.format_report(current, previous, total)
    send_message(report)

# ============================================================
# COMANDOS
# ============================================================
def process_message(text):
    cmd = text.lower().strip()

    if cmd in ["/start", "ola", "olá", "hi", "hello"]:
        send_message(
            "*Vaelthor ao teu servico.*\n\n"
            "Sou o teu CEO. Fala so comigo — eu trato dos subordinados.\n\n"
            "*Comandos:*\n"
            "/resumo — Estado do projeto\n"
            "/pesquisar — Dravek pesquisa tendencias em PT agora\n"
            "/top — Ver top pesquisas por categoria\n"
            "/bots — Estado dos bots\n"
            "/ajuda — Todos os comandos\n\n"
            "Ou faz qualquer pergunta em linguagem natural."
        )

    elif cmd in ["/resumo", "/status"]:
        resp = ask_vaelthor("Faz um resumo rapido do estado atual do projeto.")
        send_message(f"*Vaelthor*\n\n{resp}")

    elif cmd in ["/pesquisar", "/search"]:
        send_message("*Vaelthor* — A chamar o Dravek. Pesquisa Google Trends PT em curso, aguarda 2-3 minutos...")
        current, previous, total = dravek.run_all()
        report = dravek.format_report(current, previous, total)
        send_message(report)
        if total > 0:
            send_message("*Dravek concluiu.* Usa /top para ver os resultados ou pede-me um artigo.")

    elif cmd == "/top":
        data = dravek.load_data()
        if not data or all(len(v) == 0 for v in data.values()):
            send_message("Sem dados. Usa /pesquisar primeiro.")
            return
        lines = ["*Top 5 por categoria (Google Trends PT):*\n"]
        for cat, results in data.items():
            if results:
                lines.append(f"\n*{cat}*")
                for r in results[:5]:
                    lines.append(f"  {r['rank']}. {r['keyword']} ({r['interest']}/100)")
                lines.append(f"  [Ver na Amazon]({results[0]['url']})")
        send_message("\n".join(lines))

    elif cmd == "/bots":
        data = dravek.load_data()
        total = sum(len(v) for v in data.values())
        send_message(
            "*Estado dos Bots*\n\n"
            f"Vaelthor (CEO) — Online\n"
            f"Dravek (Tendencias) — Ativo | {total} dados guardados\n"
            "Sylvorn (Artigos) — Por instalar\n"
            "Tharnek (Precos) — Por instalar\n"
            "Myrondis (SEO) — Por instalar\n"
            "Kaelvris (Redes) — Por instalar"
        )

    elif cmd in ["/ajuda", "/help"]:
        send_message(
            "*Comandos Vaelthor*\n\n"
            "/resumo — Estado do projeto\n"
            "/pesquisar — Tendencias Google Trends PT\n"
            "/top — Top por categoria\n"
            "/bots — Estado dos bots\n"
            "/ajuda — Esta mensagem\n\n"
            "Podes tambem fazer qualquer pergunta em linguagem natural."
        )

    else:
        resp = ask_vaelthor(text)
        send_message(f"*Vaelthor*\n\n{resp}")

# ============================================================
# MAIN
# ============================================================
def main():
    print("Vaelthor v4 a iniciar...")

    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_summary, 'cron', hour=8, minute=0)
    scheduler.add_job(daily_search, 'cron', hour=7, minute=0)
    scheduler.start()

    send_message(
        "*Vaelthor v4 online*\n\n"
        "Dravek agora usa Google Trends PT — sem bloqueios da Amazon.\n"
        "Usa /pesquisar para ver as tendencias de produtos em Portugal agora."
    )

    print("Vaelthor v4 online.")

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
