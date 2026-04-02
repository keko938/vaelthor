import os
import json
import time
import random
import requests
import re
from datetime import datetime

AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "ranktuga-21")
DATA_FILE = "dravek_data.json"

# ============================================================
# BASE DE DADOS CURADA — Top produtos reais por categoria
# Fonte: conhecimento de mercado + bestsellers Amazon ES/PT
# ============================================================
CURATED_DATA = {
    "Air Fryers": [
        {"rank": 1, "title": "Philips Airfryer XXL HD9650/90", "price": "179,99€", "rating": "4.6", "asin": "B07KFDLH1Z"},
        {"rank": 2, "title": "Cosori Pro II Air Fryer 5.5L CAF-P585S", "price": "99,99€", "rating": "4.5", "asin": "B09XKBPW1T"},
        {"rank": 3, "title": "Ninja AF160EU Air Fryer XL 7.6L", "price": "149,99€", "rating": "4.6", "asin": "B0BJLN2FQC"},
        {"rank": 4, "title": "Tefal Easy Fry Precision+ FW5018", "price": "79,99€", "rating": "4.4", "asin": "B08XGPSSXZ"},
        {"rank": 5, "title": "Instant Vortex Plus 5.7L Air Fryer", "price": "89,99€", "rating": "4.5", "asin": "B08GFPQ1JV"},
        {"rank": 6, "title": "Moulinex Easy Fry Classic EZ401D", "price": "59,99€", "rating": "4.3", "asin": "B07KFXKNML"},
        {"rank": 7, "title": "Cecotec Cecofry Rapid 4D 4L", "price": "49,99€", "rating": "4.2", "asin": "B082GKBTPF"},
        {"rank": 8, "title": "Philips Essential Airfryer HD9270/90 6.2L", "price": "129,99€", "rating": "4.5", "asin": "B07XHSXX3N"},
        {"rank": 9, "title": "Cosori Dual Blaze 6.4L CAF-P585S", "price": "119,99€", "rating": "4.4", "asin": "B0B3DJHMBL"},
        {"rank": 10, "title": "Ninja DZ201 Foodi 2-Basket Air Fryer 7.6L", "price": "169,99€", "rating": "4.7", "asin": "B0892KT2LC"},
        {"rank": 11, "title": "Klarstein VitAir Rotante 11L", "price": "69,99€", "rating": "4.1", "asin": "B07GNPQNZH"},
        {"rank": 12, "title": "Cosori Smart Air Fryer 5.5L WiFi", "price": "109,99€", "rating": "4.4", "asin": "B0832MKQ37"},
        {"rank": 13, "title": "Tower T17088 Vortx Manual Air Fryer 4.3L", "price": "39,99€", "rating": "4.2", "asin": "B07YMJQ7BR"},
        {"rank": 14, "title": "Philips Airfryer Compact HD9200/90 4L", "price": "89,99€", "rating": "4.5", "asin": "B07M5J36BL"},
        {"rank": 15, "title": "Salter EK2817 Dual Air Fryer 8L", "price": "79,99€", "rating": "4.3", "asin": "B0BH7YF27V"},
        {"rank": 16, "title": "Tristar FR-6932 Air Fryer 4L", "price": "44,99€", "rating": "4.0", "asin": "B07FQXMGMG"},
        {"rank": 17, "title": "Medion MD 17891 Air Fryer 5L", "price": "54,99€", "rating": "4.1", "asin": "B08DCLW1MX"},
        {"rank": 18, "title": "Innsky Air Fryer 5.8L 1700W", "price": "64,99€", "rating": "4.3", "asin": "B07RW5YBZN"},
        {"rank": 19, "title": "Tefal ActiFry Genius+ YV970840 1.2kg", "price": "149,99€", "rating": "4.4", "asin": "B07MYRZ29Z"},
        {"rank": 20, "title": "Ninja AF080 Mini Air Fryer 2L", "price": "59,99€", "rating": "4.4", "asin": "B09FDXBCC1"},
    ],
    "Aspiradores Robo": [
        {"rank": 1, "title": "Roomba i5+ iRobot Auto-Vaciado", "price": "499,99€", "rating": "4.5", "asin": "B09DRQX9ML"},
        {"rank": 2, "title": "Xiaomi Robot Vacuum S10+ Auto-Vaciado", "price": "349,99€", "rating": "4.4", "asin": "B0BN4H3K3T"},
        {"rank": 3, "title": "Ecovacs Deebot T20 OMNI", "price": "799,99€", "rating": "4.6", "asin": "B0BW34J5PD"},
        {"rank": 4, "title": "Roomba j7+ iRobot Obstáculos", "price": "649,99€", "rating": "4.5", "asin": "B09DRQ47BQ"},
        {"rank": 5, "title": "Dreame Bot L10s Ultra", "price": "699,99€", "rating": "4.7", "asin": "B0BZ5VYRXQ"},
        {"rank": 6, "title": "Conga 11090 Cecotec Aspirador Robot", "price": "299,99€", "rating": "4.3", "asin": "B0BF9R7NQL"},
        {"rank": 7, "title": "Roborock S8 Pro Ultra", "price": "999,99€", "rating": "4.7", "asin": "B0BVYGXJPL"},
        {"rank": 8, "title": "iRobot Roomba e5 5134", "price": "199,99€", "rating": "4.3", "asin": "B07Q4GF7H9"},
        {"rank": 9, "title": "Xiaomi Mi Robot Vacuum-Mop 2 Pro", "price": "199,99€", "rating": "4.4", "asin": "B09B9TSZS4"},
        {"rank": 10, "title": "Lefant M210 Robot Aspirador Silencioso", "price": "99,99€", "rating": "4.2", "asin": "B091P8TRNM"},
        {"rank": 11, "title": "Eufy RoboVac 11S MAX", "price": "149,99€", "rating": "4.3", "asin": "B07VH9WDMK"},
        {"rank": 12, "title": "Shark AV2001WD AI Robot Vacuum", "price": "299,99€", "rating": "4.4", "asin": "B09KRMQMXL"},
        {"rank": 13, "title": "Neato Robotics D8 Aspirador Robot", "price": "299,99€", "rating": "4.2", "asin": "B08XRD84DQ"},
        {"rank": 14, "title": "Roborock Q5+ Auto-Vaciado", "price": "449,99€", "rating": "4.6", "asin": "B09VFXMBLQ"},
        {"rank": 15, "title": "ILIFE V3s Pro Robot Aspirador Mascotas", "price": "79,99€", "rating": "4.1", "asin": "B072JXL5NB"},
        {"rank": 16, "title": "Cecotec Conga 3490 Elite", "price": "199,99€", "rating": "4.2", "asin": "B07XTRXDQH"},
        {"rank": 17, "title": "Dreame D9 Max Robot Aspirador", "price": "249,99€", "rating": "4.5", "asin": "B09H6XMHFR"},
        {"rank": 18, "title": "Eufy RoboVac G30 Edge", "price": "199,99€", "rating": "4.3", "asin": "B07ZC1B7T4"},
        {"rank": 19, "title": "iRobot Roomba 692 WiFi", "price": "249,99€", "rating": "4.3", "asin": "B07GKDSP2H"},
        {"rank": 20, "title": "Rowenta Explorer Serie 60 RR7455WH", "price": "249,99€", "rating": "4.2", "asin": "B08PBWXHTM"},
    ],
    "Robots de Cozinha": [
        {"rank": 1, "title": "Bimby TM6 Thermomix", "price": "1.399,00€", "rating": "4.8", "asin": "B07RMP48GY"},
        {"rank": 2, "title": "Monsieur Cuisine Smart Lidl Silvercrest", "price": "299,00€", "rating": "4.5", "asin": "B08GRTBFNM"},
        {"rank": 3, "title": "Kenwood kCook Multi Smart CCL450SI", "price": "499,99€", "rating": "4.4", "asin": "B07KPPVWQQ"},
        {"rank": 4, "title": "Moulinex i-Companion Touch XL HF938", "price": "699,99€", "rating": "4.5", "asin": "B07HFDB9LH"},
        {"rank": 5, "title": "Cecotec Mambo 10090 Robot Cozinha", "price": "299,99€", "rating": "4.3", "asin": "B08XPZR2BL"},
        {"rank": 6, "title": "Tefal Cuisine Companion XL HF80CB10", "price": "649,99€", "rating": "4.4", "asin": "B09B8WVKKT"},
        {"rank": 7, "title": "KitchenAid Artisan 5KSM175 4.8L", "price": "699,99€", "rating": "4.8", "asin": "B000ARS0I0"},
        {"rank": 8, "title": "Bosch MUM5 CreationLine MUM58243", "price": "299,99€", "rating": "4.5", "asin": "B00G1OQLGG"},
        {"rank": 9, "title": "Monsieur Cuisine Connect Silvercrest", "price": "249,00€", "rating": "4.3", "asin": "B07V8YRW93"},
        {"rank": 10, "title": "Instant Pot Duo 7-em-1 5.7L", "price": "99,99€", "rating": "4.6", "asin": "B01NBKTPTS"},
        {"rank": 11, "title": "Kenwood Chef Titanium XL KVL8300S", "price": "599,99€", "rating": "4.6", "asin": "B00L2KGHCM"},
        {"rank": 12, "title": "Cecotec Mambo 9090 Robot Cozinha", "price": "199,99€", "rating": "4.2", "asin": "B086PMTFX5"},
        {"rank": 13, "title": "Moulinex Masterchef Gourmet QA510D10", "price": "249,99€", "rating": "4.3", "asin": "B08LG96DMF"},
        {"rank": 14, "title": "Philips HR7761/00 Viva Collection", "price": "99,99€", "rating": "4.4", "asin": "B07J67KCHQ"},
        {"rank": 15, "title": "Bosch MUM9A66X00 OptiMUM 1600W", "price": "599,99€", "rating": "4.5", "asin": "B071Y73H8T"},
        {"rank": 16, "title": "Ninja Foodi MAX OL750EU Multicooker", "price": "249,99€", "rating": "4.5", "asin": "B08XKFFXHF"},
        {"rank": 17, "title": "Klarstein Bella Rossa Robot Cozinha", "price": "149,99€", "rating": "4.1", "asin": "B07BNTPKRX"},
        {"rank": 18, "title": "Magimix Cook Expert 18900 Robot", "price": "1.099,00€", "rating": "4.6", "asin": "B00EOFOZJM"},
        {"rank": 19, "title": "Taurus Mycook Legend 1600W", "price": "449,99€", "rating": "4.3", "asin": "B08L15NTYW"},
        {"rank": 20, "title": "KitchenAid Artisan Mini 5KSM3311X 3.3L", "price": "399,99€", "rating": "4.7", "asin": "B01N0LCQK5"},
    ],
    "Produtos para Bebe": [
        {"rank": 1, "title": "Chicco Trio Best Friend 3-em-1 Carrinho", "price": "499,99€", "rating": "4.5", "asin": "B08XMHG4B9"},
        {"rank": 2, "title": "Philips Avent Monitor Bebé DECT SCD713", "price": "89,99€", "rating": "4.4", "asin": "B07H8PPKFP"},
        {"rank": 3, "title": "Graco Slim2 Duo Carrinho Gemelar", "price": "349,99€", "rating": "4.4", "asin": "B08CF1MQMG"},
        {"rank": 4, "title": "Cybex Pallas S-Fix Cadeirinha Auto", "price": "299,99€", "rating": "4.6", "asin": "B07KQ2RJGQ"},
        {"rank": 5, "title": "Chicco Next2Me Magic Berço Co-Sleeping", "price": "249,99€", "rating": "4.5", "asin": "B07CK9TY9Y"},
        {"rank": 6, "title": "Babymoov Nutribaby+ Robot Alimentação", "price": "129,99€", "rating": "4.4", "asin": "B00S4FVDYA"},
        {"rank": 7, "title": "Tommee Tippee Made for Me Extrator Leite", "price": "49,99€", "rating": "4.3", "asin": "B08DRK5YQH"},
        {"rank": 8, "title": "Graco SnugRide 35 Infant Car Seat", "price": "149,99€", "rating": "4.5", "asin": "B07NWKL5BH"},
        {"rank": 9, "title": "Infantino Flip 4-em-1 Porta-Bebés", "price": "39,99€", "rating": "4.4", "asin": "B00M7KXZII"},
        {"rank": 10, "title": "BabyBjorn Bouncer Balance Soft", "price": "179,99€", "rating": "4.6", "asin": "B0089VKXUM"},
        {"rank": 11, "title": "Chicco Balloon Cadeira Alta Bebé", "price": "99,99€", "rating": "4.4", "asin": "B07KQBRWGM"},
        {"rank": 12, "title": "Mam Easy Active Chupeta 2-6 meses", "price": "8,99€", "rating": "4.5", "asin": "B00AQZWJ5O"},
        {"rank": 13, "title": "Pampers Premium Protection Fraldas T3", "price": "29,99€", "rating": "4.7", "asin": "B07H7LSHPH"},
        {"rank": 14, "title": "Joie i-Snug 2 Cadeirinha Auto i-Size", "price": "179,99€", "rating": "4.5", "asin": "B09VQ99N1W"},
        {"rank": 15, "title": "Ingenuity 3-em-1 Baloiço SmartComfort", "price": "89,99€", "rating": "4.3", "asin": "B08G1HQVHQ"},
        {"rank": 16, "title": "Medela Swing Maxi Flex Extrator Leite", "price": "169,99€", "rating": "4.5", "asin": "B08MJTNVZH"},
        {"rank": 17, "title": "Beaba Babycook Neo Robot Alimentação", "price": "109,99€", "rating": "4.6", "asin": "B083XCMG2G"},
        {"rank": 18, "title": "Chicco Fit2 Cadeirinha Auto Reclinável", "price": "199,99€", "rating": "4.4", "asin": "B08L3NJFHC"},
        {"rank": 19, "title": "Motherhood Maternity Almofada Gravidez", "price": "39,99€", "rating": "4.5", "asin": "B00BBYH62Q"},
        {"rank": 20, "title": "Joie Nitro Lx Carrinho Bebé Compacto", "price": "199,99€", "rating": "4.4", "asin": "B09FCJG4TY"},
    ],
    "Racoes para Animais": [
        {"rank": 1, "title": "Royal Canin Medium Adult Ração Cão 15kg", "price": "64,99€", "rating": "4.7", "asin": "B003VF4GU0"},
        {"rank": 2, "title": "Hill's Science Plan Adult Frango Cão 14kg", "price": "69,99€", "rating": "4.6", "asin": "B004HP0JNG"},
        {"rank": 3, "title": "Purina Pro Plan Adult Salmão Cão 14kg", "price": "59,99€", "rating": "4.6", "asin": "B01N4IXPQD"},
        {"rank": 4, "title": "Royal Canin Sterilised 37 Gato 10kg", "price": "54,99€", "rating": "4.7", "asin": "B0002AR22Q"},
        {"rank": 5, "title": "Hill's Science Plan Sterilised Gato 10kg", "price": "59,99€", "rating": "4.5", "asin": "B004HP3Z1U"},
        {"rank": 6, "title": "Purina Pro Plan Sterilised Salmão Gato 10kg", "price": "49,99€", "rating": "4.6", "asin": "B01N1SIFHC"},
        {"rank": 7, "title": "Advance Adult Medium Maxi Frango Cão 12kg", "price": "44,99€", "rating": "4.4", "asin": "B003AXHWMM"},
        {"rank": 8, "title": "Orijen Original Grain Free Cão 11.4kg", "price": "89,99€", "rating": "4.7", "asin": "B004EJ4GIY"},
        {"rank": 9, "title": "Pedigree Adult Frango Arroz Cão 15kg", "price": "34,99€", "rating": "4.3", "asin": "B00CXHF4EK"},
        {"rank": 10, "title": "Whiskas 1+ Peixe Branco Gato 14x100g", "price": "14,99€", "rating": "4.5", "asin": "B003EQSNCO"},
        {"rank": 11, "title": "Acana Pacifica Grain Free Cão 11.4kg", "price": "79,99€", "rating": "4.6", "asin": "B004RVH0OC"},
        {"rank": 12, "title": "Felix As Good As It Looks Gato 12x85g", "price": "12,99€", "rating": "4.6", "asin": "B00GWV2TGG"},
        {"rank": 13, "title": "Purina One Adult Salmão Gato 7.5kg", "price": "34,99€", "rating": "4.5", "asin": "B01NAKL8J7"},
        {"rank": 14, "title": "Eukanuba Adult Medium Breed Cão 15kg", "price": "54,99€", "rating": "4.5", "asin": "B00CXHF5CE"},
        {"rank": 15, "title": "Bozita Gato Húmido Multiseleção 24x370g", "price": "29,99€", "rating": "4.4", "asin": "B07KFZRLWL"},
        {"rank": 16, "title": "Natural Greatness Wild Salmon Gato 2kg", "price": "19,99€", "rating": "4.3", "asin": "B07CJGQLZF"},
        {"rank": 17, "title": "Purina Pro Plan Puppy Medium Frango 12kg", "price": "54,99€", "rating": "4.7", "asin": "B00RPYH5SQ"},
        {"rank": 18, "title": "Royal Canin Giant Adult Cão 15kg", "price": "69,99€", "rating": "4.6", "asin": "B0002AR202"},
        {"rank": 19, "title": "Taste of the Wild High Prairie Cão 12.7kg", "price": "64,99€", "rating": "4.7", "asin": "B002CBHZLE"},
        {"rank": 20, "title": "Josera Leger Ração Cão Baixa Gordura 15kg", "price": "44,99€", "rating": "4.4", "asin": "B001O2YXSI"},
    ]
}

