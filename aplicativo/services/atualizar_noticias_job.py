import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from django.db import transaction

from ..models import News

logger = logging.getLogger(__name__)

PT_MONTH_TO_NUM = {
    "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12,
}

UOL_MIN_DESC_LEN = 40
UOL_MAX_FALLBACK_FETCH_PER_RUN = 8

DEFAULT_IMPORTANT_WORDS = "A Nuvem de Palavras ainda não foi gerada."
DEFAULT_CLASSIFICATION = {
    "pilar": "Classificação ainda não foi gerada.",
    "objetivo_codigo": "",
    "objetivo_titulo": "-",
    "justificativa": "-",
}

_MOJ_RE = re.compile(r"(Ã.|Â.)")
_META_CHARSET_RE = re.compile(
    r'charset\s*=\s*["\']?\s*([a-zA-Z0-9_\-]+)\s*["\']?',
    re.IGNORECASE,
)
_XML_DECL_ENCODING_RE = re.compile(
    r'encoding\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)


@dataclass
class FeedItem:
    title: str
    link: str
    pub_date: date
    description_html: str = ""
    content_html: str = ""


def _score_text(s: str) -> int:
    return s.count("�") * 5 + len(_MOJ_RE.findall(s)) * 2


def _unique_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        if not x:
            continue
        k = str(x).strip()
        if not k:
            continue
        lk = k.lower()
        if lk in seen:
            continue
        seen.add(lk)
        out.append(k)
    return out


def decode_xml_bytes(raw: bytes, preferred: Optional[list[str]] = None, hint: Optional[str] = None) -> str:
    if not raw:
        return ""

    head = raw[:300].decode("ascii", errors="ignore")
    decl_enc = None
    m = _XML_DECL_ENCODING_RE.search(head)
    if m:
        decl_enc = m.group(1)

    candidates = []
    if decl_enc:
        candidates.append(decl_enc)
    if hint:
        candidates.append(hint)
    if preferred:
        candidates.extend(preferred)
    candidates.extend(["utf-8", "windows-1252", "iso-8859-1"])

    candidates = _unique_keep_order(candidates)

    best_s = None
    best_sc = 10**18

    for enc in candidates:
        try:
            s = raw.decode(enc, errors="replace")
        except Exception:
            continue

        sc = _score_text(s)

        if _MOJ_RE.search(s):
            try:
                fixed = s.encode("latin1", errors="strict").decode("utf-8", errors="strict")
                sc2 = _score_text(fixed)
                if sc2 < sc:
                    s, sc = fixed, sc2
            except Exception:
                pass

        if sc < best_sc:
            best_sc = sc
            best_s = s

            if best_sc == 0 and enc.lower() in ("utf-8", "iso-8859-1", "windows-1252"):
                pass

    return best_s if best_s is not None else raw.decode("utf-8", errors="replace")


def decode_html_bytes(raw: bytes, hint: Optional[str] = None) -> str:
    if not raw:
        return ""

    sniff = raw[:4096].decode("ascii", errors="ignore")
    meta_enc = None
    m = _META_CHARSET_RE.search(sniff)
    if m:
        meta_enc = m.group(1)

    candidates = []
    if meta_enc:
        candidates.append(meta_enc)
    if hint:
        candidates.append(hint)

    candidates.extend(["utf-8", "windows-1252", "iso-8859-1"])
    candidates = _unique_keep_order(candidates)

    best_s = None
    best_sc = 10**18

    for enc in candidates:
        try:
            s = raw.decode(enc, errors="replace")
        except Exception:
            continue

        sc = _score_text(s)

        if _MOJ_RE.search(s):
            try:
                fixed = s.encode("latin1", errors="strict").decode("utf-8", errors="strict")
                sc2 = _score_text(fixed)
                if sc2 < sc:
                    s, sc = fixed, sc2
            except Exception:
                pass

        if sc < best_sc:
            best_sc = sc
            best_s = s

    return best_s if best_s is not None else raw.decode("utf-8", errors="replace")


def extrair_texto_limpo(html_or_text: str) -> str:
    if not html_or_text:
        return ""

    s = str(html_or_text)

    if "<" not in s and ">" not in s:
        s = re.sub(r"\s+", " ", s).strip()
        return s

    soup = BeautifulSoup(s, "html.parser")
    for tag in soup(["script", "style", "noscript", "img", "svg", "figure", "source", "picture", "aside", "footer", "header"]):
        tag.decompose()

    texto = soup.get_text(separator="\n", strip=True)
    linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
    return "\n".join(linhas)


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if tag and "}" in tag else (tag or "")


def _child_text_by_localname(item: ET.Element, localname: str) -> str:
    for ch in list(item):
        if _strip_ns(ch.tag) == localname:
            return (ch.text or "").strip()
    return ""


def parse_data_uol(pub_date_raw: str) -> date:
    s = (pub_date_raw or "").strip()
    if not s:
        return date.today()

    try:
        s2 = s.split(",", 1)[1].strip() if "," in s else s
        partes = s2.split()
        dia = int(partes[0])
        mes_str = partes[1][:3].capitalize()
        ano = int(partes[2])
        mes = PT_MONTH_TO_NUM[mes_str]
        return date(ano, mes, dia)
    except Exception:
        pass

    try:
        return date_parser.parse(s).date()
    except Exception:
        return date.today()


def parse_data_generica(pub_date_raw: str) -> date:
    s = (pub_date_raw or "").strip()
    if not s:
        return date.today()
    try:
        return date_parser.parse(s).date()
    except Exception:
        return date.today()


def _first_meta_content(soup: BeautifulSoup, selectors: list[tuple[str, dict]]) -> str:
    for tag_name, attrs in selectors:
        tag = soup.find(tag_name, attrs=attrs)
        if tag and tag.get("content"):
            txt = tag.get("content", "").strip()
            if txt:
                return txt
    return ""


def _extract_jsonld_best(soup: BeautifulSoup) -> tuple[str, str]:
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for sc in scripts:
        raw = (sc.string or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        candidates = data if isinstance(data, list) else [data]
        for obj in candidates:
            if not isinstance(obj, dict):
                continue
            desc = (obj.get("description") or "").strip()
            body = (obj.get("articleBody") or "").strip()
            desc = re.sub(r"\s+", " ", desc).strip()
            body = re.sub(r"\s+", " ", body).strip()
            if desc or body:
                return desc, body
    return "", ""


def _extrair_conteudo_artigo(soup: BeautifulSoup) -> str:
    article = soup.find("article")
    container = article or soup.find("main") or soup.body or soup

    for tag in container.find_all(["script", "style", "noscript", "aside", "footer", "header", "svg", "img", "figure"]):
        tag.decompose()

    ps = container.find_all("p")
    chunks: list[str] = []
    for p in ps:
        txt = p.get_text(" ", strip=True)
        txt = re.sub(r"\s+", " ", txt).strip()
        if len(txt) >= 40:
            chunks.append(txt)

    if chunks:
        return "\n".join(chunks)

    return extrair_texto_limpo(str(container))


def enriquecer_uol_pela_pagina(session: requests.Session, url: str, headers: dict, timeout: int = 20) -> tuple[str, str]:
    if not url:
        return "", ""

    try:
        r = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code != 200:
            return "", ""

        html = decode_html_bytes(r.content, hint=getattr(r, "encoding", None))
        soup = BeautifulSoup(html, "html.parser")

        desc_ld, body_ld = _extract_jsonld_best(soup)
        desc_meta = _first_meta_content(
            soup,
            selectors=[
                ("meta", {"property": "og:description"}),
                ("meta", {"name": "twitter:description"}),
                ("meta", {"name": "description"}),
            ],
        )

        desc = desc_ld or desc_meta
        desc = re.sub(r"\s+", " ", (desc or "")).strip()

        content = body_ld or _extrair_conteudo_artigo(soup)

        if not desc and content:
            first_line = next((ln.strip() for ln in content.splitlines() if len(ln.strip()) >= 40), "")
            desc = first_line

        return desc, content

    except Exception as e:
        logger.warning("Falha ao enriquecer UOL via página (%s): %s", url, e)
        return "", ""


def extrair_itens_ebserh(root: ET.Element) -> list[FeedItem]:
    out: list[FeedItem] = []
    items = root.findall("{http://purl.org/rss/1.0/}item")
    for it in items:
        title = (it.findtext("{http://purl.org/rss/1.0/}title") or "").strip()
        link = (it.findtext("{http://purl.org/rss/1.0/}link") or "").strip()
        description_html = (it.findtext("{http://purl.org/rss/1.0/}description") or "").strip()
        pub_date_raw = (it.findtext("{http://purl.org/dc/elements/1.1/}date") or "").strip()
        content_html = (it.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "").strip()

        if not link:
            continue

        try:
            dt = datetime.strptime(pub_date_raw, "%Y-%m-%dT%H:%M:%SZ")
            pub_value = dt.date()
        except Exception:
            pub_value = date.today()

        out.append(FeedItem(title=title, link=link, pub_date=pub_value, description_html=description_html, content_html=content_html))
    return out


def extrair_itens_uol(root: ET.Element) -> list[FeedItem]:
    out: list[FeedItem] = []
    channel = root.find("channel")
    if channel is None:
        return out

    for it in channel.findall("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub_raw = (it.findtext("pubDate") or "").strip()
        desc_html = (it.findtext("description") or "").strip()
        content_html = _child_text_by_localname(it, "encoded")

        if not link:
            continue

        out.append(FeedItem(title=title, link=link, pub_date=parse_data_uol(pub_raw), description_html=desc_html, content_html=content_html))
    return out


def extrair_itens_g1(root: ET.Element) -> list[FeedItem]:
    out: list[FeedItem] = []
    channel = root.find("channel")
    if channel is None:
        return out

    for it in channel.findall("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub_raw = (it.findtext("pubDate") or "").strip()

        subtitle = ""
        for ch in list(it):
            if _strip_ns(ch.tag) == "subtitle":
                subtitle = (ch.text or "").strip()
                break

        description_html = (it.findtext("description") or "").strip()
        soup = BeautifulSoup(description_html, "html.parser")
        if soup.img:
            soup.img.decompose()
        content_text = soup.get_text(separator="\n", strip=True)

        if not link:
            continue

        out.append(FeedItem(title=title, link=link, pub_date=parse_data_generica(pub_raw), description_html=subtitle, content_html=content_text))
    return out


def _bulk_insert_news(source: str, items: list[FeedItem], session: Optional[requests.Session] = None, headers: Optional[dict] = None) -> int:
    if not items:
        return 0

    by_link: dict[str, FeedItem] = {}
    for it in items:
        if it.link:
            by_link[it.link] = it
    items = list(by_link.values())

    links = [it.link for it in items if it.link]
    existing = set(News.objects.filter(link__in=links).values_list("link", flat=True))
    new_items = [it for it in items if it.link not in existing]
    if not new_items:
        return 0

    if source == "UOL":
        for it in new_items:
            it.description_html = extrair_texto_limpo(it.description_html)
            it.content_html = extrair_texto_limpo(it.content_html)

        if session and headers:
            fallback_used = 0
            need_fallback = [it for it in new_items if (not it.description_html or len(it.description_html) < UOL_MIN_DESC_LEN)]
            for it in need_fallback:
                if fallback_used >= UOL_MAX_FALLBACK_FETCH_PER_RUN:
                    break
                fallback_used += 1
                desc_fb, content_fb = enriquecer_uol_pela_pagina(session, it.link, headers=headers, timeout=20)
                if desc_fb:
                    it.description_html = desc_fb
                if content_fb:
                    it.content_html = content_fb

        for it in new_items:
            if not it.description_html:
                it.description_html = it.title
            if not it.content_html:
                it.content_html = it.description_html
    else:
        for it in new_items:
            it.description_html = extrair_texto_limpo(it.description_html)
            it.content_html = extrair_texto_limpo(it.content_html)
            if not it.content_html:
                it.content_html = it.description_html

    objs: list[News] = []
    for it in new_items:
        objs.append(
            News(
                title=it.title,
                link=it.link,
                pub_date=it.pub_date,
                description=it.description_html or it.title,
                content=it.content_html or it.description_html or "",
                source=source,
                important_words=DEFAULT_IMPORTANT_WORDS,
                classification=dict(DEFAULT_CLASSIFICATION),
            )
        )

    with transaction.atomic():
        News.objects.bulk_create(objs, batch_size=200, ignore_conflicts=True)

    return len(objs)


def atualizar_noticias_job() -> int:
    fontes = {
        "G1": "https://g1.globo.com/rss/g1/",
        "UOL": "https://rss.uol.com.br/feed/noticias.xml",
        "EBSERH": "https://www.gov.br/ebserh/pt-br/site-feed/RSS",
    }

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    novas_total = 0

    with requests.Session() as session:
        for fonte, url in fontes.items():
            try:
                resp = session.get(url, headers=headers, timeout=20)
                if resp.status_code != 200:
                    logger.warning("RSS %s retornou status %s", fonte, resp.status_code)
                    continue

                if fonte == "UOL":
                    pass
                    #xml_text = decode_xml_bytes(
                    #    resp.content,
                    #    preferred=["iso-8859-1", "windows-1252", "utf-8"],
                    #    hint=getattr(resp, "encoding", None),
                    #)
                    #root = ET.fromstring(xml_text)
                    #items = extrair_itens_uol(root)
                    #novas_total += _bulk_insert_news("UOL", items, session=session, headers=headers)
                else:
                    xml_text = decode_xml_bytes(resp.content, hint=getattr(resp, "encoding", None))
                    root = ET.fromstring(xml_text)

                    if fonte == "EBSERH":
                        items = extrair_itens_ebserh(root)
                        novas_total += _bulk_insert_news("EBSERH", items)
                    elif fonte == "G1":
                        pass
                        #items = extrair_itens_g1(root)
                        #novas_total += _bulk_insert_news("G1", items)

            except ET.ParseError as e:
                logger.exception("Erro parseando XML de %s: %s", fonte, e)
            except Exception as e:
                logger.exception("Erro ao processar fonte %s: %s", fonte, e)

    return novas_total
