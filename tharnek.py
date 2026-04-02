import os
import json
import requests
import random
import re
import time
from datetime import datetime

AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "ranktuga-21")
PRICES_FILE = "tharnek_prices.json"

ALERT_THRESHOLD = 15  # % de variacao que dispara alerta

def load_prices():
    try:
        if os.path.exists(PRICES_FILE):
            with open(PRICES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_prices(data):
    try:
        with open(PRICES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Tharnek erro guardar: {e}")

def parse_price(price_str):
    """Converte string de preco para float."""
    try:
        clean = re.sub(r'[^\d,.]', '', str(price_str))
        clean = clean.replace(',', '.')
        return float(clean)
    except:
        return None

def check_price_change(asin, current_price_str, previous_prices):
    """Verifica se houve variacao significativa de preco."""
    current = parse_price(current_price_str)
    if not current or asin not in previous_prices:
        return None

    previous = previous_prices[asin].get("price_value")
    if not previous or previous == 0:
        return None

    change_pct = ((current - previous) / previous) * 100

    if abs(change_pct) >= ALERT_THRESHOLD:
        direction = "subiu" if change_pct > 0 else "baixou"
        return {
            "asin": asin,
            "direction": direction,
            "change_pct": round(abs(change_pct), 1),
            "old_price": previous,
            "new_price": current
        }
    return None

def monitor_prices(dravek_data):
    """Monitoriza precos de todos os produtos no Dravek."""
    previous = load_prices()
    current = {}
    alerts = []
    changes = 0

    for category, products in dravek_data.items():
        for p in products:
            asin = p.get("asin")
            price_str = p.get("price", "N/D")
            price_val = parse_price(price_str)

            if not asin:
                continue

            # Verifica variacao
            alert = check_price_change(asin, price_str, previous)
            if alert:
                alert["title"] = p.get("title", "")[:50]
                alert["category"] = category
                alert["url"] = p.get("url", "")
                alerts.append(alert)
                changes += 1

            # Guarda preco atual
            current[asin] = {
                "title": p.get("title", "")[:60],
                "category": category,
                "price_str": price_str,
                "price_value": price_val,
                "url": p.get("url", ""),
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

    save_prices(current)
    return alerts, changes, len(current)

def get_price_history(asin):
    """Retorna historico de preco de um produto."""
    prices = load_prices()
    return prices.get(asin)

def format_alerts(alerts):
    """Formata alertas de preco para Telegram."""
    if not alerts:
        return "Sem alteracoes significativas de preco."

    lines = [f"*Tharnek — {len(alerts)} alerta(s) de preco*\n"]
    for a in alerts:
        emoji = "📈" if a["direction"] == "subiu" else "📉"
        lines.append(
            f"{emoji} *{a['title']}*\n"
            f"   {a['category']}\n"
            f"   {a['old_price']}€ → {a['new_price']}€ ({a['direction']} {a['change_pct']}%)\n"
            f"   ⚠️ _Atualiza o artigo!_\n"
        )
    return "\n".join(lines)

def get_stats():
    prices = load_prices()
    if not prices:
        return "Tharnek ainda nao tem dados. Usa /precos para iniciar."
    return f"Tharnek monitoriza {len(prices)} produtos."
