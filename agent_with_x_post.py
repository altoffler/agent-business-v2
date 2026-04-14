import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from groq import Groq
from tavily import TavilyClient
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import tweepy

# CONFIGURARE
TELEGRAM_TOKEN = "8199071513:AAHQVAvz-eE35Jmekm2-8Jj1KbrBbF5_AiA"
TELEGRAM_CHAT_ID = "1141081945"
TAVILY_API_KEY = "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"

# X (Twitter) Config
X_CONSUMER_KEY = "UjoJM8VqoJI08CNbiOi3V61yM"
X_CONSUMER_SECRET = "AAAAAAAAAAAAAAAAAAAAAHcH9AEAAAAAUHuPsOOYLv9N4KS0ZZC7Z7SBBbE%3DoRPsdSjWKHxRvIhR2qplt4jgoXPoG0lEHVjTk0hlYdRmIDZUdE"
X_ACCESS_TOKEN = "1488580767408168962-ZvsPPtL4rnilFtJw2BxZcCgYJ10NVs"
X_ACCESS_TOKEN_SECRET = "7kSrIH1DHqt4KzqnDhGML4GFNI4XERACjGDeJZtadcazh"

MEMORY_FILE = "/data/memory_index.json"

tavily = TavilyClient(api_key=TAVILY_API_KEY)

def remove_diacritics(text):
    """Inlocuieste diacriticele cu litere simple"""
    diacritics = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
    }
    for diacritic, plain in diacritics.items():
        text = text.replace(diacritic, plain)
    return text

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram eroare: {e}")
        return False

def post_to_x(message):
    """Posteaza pe X"""
    try:
        auth = tweepy.OAuth1UserHandler(
            X_CONSUMER_KEY, X_CONSUMER_SECRET,
            X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth)
        
        if len(message) > 280:
            message = message[:277] + "..."
        
        api.update_status(message)
        print("✅ Postat pe X cu succes!")
        send_telegram_message("🐦 Postare pe X realizata!")
        return True
    except Exception as e:
        print(f"❌ Eroare postare X: {e}")
        send_telegram_message(f"❌ Eroare postare X: {str(e)[:100]}")
        return False

def search_web(query):
    try:
        result = tavily.search(query=query, search_depth="basic", max_results=3)
        if result and "results" in result:
            return "\n".join([r["content"] for r in result["results"][:2]])
        return "Nu s-au gasit rezultate."
    except Exception as e:
        print(f"Search error: {e}")
        return f"Eroare: {e}"

def generate_landing_page(domain, opportunity, product_name, price):
    prompt = f"""Genereaza un site HTML complet pentru o afacere in domeniul {domain}.

Informatii:
- Nume produs/serviciu: {product_name}
- Pret: ${price}
- Oportunitate: {opportunity[:500]}

Site-ul trebuie sa contina:
1. Header cu numele produsului
2. Hero section (titlu + descriere)
3. Beneficii (3-4 bullet points)
4. Sectiune pret cu buton de cumparare
5. Footer cu contact
6. Design modern, responsive

Genereaza DOAR codul HTML."""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

