import os
import anthropic
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time

# ============================================================
# CONFIGURAÇÕES
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """És o Vaelthor, o bot CEO e governador do sistema de afiliados.
O teu trabalho é gerir e reportar o estado do projeto de site de afiliados do teu dono.
Respondes sempre em português de Portugal, de forma direta e clara.
Quando não tens dados reais disponíveis, dizes isso honestamente e sugeres o que fazer.
O projeto consiste num site de comparação de produtos (air fryers, aspiradores, etc.)
que monetiza através de links de afiliado Amazon."""

# ============================================================
# FUNÇÕES TELEGRAM
# ============================================================
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Erro ao obter updates: {e}")
        return {"result": []}

# ============================================================
# FUNÇÕES CLAUDE
# ============================================================
def ask_claude(user_message, context=""):
    try:
        full_message = user_message
        if context:
            full_message = f"Contexto atual do sistema:\n{context}\n\nPergunta: {user_message}"

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": full_message}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"Erro ao contactar Claude: {e}"

# ============================================================
# RESUMO DIÁRIO
# ============================================================
def get_system_context():
    now = datetime.now().strftime("%d/%m/%Y às %H:%M")
    context = f"""
Data e hora atual: {now}
Estado do sistema:
- Vaelthor (CEO bot): Operacional
- Dravek (pesquisa Amazon): Ainda não instalado
- Sylvorn (criador de artigos): Ainda não instalado
- Tharnek (monitor de preços): Ainda não instalado
- Myrondis (SEO): Ainda não instalado
- Kaelvris (redes sociais): Ainda não instalado
Site: Ainda em configuração
Artigos publicados: 0
Receita este mês: €0
"""
    return context

def send_daily_summary():
    context = get_system_context()
    prompt = f"""Gera um resumo diário matinal do sistema de afiliados.
Sê direto, usa emojis para tornar mais legível, e termina sempre com
uma sugestão do que fazer hoje para avançar o projeto.
Contexto: {context}"""

    summary = ask_claude(prompt)
    send_message(f"🏰 *Relatório Matinal do Vaelthor*\n\n{summary}")

# ============================================================
# PROCESSADOR DE MENSAGENS
# ============================================================
def process_message(text, username):
    text_lower = text.lower().strip()

    if text_lower in ["/start", "olá", "ola", "hello", "hi"]:
        return (
            "🏰 *Vaelthor ao teu serviço.*\n\n"
            "Sou o teu bot CEO. Podes perguntar-me qualquer coisa sobre o projeto.\n\n"
            "*Comandos rápidos:*\n"
            "/resumo — Resumo do estado atual\n"
            "/bots — Estado de todos os bots\n"
            "/ajuda — Lista de comandos\n\n"
            "Ou faz qualquer pergunta diretamente."
        )

    elif text_lower in ["/resumo", "/status"]:
        context = get_system_context()
        return ask_claude("Faz um resumo rápido do estado atual do projeto.", context)

    elif text_lower in ["/bots", "/sistema"]:
        return (
            "⚙️ *Estado dos Bots*\n\n"
            "🟢 Vaelthor (CEO) — Operacional\n"
            "🔴 Dravek (Pesquisa) — Por instalar\n"
            "🔴 Sylvorn (Conteúdo) — Por instalar\n"
            "🔴 Tharnek (Preços) — Por instalar\n"
            "🔴 Myrondis (SEO) — Por instalar\n"
            "🔴 Kaelvris (Redes) — Por instalar\n\n"
            "_O sistema está em fase de construção._"
        )

    elif text_lower in ["/ajuda", "/help"]:
        return (
            "📋 *Comandos do Vaelthor*\n\n"
            "/resumo — Estado atual do projeto\n"
            "/bots — Estado de todos os bots\n"
            "/ajuda — Esta mensagem\n\n"
            "_Podes também fazer qualquer pergunta em linguagem natural._"
        )

    else:
        context = get_system_context()
        return ask_claude(text, context)

# ============================================================
# LOOP PRINCIPAL
# ============================================================
def main():
    print("🏰 Vaelthor a iniciar...")

    # Agendador para o resumo diário às 8h
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_summary, 'cron', hour=8, minute=0)
    scheduler.start()

    # Mensagem de arranque
    send_message(
        "🏰 *Vaelthor está online.*\n\n"
        "O sistema de afiliados está a arrancar.\n"
        "Escreve /ajuda para ver os comandos disponíveis."
    )

    print("✅ Vaelthor online. À escuta de mensagens...")

    offset = None
    while True:
        updates = get_updates(offset)

        for update in updates.get("result", []):
            offset = update["update_id"] + 1

            if "message" not in update:
                continue

            message = update["message"]

            # Só responde ao dono (o teu chat ID)
            if str(message["chat"]["id"]) != str(CHAT_ID):
                send_message("⚠️ Acesso não autorizado.")
                continue

            text = message.get("text", "")
            username = message.get("from", {}).get("first_name", "Desconhecido")

            if text:
                print(f"Mensagem de {username}: {text}")
                response = process_message(text, username)
                send_message(response)

        time.sleep(1)

if __name__ == "__main__":
    main()
