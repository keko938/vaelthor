import os
import re
import json
import anthropic
from datetime import datetime

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
SEO_FILE = "myrondis_seo.json"

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

def analyze_article_seo(article):
    """Analisa um artigo e da recomendacoes SEO."""
    content = article.get("content", "")
    title = article.get("title", "")
    category = article.get("category", "")
    word_count = article.get("word_count", 0)

    # Analise basica sem API
    issues = []
    score = 100

    # 1. Contagem de palavras
    if word_count < 1200:
        issues.append(("⚠️", "Artigo curto", f"Tem {word_count} palavras. O ideal e 1500+"))
        score -= 15
    elif word_count > 1500:
        issues.append(("✅", "Tamanho ideal", f"{word_count} palavras — bom para SEO"))

    # 2. Titulo
    if len(title) < 30:
        issues.append(("⚠️", "Titulo curto", "O titulo deve ter 40-60 caracteres"))
        score -= 10
    elif len(title) > 65:
        issues.append(("⚠️", "Titulo longo", f"O titulo tem {len(title)} chars — ideal e max 60"))
        score -= 5
    else:
        issues.append(("✅", "Titulo bom", f"{len(title)} caracteres"))

    # 3. Meta descricao
    if "meta descri" in content.lower():
        issues.append(("✅", "Meta descricao presente", ""))
    else:
        issues.append(("⚠️", "Meta descricao em falta", "Adiciona uma meta descricao de 155 chars"))
        score -= 10

    # 4. Tabela comparativa
    if "|" in content and "---" in content:
        issues.append(("✅", "Tabela comparativa presente", ""))
    else:
        issues.append(("⚠️", "Sem tabela", "Adiciona uma tabela comparativa"))
        score -= 10

    # 5. H2/H3 headings
    h2_count = content.count("## ")
    h3_count = content.count("### ")
    if h2_count >= 3:
        issues.append(("✅", f"Estrutura boa", f"{h2_count} H2 + {h3_count} H3"))
    else:
        issues.append(("⚠️", "Poucos headings", f"So {h2_count} H2. Adiciona mais secoes"))
        score -= 10

    # 6. FAQ
    if "faq" in content.lower() or "pergunta" in content.lower():
        issues.append(("✅", "FAQ presente", "Bom para featured snippets"))
    else:
        issues.append(("⚠️", "Sem FAQ", "Adiciona 4-5 perguntas frequentes"))
        score -= 5

    # 7. Links de afiliado
    affiliate_links = content.count("amazon.es")
    if affiliate_links >= 3:
        issues.append(("✅", f"Links afiliado OK", f"{affiliate_links} links Amazon"))
    else:
        issues.append(("⚠️", "Poucos links afiliado", f"So {affiliate_links} links. Adiciona mais"))
        score -= 10

    # 8. Palavra-chave no titulo
    kw = category.lower().split()[0] if category else ""
    if kw and kw in title.lower():
        issues.append(("✅", "Palavra-chave no titulo", ""))
    else:
        issues.append(("⚠️", "Palavra-chave em falta no titulo", f"Inclui '{category}' no titulo"))
        score -= 5

    return {
        "score": max(score, 0),
        "issues": issues,
        "word_count": word_count,
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

def get_ai_seo_tips(article):
    """Usa Claude para dar dicas SEO mais avancadas."""
    try:
        content_preview = article.get("content", "")[:800]
        category = article.get("category", "")

        prompt = f"""Analisa este artigo de afiliado sobre {category} e da 3 dicas SEO especificas e acionaveis em portugues europeu. Sê direto e pratico. Max 150 palavras total.

Preview do artigo:
{content_preview}"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Erro ao obter dicas AI: {e}"

def save_seo_report(article_id, report):
    """Guarda relatorio SEO."""
    try:
        reports = {}
        if os.path.exists(SEO_FILE):
            with open(SEO_FILE, "r", encoding="utf-8") as f:
                reports = json.load(f)
        reports[article_id] = report
        with open(SEO_FILE, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Myrondis erro: {e}")

def format_seo_report(article, analysis, ai_tips=""):
    """Formata relatorio SEO para Telegram."""
    score = analysis["score"]
    emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"

    lines = [
        f"*Myrondis — Analise SEO*\n",
        f"{emoji} *Score: {score}/100*",
        f"_{article.get('title', '')[:50]}_\n",
        "*Checklist:*"
    ]

    for icon, title, detail in analysis["issues"]:
        line = f"{icon} {title}"
        if detail:
            line += f"\n   _{detail}_"
        lines.append(line)

    if ai_tips:
        lines.append(f"\n*Dicas Myrondis (IA):*\n{ai_tips}")

    lines.append(f"\n_Analisado em {analysis['analyzed_at']}_")
    return "\n".join(lines)

def analyze_keywords(category):
    """Sugere palavras-chave para uma categoria."""
    keywords = {
        "Air Fryers": [
            "melhor air fryer portugal",
            "air fryer qual comprar",
            "fritadeira sem oleo",
            "air fryer 2025",
            "melhor air fryer qualidade preco"
        ],
        "Aspiradores Robo": [
            "melhor aspirador robo",
            "aspirador robot qual comprar",
            "roomba alternativa barata",
            "aspirador robo portugal 2025",
            "melhor aspirador autonomo"
        ],
        "Robots de Cozinha": [
            "melhor robot cozinha",
            "alternativa bimby barata",
            "robot cozinha qual comprar",
            "thermomix vs monsieur cuisine",
            "melhor robot cozinha portugal"
        ],
        "Produtos para Bebe": [
            "melhor carrinho bebe",
            "cadeirinha auto qual comprar",
            "monitor bebe recomendado",
            "berco co-sleeping portugal",
            "produtos bebe essenciais"
        ],
        "Racoes para Animais": [
            "melhor racao cao portugal",
            "racao gato recomendada",
            "royal canin vs hills",
            "racao natural cao",
            "melhor racao qualidade preco"
        ]
    }
    return keywords.get(category, [])