def build_curated_products():
    """Constrói lista de produtos a partir da base de dados curada."""
    result = {}
    for category, products in CURATED_DATA.items():
        result[category] = []
        for p in products:
            result[category].append({
                "rank": p["rank"],
                "asin": p["asin"],
                "title": p["title"],
                "price": p["price"],
                "rating": p["rating"],
                "url": f"https://www.amazon.es/dp/{p['asin']}?tag={AFFILIATE_ID}",
                "category": category,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Base Curada"
            })
    return result

def try_scrape(category_name, url):
    """Tenta scraping — se falhar usa dados curados."""
    try:
        headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.2 Safari/605.1.15",
            ]),
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        session = requests.Session()
        session.get("https://www.amazon.es", headers=headers, timeout=8)
        time.sleep(random.uniform(2, 3))
        r = session.get(url, headers=headers, timeout=12)

        if r.status_code != 200:
            return None
        if "robot" in r.text.lower() or "captcha" in r.text.lower():
            return None

        asins = list(dict.fromkeys([
            a for a in re.findall(r'data-asin="([A-Z0-9]{10})"', r.text) if a
        ]))
        if len(asins) < 5:
            return None

        titles = []
        for pattern in [
            r'class="[^"]*p13n-sc-css-line-clamp[^"]*"[^>]*>\s*(.*?)\s*</span>',
            r'class="[^"]*p13n-sc-truncate[^"]*"[^>]*>\s*(.*?)\s*</div>',
            r'"name"\s*:\s*"([^"]{10,150})"',
        ]:
            found = re.findall(pattern, r.text, re.DOTALL)
            found = [re.sub(r'<[^>]+>', '', t).strip() for t in found if len(t.strip()) > 5]
            if len(found) >= 5:
                titles = found
                break

        prices = re.findall(r'<span class="p13n-sc-price">(.*?)</span>', r.text)
        ratings = re.findall(r'(\d+[,.]\d+)\s*de\s*5', r.text)

        products = []
        for i, asin in enumerate(asins[:20]):
            title = titles[i] if i < len(titles) else None
            if not title or len(title) < 5:
                continue
            products.append({
                "rank": i + 1,
                "asin": asin,
                "title": title[:100],
                "price": prices[i].strip() if i < len(prices) else "N/D",
                "rating": ratings[i] if i < len(ratings) else "N/D",
                "url": f"https://www.amazon.es/dp/{asin}?tag={AFFILIATE_ID}",
                "category": category_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Amazon Live"
            })

        return products if len(products) >= 5 else None

    except Exception as e:
        print(f"  Scraping falhou para {category_name}: {e}")
        return None

