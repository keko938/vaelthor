import os
import json
import time
import anthropic
from datetime import datetime

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "ranktuga-21")
ARTICLES_FILE = "sylvorn_articles.json"

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# ============================================================
# GERADOR DE ARTIGOS
# ============================================================

def generate_article(category_name, products):
    """Gera artigo completo em português europeu para uma categoria."""

    top_products = products[:7]
    product_list = ""
    for p in top_products:
        product_list += f"- {p['title']} | Preço: {p['price']} | Avaliação: {p['rating']}/5 | Link: {p['url']}\n"

    prompt = f"""Escreve um artigo de comparação de produtos em português europeu (Portugal) para o site ranktuga.com.

Categoria: {category_name}
Produtos a comparar:
{product_list}

INSTRUÇÕES:
- Escreve em português europeu (nunca brasileiro)
- Tom informal mas informativo, como um amigo que percebe do assunto
- Inclui nota de transparência sobre links de afiliado
- Estrutura obrigatória:
  1. Título SEO (começa com "Melhor" ou "Os X melhores")
  2. Meta descrição (máximo 155 caracteres)
  3. URL sugerido (slug simples)
  4. Introdução (2-3 parágrafos, menciona o problema que resolve)
  5. Tabela comparativa resumo (markdown)
  6. Review de cada produto (título H3, descrição 2-3 parágrafos, prós, contras, para quem é, botão comprar)
  7. Guia de compra (como escolher)
  8. Conclusão com recomendação clara
  9. FAQ com 4-5 perguntas

IMPORTANTE:
- Cada review deve ter entre 150-200 palavras
- Os links de afiliado já estão nos dados — usa-os nos botões "Ver preço na Amazon"
- Artigo final deve ter 1800-2500 palavras
- Não uses adjetivos exagerados como "incrível" ou "fantástico"
- Sê honesto sobre as limitações de cada produto

Formata em Markdown pronto para copiar para WordPress."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Erro ao gerar artigo para {category_name}: {e}")
        return None

def generate_quick_article(product):
    """Gera artigo de review individual de um produto específico."""

    prompt = f"""Escreve uma review completa em português europeu (Portugal) para o produto:

Produto: {product['title']}
Preço: {product['price']}
Avaliação: {product['rating']}/5
Categoria: {product['category']}
Link: {product['url']}

ESTRUTURA:
1. Título SEO com a palavra-chave principal
2. Meta descrição (155 chars)
3. URL sugerido
4. Introdução (1-2 parágrafos)
5. Especificações principais (tabela markdown)
6. Análise detalhada (design, desempenho, facilidade de uso, qualidade/preço)
7. Prós e contras (listas)
8. Para quem é este produto
9. Veredicto final com nota /10
10. FAQ (3 perguntas)

Tom: honesto, direto, português europeu.
Tamanho: 1000-1500 palavras.
Formata em Markdown."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Erro ao gerar review: {e}")
        return None

# ============================================================
# GESTÃO DE ARTIGOS
# ============================================================

def load_articles():
    try:
        if os.path.exists(ARTICLES_FILE):
            with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []

def save_article(article):
    articles = load_articles()
    articles.append(article)
    try:
        with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao guardar artigo: {e}")
        return False

def save_article_file(title, content, category):
    """Guarda artigo em ficheiro .md separado."""
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
    safe_title = safe_title[:50].replace(" ", "_").lower()
    filename = f"artigo_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return filename
    except Exception as e:
        print(f"Erro ao guardar ficheiro: {e}")
        return None

def get_stats():
    articles = load_articles()
    if not articles:
        return "Sem artigos gerados ainda."

    by_category = {}
    for a in articles:
        cat = a.get("category", "Outro")
        by_category[cat] = by_category.get(cat, 0) + 1

    stats = f"Total: {len(articles)} artigos\n"
    for cat, count in by_category.items():
        stats += f"- {cat}: {count}\n"
    return stats

# ============================================================
# FUNÇÕES PRINCIPAIS
# ============================================================

def create_category_article(category_name, products):
    """Cria artigo de comparação para uma categoria completa."""
    print(f"Sylvorn a gerar artigo para: {category_name}...")

    if not products:
        return None, "Sem produtos para esta categoria."

    content = generate_article(category_name, products)
    if not content:
        return None, "Erro ao gerar conteúdo."

    # Extrai título da primeira linha
    lines = content.strip().split('\n')
    title = lines[0].replace('#', '').strip() if lines else f"Melhores {category_name}"

    article = {
        "id": f"art_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "title": title,
        "category": category_name,
        "content": content,
        "status": "rascunho",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "word_count": len(content.split()),
        "products_count": len(products[:7])
    }

    save_article(article)
    filename = save_article_file(title, content, category_name)

    return article, filename

def create_product_review(product):
    """Cria review individual de um produto."""
    print(f"Sylvorn a gerar review: {product['title']}...")

    content = generate_quick_article(product)
    if not content:
        return None, "Erro ao gerar conteúdo."

    lines = content.strip().split('\n')
    title = lines[0].replace('#', '').strip()

    article = {
        "id": f"rev_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "title": title,
        "category": product.get("category", "Geral"),
        "content": content,
        "status": "rascunho",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "word_count": len(content.split()),
        "product_asin": product.get("asin", "")
    }

    save_article(article)
    filename = save_article_file(title, content, product.get("category", ""))

    return article, filename

def list_articles(limit=10):
    """Lista artigos criados."""
    articles = load_articles()
    if not articles:
        return "Sem artigos ainda. Usa /artigo para criar o primeiro."

    lines = [f"*Artigos criados pelo Sylvorn ({len(articles)} total):*\n"]
    for a in articles[-limit:]:
        status = "✅" if a.get("status") == "publicado" else "📝"
        words = a.get("word_count", 0)
        lines.append(f"{status} {a['title'][:50]}...")
        lines.append(f"   _{a['category']} | {words} palavras | {a['created_at']}_\n")

    return "\n".join(lines)

def get_latest_article_content():
    """Retorna conteúdo do último artigo gerado."""
    articles = load_articles()
    if not articles:
        return None
    return articles[-1]
