import xml.etree.ElementTree as ET
from datetime import datetime, date
import requests

from bs4 import BeautifulSoup
from dateutil import parser

from ..models import News


def extrair_texto_limpo(html):
    # Parse do HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Remove elementos de script, style, etc, se existirem
    for tag in soup(['script', 'style']):
        tag.decompose()

    # Extrai e limpa o texto
    texto = soup.get_text(separator='\n', strip=True)

    # Remove múltiplas quebras de linha (opcional)
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    texto_limpo = '\n'.join(linhas)

    return texto_limpo


PT_MONTH_TO_NUM = {
    "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12,
}

def parse_data_uol(pub_date_raw: str) -> date:
    s = pub_date_raw.strip()
    if "," in s:
        _, s = s.split(",", 1)
        s = s.strip()

    partes = s.split()
    dia = int(partes[0])
    mes_str = partes[1][:3].capitalize()
    ano = int(partes[2])
    mes = PT_MONTH_TO_NUM[mes_str]
    return date(ano, mes, dia)


def processar_ebserh(root) -> int:
    novas = 0
    items = root.findall("{http://purl.org/rss/1.0/}item")

    for item in items:
        title = item.find("{http://purl.org/rss/1.0/}title")
        link = item.find("{http://purl.org/rss/1.0/}link")
        description = item.find("{http://purl.org/rss/1.0/}description")
        pub_date = item.find("{http://purl.org/dc/elements/1.1/}date")
        content_encoded = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")

        title_text = title.text.strip() if title is not None else ""
        link_text = link.text.strip() if link is not None else ""
        description_text = description.text.strip() if description is not None else ""
        pub_date_text = pub_date.text.strip() if pub_date is not None else ""
        content_text = content_encoded.text.strip() if content_encoded is not None else ""

        if link_text and not News.objects.filter(link=link_text).exists():
            dt = datetime.strptime(pub_date_text, "%Y-%m-%dT%H:%M:%SZ")
            data_only = dt.date()

            News.objects.create(
                title=title_text,
                link=link_text,
                pub_date=data_only,
                description=extrair_texto_limpo(description_text),
                content=extrair_texto_limpo(content_text),
                source="EBSERH",
                important_words="A Nuvem de Palavras ainda não foi gerada.",
                classification={
                    "pilar": "Classificação ainda não foi gerada.",
                    "objetivo_codigo": "",
                    "objetivo_titulo": "-",
                    "justificativa": "-"
                }
            )
            novas += 1

    return novas


def processar_uol(root) -> int:
    novas = 0
    channel = root.find("channel")
    if channel is None:
        return 0

    for item in channel.findall("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_raw = item.findtext("pubDate", "").strip()
        description = item.findtext("description", title).strip()

        if link and not News.objects.filter(link=link).exists():
            data_only = parse_data_uol(pub_date_raw)

            News.objects.create(
                title=title,
                link=link,
                pub_date=data_only,
                description=extrair_texto_limpo(description),
                content="",
                source="UOL",
                important_words="A Nuvem de Palavras ainda não foi gerada.",
                classification={
                    "pilar": "Classificação ainda não foi gerada.",
                    "objetivo_codigo": "",
                    "objetivo_titulo": "-",
                    "justificativa": "-"
                },
            )
            novas += 1

    return novas


def processar_g1(root) -> int:
    novas = 0
    channel = root.find("channel")
    if channel is None:
        return 0

    for item in channel.findall("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_raw = item.findtext("pubDate", "").strip()

        atom_subtitle = item.find("{http://www.w3.org/2005/Atom}subtitle")
        description_text = atom_subtitle.text.strip() if atom_subtitle is not None and atom_subtitle.text else ""

        description_html = item.findtext("description", "").strip()
        soup = BeautifulSoup(description_html, "html.parser")
        if soup.img:
            soup.img.decompose()
        content_text = soup.get_text(separator="\n").strip()

        if link and not News.objects.filter(link=link).exists():
            # Se seu campo for DateField, use .date()
            pub_dt = parser.parse(pub_date_raw).replace(tzinfo=None)
            pub_value = pub_dt.date()  # << mantém consistente com DateField

            News.objects.create(
                title=title,
                link=link,
                pub_date=pub_value,
                description=description_text,
                content=content_text,
                source="G1",
                important_words="A Nuvem de Palavras ainda não foi gerada.",
                classification={
                    "pilar": "Classificação ainda não foi gerada.",
                    "objetivo_codigo": "",
                    "objetivo_titulo": "-",
                    "justificativa": "-"
                }
            )
            novas += 1

    return novas


def atualizar_noticias_job() -> int:
    fontes = {
        "G1": "https://g1.globo.com/rss/g1/",
        "UOL": "https://rss.uol.com.br/feed/noticias.xml",
        "EBSERH": "https://www.gov.br/ebserh/pt-br/site-feed/RSS",
    }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    novas = 0

    for fonte, url in fontes.items():
        try:
            # timeout evita o job travar
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                continue

            content = response.content
            if fonte == "UOL":
                content = content.decode("iso-8859-1")

            root = ET.fromstring(content)

            if fonte == "EBSERH":
                novas += processar_ebserh(root)
            elif fonte == "UOL":
                novas += processar_uol(root)
            elif fonte == "G1":
                novas += processar_g1(root)

        except Exception as e:
            # ideal: logger em vez de print
            print(f"Erro ao processar fonte {fonte}: {e}")
            continue

    return novas