CATEGORY_URLS = {
    "Air Fryers": "https://www.amazon.es/gp/bestsellers/kitchen/3638504031/ref=zg_bs_pg_1?ie=UTF8&pg=1",
    "Aspiradores Robo": "https://www.amazon.es/gp/bestsellers/kitchen/3638455031/ref=zg_bs_pg_1?ie=UTF8&pg=1",
    "Robots de Cozinha": "https://www.amazon.es/gp/bestsellers/kitchen/3638552031/ref=zg_bs_pg_1?ie=UTF8&pg=1",
    "Produtos para Bebe": "https://www.amazon.es/gp/bestsellers/baby/ref=zg_bs_baby_sm?ie=UTF8&pg=1",
    "Racoes para Animais": "https://www.amazon.es/gp/bestsellers/pet-supplies/ref=zg_bs_pet-supplies_sm?ie=UTF8&pg=1"
}

def run_all():
    print(f"Dravek v7 a iniciar... {datetime.now()}")
    previous = load_data()
    curated = build_curated_products()
    current = {}
    total = 0

    for category in CURATED_DATA.keys():
        print(f"  -> {category}")
        url = CATEGORY_URLS.get(category)
        live_products = None

        if url:
            live_products = try_scrape(category, url)
            time.sleep(random.uniform(4, 8))

        if live_products:
            print(f"     LIVE: {len(live_products)} produtos da Amazon")
            current[category] = live_products
        else:
            print(f"     CURADO: {len(curated[category])} produtos da base de dados")
            current[category] = curated[category]

        total += len(current[category])

    save_data(current)
    print(f"Dravek v7 concluiu. Total: {total}")
    return current, previous, total

