import os
import json
import anthropic
from datetime import datetime

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
POSTS_FILE = "kaelvris_posts.json"

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

def generate_pinterest_post(article, top_product=None):
    """Gera post otimizado para Pinterest."""
    try:
        title = article.get("title", "")
        category = article.get("category", "")
        top = top_product.get("title", "") if top_product else ""

        prompt = f"""Cria um post para Pinterest sobre este artigo em portugues europeu.

Artigo: {title}
Categoria: {category}
Produto destaque: {top}

Formato:
- Titulo do pin (max 100 chars, com palavra-chave)
- Descricao (max 500 chars, com hashtags relevantes)
- 15 hashtags relevantes separadas por virgula

Sê direto e apelativo. Portugues europeu."""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Erro Pinterest: {e}"

def generate_facebook_post(article, top_product=None):
    """Gera post para Facebook."""
    try:
        title = article.get("title", "")
        category = article.get("category", "")
        top = top_product.get("title", "") if top_product else ""
        price = top_product.get("price", "") if top_product else ""

        prompt = f"""Cria um post para Facebook sobre este artigo em portugues europeu.

Artigo: {title}
Categoria: {category}
Produto destaque: {top} — {price}

O post deve:
- Comecar com uma pergunta ou facto interessante
- Ter 2-3 paragrafos curtos
- Terminar com call-to-action para o site
- Ter 3-5 hashtags no final
- Soar natural, nao como publicidade
- Max 300 palavras"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Erro Facebook: {e}"

def generate_instagram_caption(article, top_product=None):
    """Gera legenda para Instagram."""
    try:
        title = article.get("title", "")
        category = article.get("category", "")

        prompt = f"""Cria uma legenda para Instagram sobre este artigo em portugues europeu.

Artigo: {title}
Categoria: {category}

A legenda deve:
- Ser curta e impactante (max 150 palavras)
- Ter emojis relevantes
- Terminar com CTA
- Ter 20-25 hashtags em portugues e ingles
- Tom informal e direto"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Erro Instagram: {e}"

def save_posts(article_id, posts):
    """Guarda posts gerados."""
    try:
        all_posts = {}
        if os.path.exists(POSTS_FILE):
            with open(POSTS_FILE, "r", encoding="utf-8") as f:
                all_posts = json.load(f)
        all_posts[article_id] = {
            **posts,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "pronto"
        }
        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Kaelvris erro guardar: {e}")

def load_posts():
    try:
        if os.path.exists(POSTS_FILE):
            with open(POSTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def create_all_posts(article, top_product=None):
    """Cria posts para todas as plataformas."""
    print(f"Kaelvris a criar posts para: {article.get('title', '')[:40]}")

    pinterest = generate_pinterest_post(article, top_product)
    facebook = generate_facebook_post(article, top_product)
    instagram = generate_instagram_caption(article, top_product)

    posts = {
        "article_title": article.get("title", ""),
        "category": article.get("category", ""),
        "pinterest": pinterest,
        "facebook": facebook,
        "instagram": instagram
    }

    save_posts(article.get("id", "unknown"), posts)
    return posts

def format_posts_for_telegram(posts, platform="all"):
    """Formata posts para envio no Telegram."""
    lines = [f"*Kaelvris — Posts Prontos*\n"]
    lines.append(f"_Artigo: {posts.get('article_title', '')[:50]}_\n")

    if platform in ["all", "pinterest"]:
        lines.append("*Pinterest:*")
        lines.append(posts.get("pinterest", "N/D")[:600])
        lines.append("")

    if platform in ["all", "facebook"]:
        lines.append("*Facebook:*")
        lines.append(posts.get("facebook", "N/D")[:600])
        lines.append("")

    if platform in ["all", "instagram"]:
        lines.append("*Instagram:*")
        lines.append(posts.get("instagram", "N/D")[:600])

    return "\n".join(lines)

def get_stats():
    posts = load_posts()
    if not posts:
        return "Kaelvris ainda nao criou posts."
    return f"Kaelvris criou posts para {len(posts)} artigos."