class BusinessAgent:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.memory = self.load_memory()
    
    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        return {"analyses": {}}
    
    def save_memory(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.memory, f, indent=2)
    
    def research_market_with_search(self, domain):
        print(f"🔍 Caut informatii despre {domain}...")
        search_results = search_web(f"piata {domain} trenduri 2026")
        
        prompt = f"""Analizeaza piata pentru {domain}.

Informatii actualizate: {search_results}

Raspunde in 6-8 propozitii:
- Dimensiunea pietei
- Trenduri principale
- Gap-uri in piata
- Oportunitati concrete"""
        
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def analyze_competition_with_search(self, domain):
        print(f"🔍 Caut competitori pentru {domain}...")
        search_results = search_web(f"competitori {domain}")
        
        prompt = f"""Analizeaza competitorii pentru {domain}.

Informatii: {search_results}

Raspunde in 4-6 propozitii:
- Principalii competitori
- Oportunitatea ta de diferentiere"""
        
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def generate_business_names(self, domain):
        prompt = f"""Genereaza 8 nume creative pentru o afacere in {domain}.
Un nume pe linie, scurte, usor de pronuntat."""
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def generate_sales_script(self, domain, opportunity):
        prompt = f"""Genereaza un script de vanzari (email) pentru {domain}.
Oportunitate: {opportunity[:300]}
Lungime: maxim 12 randuri."""
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def generate_leads(self, domain):
        print(f"🔍 Caut potentiali clienti pentru {domain}...")
        search_results = search_web(f"companii care au nevoie de {domain}")
        
        prompt = f"""Genereaza 5 potentiali clienti pentru {domain}.

Informatii: {search_results}

Fiecare linie: Nume companie - Motiv nevoie"""
        
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def generate_product_name_and_price(self, domain, opportunity):
        prompt = f"""Genereaza un nume de produs si un pret pentru o afacere in {domain}.
Oportunitate: {opportunity[:300]}

Raspunde exact in formatul:
PRODUS: [nume produs]
PRET: [numar]"""
        
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def create_x_post(self, domain, product_name, price):
        prompt = f"""Creeaza un text scurt (maxim 250 caractere) pentru a promova o afacere.

Domeniu: {domain}
Produs: {product_name}
Pret: ${price}

Textul trebuie sa fie captivant, sa atraga atentia si sa includa un hashtag relevant.
Doar textul, fara alte explicatii."""
        
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def full_analysis(self, domain):
        print(f"Analizez: {domain}")
        send_telegram_message(f"🔍 Analiza inceputa: {domain}")
        
        market = self.research_market_with_search(domain)
        competition = self.analyze_competition_with_search(domain)
        names = self.generate_business_names(domain)
        sales_script = self.generate_sales_script(domain, competition)
        leads = self.generate_leads(domain)
        
        product_info = self.generate_product_name_and_price(domain, competition)
        
        product_name = "Produsul tau"
        price = "49"
        for line in product_info.split("\n"):
            if line.startswith("PRODUS:"):
                product_name = line.replace("PRODUS:", "").strip()
            elif line.startswith("PRET:"):
                price = line.replace("PRET:", "").strip()
        
        print("🌐 Generez landing page...")
        send_telegram_message(f"🌐 Generez site pentru {domain}...")
        html = generate_landing_page(domain, competition, product_name, price)
        
        site_filename = f"/data/landing_{domain.replace(' ', '_')}.html"
        with open(site_filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Site generat: {site_filename}")
        
        print("🐦 Generez postare pentru X...")
        x_post_text = self.create_x_post(domain, product_name, price)
        post_to_x(x_post_text)
        
        result = {
            "domain": domain,
            "date": datetime.now().isoformat(),
            "market": market,
            "competition": competition,
            "business_names": names,
            "sales_script": sales_script,
            "leads": leads,
            "product_name": product_name,
            "price": price,
            "site_file": site_filename,
            "x_post": x_post_text
        }
        
        self.memory["analyses"][domain.lower()] = result
        self.save_memory()
        
        send_telegram_message(f"✅ Analiza finalizata: {domain}\n\n📌 {competition[:100]}...\n🌐 Site generat\n🐦 Postat pe X")
        
        return result
    
    def run_daily_scan(self, domains_list):
        results = []
        for domain in domains_list:
            if domain.lower() in self.memory["analyses"]:
                existing = self.memory["analyses"][domain.lower()]
                existing_date = datetime.fromisoformat(existing["date"])
                days_old = (datetime.now() - existing_date).days
                if days_old < 7:
                    print(f"{domain} - analizat acum {days_old} zile (skip)")
                    continue
            result = self.full_analysis(domain)
            results.append(result)
        return results

def create_pdf_report(result, filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#2E6A8C'), spaceAfter=30)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#2E6A8C'), spaceAfter=12)
    normal_style = styles['Normal']
    
    story = []
    story.append(Paragraph(f"ANALIZA OPORTUNITATE", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Domeniu: {result['domain'].upper()}", normal_style))
    story.append(Paragraph(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Elimina diacriticele
    market_text = remove_diacritics(result['market']).replace('\n', '<br/>')
    competition_text = remove_diacritics(result['competition']).replace('\n', '<br/>')
    
    story.append(Paragraph("CERCETARE PIATA", heading_style))
    story.append(Paragraph(market_text, normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("OPORTUNITATE", heading_style))
    story.append(Paragraph(competition_text, normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(f"PRODUS: {remove_diacritics(result.get('product_name', 'N/A'))} - ${result.get('price', 'N/A')}", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("POSTARE X", heading_style))
    story.append(Paragraph(remove_diacritics(result.get('x_post', 'N/A')), normal_style))
    
    doc.build(story)
    print(f"PDF generat: {filename}")

def send_email_with_pdf(sender_email, sender_password, receiver_email, subject, body, pdf_filename):
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        with open(pdf_filename, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_filename)}")
            msg.attach(part)
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Eroare email: {e}")
        return False

if __name__ == "__main__":
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Eroare: GROQ_API_KEY nu este setata")
        exit(1)
    
    client = Groq(api_key=api_key)
    
    SENDER_EMAIL = "altoffler@gmail.com"
    SENDER_PASSWORD = "mgsdthjtwuttqvck"
    RECEIVER_EMAIL = "altoffler@gmail.com"
    
    send_telegram_message("🚀 Agentul cu postare pe X a pornit!")
    
    agent = BusinessAgent(api_key)
    
    domains_to_scan = [
        "cursuri online programare",
        "servicii marketing pentru mici afaceri"
    ]
    
    print("🚀 Pornim scanarea cu postare pe X...")
    
    results = agent.run_daily_scan(domains_to_scan)
    
    if results:
        for r in results:
            pdf_name = f"/data/analiza_{r['domain'].replace(' ', '_')}.pdf"
            create_pdf_report(r, pdf_name)
        
        send_email_with_pdf(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL,
                           f"Raport X - {datetime.now().strftime('%Y-%m-%d')}",
                           f"Au fost generate {len(results)} analize. Postari facute pe X.",
                           pdf_name)
        
        send_telegram_message(f"📊 Finalizat! {len(results)} analize cu postari pe X.")
    else:
        send_telegram_message("📭 Niciun domeniu nou de analizat.")
    
    print("✅ Finalizat!")