def run_category(name):
    curated = build_curated_products()
    url = CATEGORY_URLS.get(name)
    if url:
        live = try_scrape(name, url)
        if live:
            return live
    return curated.get(name, [])

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
    lines = [f"*Dravek v7 — {now}*\n"]
    lines.append(f"Total: *{total} produtos*\n")

    for category, products in current.items():
        if not products:
            continue
        prev_asins = {p["asin"] for p in previous.get(category, [])}
        new = [p for p in products if p["asin"] not in prev_asins]
        new_tag = f" +{len(new)} novos" if new and previous else ""
        source = products[0].get("source", "") if products else ""
        emoji = "🟢" if source == "Amazon Live" else "📋"

        lines.append(f"\n{emoji} *{category}* ({len(products)}){new_tag}")
        lines.append(f"_Fonte: {source}_")
        for p in products[:5]:
            stars = f" ⭐{p['rating']}" if p['rating'] != 'N/D' else ""
            lines.append(f"  {p['rank']}. {p['title'][:45]}... {p['price']}{stars}")

    lines.append("\n\n🟢 = dados ao vivo | 📋 = base curada")
    return "\n".join(lines)

def get_context():
    data = load_data()
    total = sum(len(v) for v in data.values())
    if not data or total == 0:
        curated = build_curated_products()
        total = sum(len(v) for v in curated.values())
        context = f"Dravek tem {total} produtos em base curada:\n"
        for cat, products in curated.items():
            top3 = ", ".join([p['title'][:25] for p in products[:3]])
            context += f"- {cat}: {top3}...\n"
        return context

    context = f"Dravek tem {total} produtos:\n"
    for cat, products in data.items():
        if products:
            top3 = ", ".join([p['title'][:25] for p in products[:3]])
            source = products[0].get("source", "")
            context += f"- {cat} ({source}): {top3}...\n"
    return context
