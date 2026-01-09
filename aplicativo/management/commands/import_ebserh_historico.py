# <seu_app>/management/commands/import_ebserh_historico.py

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import News  # ajuste se necessário (ex: from app.models import News)

logger = logging.getLogger(__name__)

BASE_LIST_URL = "https://www.gov.br/ebserh/pt-br/comunicacao/noticias"

DEFAULT_IMPORTANT_WORDS = "A Nuvem de Palavras ainda não foi gerada."
DEFAULT_CLASSIFICATION = {
    "pilar": "Classificação ainda não foi gerada.",
    "objetivo_codigo": "",
    "objetivo_titulo": "-",
    "justificativa": "-",
}

# No listing costuma aparecer: "08/01/2026 - resumo..."
DATE_RE_LIST = re.compile(r"(\d{2}/\d{2}/\d{4})\s*-\s*(.+)")
# Na página da notícia costuma aparecer: "Publicado em 08/01/2026 ..."
DATE_RE_DETAIL = re.compile(r"Publicado em\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
META_CHARSET_RE = re.compile(r'charset\s*=\s*["\']?\s*([a-zA-Z0-9_\-]+)\s*["\']?', re.IGNORECASE)


@dataclass
class EbserhListItem:
    title: str
    link: str
    pub_date: Optional[date] = None
    summary: str = ""


def decode_html_bytes(raw: bytes, hint: Optional[str] = None) -> str:
    if not raw:
        return ""
    sniff = raw[:4096].decode("ascii", errors="ignore")
    meta_enc = None
    m = META_CHARSET_RE.search(sniff)
    if m:
        meta_enc = m.group(1)

    candidates = []
    if meta_enc:
        candidates.append(meta_enc)
    if hint:
        candidates.append(hint)
    candidates.extend(["utf-8", "windows-1252", "iso-8859-1"])

    best = None
    best_bad = 10**18

    for enc in candidates:
        try:
            s = raw.decode(enc, errors="replace")
        except Exception:
            continue
        bad = s.count("�")
        if bad < best_bad:
            best_bad = bad
            best = s

    return best if best is not None else raw.decode("utf-8", errors="replace")


def extrair_texto_limpo(html_or_text: str) -> str:
    if not html_or_text:
        return ""
    s = str(html_or_text)

    if "<" not in s and ">" not in s:
        return re.sub(r"\s+", " ", s).strip()

    soup = BeautifulSoup(s, "html.parser")
    for tag in soup(["script", "style", "noscript", "img", "svg", "figure", "source", "picture", "aside", "footer", "header"]):
        tag.decompose()

    texto = soup.get_text(separator="\n", strip=True)
    linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
    return "\n".join(linhas)


def _first_meta_content(soup: BeautifulSoup, selectors: list[tuple[str, dict]]) -> str:
    for tag_name, attrs in selectors:
        tag = soup.find(tag_name, attrs=attrs)
        if tag and tag.get("content"):
            txt = (tag.get("content") or "").strip()
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


def _extract_article_text(soup: BeautifulSoup) -> str:
    # gov.br/Plone costuma ter o corpo do texto nessas regiões
    container = (
        soup.select_one("#parent-fieldname-text")
        or soup.select_one("#content-core")
        or soup.select_one("main")
        or soup.body
        or soup
    )

    for tag in container.find_all(["script", "style", "noscript", "aside", "footer", "header", "svg", "img", "figure"]):
        tag.decompose()

    ps = container.find_all("p")
    chunks: list[str] = []
    for p in ps:
        txt = p.get_text(" ", strip=True)
        txt = re.sub(r"\s+", " ", txt).strip()
        if len(txt) >= 30:
            chunks.append(txt)

    if chunks:
        return "\n".join(chunks)

    return extrair_texto_limpo(str(container))


def parse_br_date(ddmmyyyy: str) -> Optional[date]:
    try:
        return datetime.strptime(ddmmyyyy, "%d/%m/%Y").date()
    except Exception:
        return None


def parse_input_date(s: str) -> Optional[date]:
    """
    Aceita:
      - YYYY-MM-DD
      - DD/MM/YYYY
    """
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        pass
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except Exception:
        return None


# ==========================
# ALTERAÇÃO AQUI (FETCH/PAGINAÇÃO + RETRY)
# ==========================

def _get_with_retry(
    session: requests.Session,
    url: str,
    headers: dict,
    connect_timeout: int,
    read_timeout: int,
    retries: int,
    backoff: float,
) -> requests.Response:
    """
    Faz GET com retry/backoff para timeouts e falhas transitórias.
    """
    last_exc: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            resp = session.get(
                url,
                headers=headers,
                timeout=(connect_timeout, read_timeout),
                allow_redirects=True,
            )
            resp.raise_for_status()
            return resp
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
            last_exc = e
        except requests.exceptions.HTTPError as e:
            # retry somente para erros típicos transitórios
            status = getattr(e.response, "status_code", None)
            if status in (429, 500, 502, 503, 504):
                last_exc = e
            else:
                raise
        except Exception as e:
            last_exc = e

        if attempt < retries:
            sleep_s = backoff * (2 ** attempt)
            time.sleep(sleep_s)

    raise last_exc if last_exc else RuntimeError("Falha desconhecida no _get_with_retry")


def fetch_list_page(
    session: requests.Session,
    start: int,
    headers: dict,
    connect_timeout: int,
    read_timeout: int,
    retries: int,
    backoff: float,
) -> str:
    """
    Paginação DO JEITO QUE VOCÊ PEDIU: b_start:int=0,30,60...

    Importante: montamos a URL literalmente (sem params) para evitar
    qualquer comportamento estranho com o ":" no nome do parâmetro.
    """
    url = f"{BASE_LIST_URL}?b_start:int={start}"
    r = _get_with_retry(
        session=session,
        url=url,
        headers=headers,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        retries=retries,
        backoff=backoff,
    )
    return decode_html_bytes(r.content, hint=getattr(r, "encoding", None))


def extract_list_items(html: str) -> list[EbserhListItem]:
    soup = BeautifulSoup(html, "html.parser")

    container = soup.select_one("main") or soup.select_one("#content") or soup

    items: list[EbserhListItem] = []

    # Estratégia 1: links de títulos em h2 (comum em listing do Plone)
    anchors = list(container.select("h2 a[href]"))

    # Fallback: qualquer <a> dentro de resultados, se h2 não vier
    if not anchors:
        anchors = list(container.select("article a[href], .tileItem a[href], .listingBar a[href]"))

    for a in anchors:
        title = (a.get_text(strip=True) or "").strip()
        href = (a.get("href") or "").strip()
        if not title or not href:
            continue

        link = urljoin(BASE_LIST_URL + "/", href)

        # mantém somente URLs de notícias do caminho esperado
        if "/ebserh/pt-br/comunicacao/noticias/" not in link:
            continue
        # descarta links de paginação/listagem
        if "b_start:int=" in link or "b_start%3Aint" in link:
            continue

        # tenta capturar o bloco que contém "DD/MM/AAAA - resumo"
        block = a.find_parent(["article", "div", "li", "section"]) or a.parent
        text_block = block.get_text("\n", strip=True) if block else ""
        text_block = re.sub(r"[ \t]+", " ", text_block).strip()

        pub = None
        summary = ""

        m = DATE_RE_LIST.search(text_block)
        if m:
            pub = parse_br_date(m.group(1))
            summary = (m.group(2) or "").strip()

        items.append(EbserhListItem(title=title, link=link, pub_date=pub, summary=summary))

    # dedupe por link preservando ordem
    seen = set()
    out = []
    for it in items:
        if it.link in seen:
            continue
        seen.add(it.link)
        out.append(it)
    return out


def fetch_detail(
    session: requests.Session,
    url: str,
    headers: dict,
    connect_timeout: int,
    read_timeout: int,
    retries: int,
    backoff: float,
) -> dict:
    """
    Igual ao seu fetch_detail, mas com retry/backoff e timeout (connect, read).
    """
    r = _get_with_retry(
        session=session,
        url=url,
        headers=headers,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        retries=retries,
        backoff=backoff,
    )

    html = decode_html_bytes(r.content, hint=getattr(r, "encoding", None))
    soup = BeautifulSoup(html, "html.parser")

    # título
    h1 = soup.find(["h1"])
    title = (h1.get_text(" ", strip=True) if h1 else "").strip()

    # data (Publicado em DD/MM/AAAA ...)
    pub_date = None
    full_text = soup.get_text("\n", strip=True)
    m = DATE_RE_DETAIL.search(full_text)
    if m:
        pub_date = parse_br_date(m.group(1))

    # descrição (preferências: JSON-LD -> documentDescription -> meta)
    desc_ld, body_ld = _extract_jsonld_best(soup)

    desc_dom = ""
    dd = soup.select_one(".documentDescription")
    if dd:
        desc_dom = dd.get_text(" ", strip=True)

    desc_meta = _first_meta_content(
        soup,
        selectors=[
            ("meta", {"property": "og:description"}),
            ("meta", {"name": "twitter:description"}),
            ("meta", {"name": "description"}),
        ],
    )

    description = (desc_ld or desc_dom or desc_meta or "").strip()
    description = re.sub(r"\s+", " ", description).strip()

    # conteúdo
    content = (body_ld or _extract_article_text(soup) or "").strip()
    content = extrair_texto_limpo(content)

    # se ainda não tem description, usa primeira linha do conteúdo
    if not description and content:
        for ln in content.splitlines():
            ln = ln.strip()
            if len(ln) >= 40:
                description = ln
                break

    return {
        "title": title,
        "pub_date": pub_date,
        "description": description,
        "content": content,
    }


class Command(BaseCommand):
    help = "Importa notícias históricas da EBSERH (scraping do listing /comunicacao/noticias)."

    def add_arguments(self, parser):
        parser.add_argument("--per-page", type=int, default=30, help="Itens por página (padrão 30).")
        parser.add_argument("--max-pages", type=int, default=9999, help="Máximo de páginas para varrer.")
        parser.add_argument("--sleep", type=float, default=0.2, help="Delay (segundos) entre requisições.")
        parser.add_argument("--timeout", type=int, default=20, help="(compat) Read timeout padrão (segundos).")

        # NOVOS (rede) — mantendo compatibilidade
        parser.add_argument("--connect-timeout", type=int, default=10, help="Connect timeout (segundos).")
        parser.add_argument("--list-timeout", type=int, default=0, help="Read timeout da LISTAGEM (0 = usa --timeout).")
        parser.add_argument("--detail-timeout", type=int, default=0, help="Read timeout do DETALHE (0 = usa --timeout).")
        parser.add_argument("--retries", type=int, default=3, help="Número de retries para requests.")
        parser.add_argument("--backoff", type=float, default=1.0, help="Backoff base (segundos). Exponencial: 1,2,4,...")

        parser.add_argument(
            "--no-detail",
            action="store_true",
            help="Não acessa a página individual da notícia (usa só data/resumo do listing).",
        )

        parser.add_argument(
            "--date-from",
            type=str,
            default="",
            help="Data inicial (inclusive). Aceita YYYY-MM-DD ou DD/MM/YYYY.",
        )
        parser.add_argument(
            "--date-to",
            type=str,
            default="",
            help="Data final (inclusive). Aceita YYYY-MM-DD ou DD/MM/YYYY. Padrão: hoje.",
        )

        # compatibilidade (opcional)
        parser.add_argument(
            "--stop-before",
            type=str,
            default="",
            help="(DEPRECATED) Alias de --date-from. Para quando encontrar data < valor.",
        )

        parser.add_argument(
            "--max-items",
            type=int,
            default=0,
            help="Para após inserir N notícias (0 = sem limite).",
        )

    def handle(self, *args, **opts):
        per_page = int(opts["per_page"])
        max_pages = int(opts["max_pages"])
        sleep_s = float(opts["sleep"])
        timeout = int(opts["timeout"])
        no_detail = bool(opts["no_detail"])
        max_items = int(opts["max_items"]) if int(opts["max_items"]) > 0 else None

        connect_timeout = int(opts["connect_timeout"])
        list_timeout = int(opts["list_timeout"]) or timeout
        detail_timeout = int(opts["detail_timeout"]) or timeout
        retries = int(opts["retries"])
        backoff = float(opts["backoff"])

        # Intervalo de datas (inclusive)
        date_from = parse_input_date(opts.get("date_from", ""))

        # compatibilidade: stop_before como alias de date-from
        if not date_from and opts.get("stop_before"):
            date_from = parse_input_date(opts["stop_before"])

        date_to = parse_input_date(opts.get("date_to", "")) or date.today()

        if date_from and date_from > date_to:
            raise SystemExit("--date-from não pode ser maior que --date-to.")

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Importer/1.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
        }

        inserted_total = 0
        page = 0
        start = 0

        self.stdout.write(self.style.NOTICE(f"[EBSERH] Intervalo: {date_from or 'sem início'} .. {date_to} (inclusive)"))
        self.stdout.write(self.style.NOTICE(f"[EBSERH] Modo no-detail={no_detail} | per-page={per_page}"))
        self.stdout.write(self.style.NOTICE(
            f"[EBSERH] Rede: connect={connect_timeout}s list_read={list_timeout}s detail_read={detail_timeout}s "
            f"retries={retries} backoff={backoff}"
        ))

        with requests.Session() as session:
            while page < max_pages:
                # página lógica = start/per_page + 1
                page = (start // per_page) + 1
                self.stdout.write(self.style.NOTICE(f"[EBSERH] Página {page} (start={start})..."))

                try:
                    html = fetch_list_page(
                        session,
                        start=start,
                        headers=headers,
                        connect_timeout=connect_timeout,
                        read_timeout=list_timeout,
                        retries=retries,
                        backoff=backoff,
                    )
                except Exception as e:
                    logger.exception("Falha ao baixar listagem (start=%s): %s", start, e)
                    # não derruba o job na primeira falha: tenta seguir para a próxima página
                    start += per_page
                    if sleep_s > 0:
                        time.sleep(sleep_s)
                    continue

                items = extract_list_items(html)
                if not items:
                    self.stdout.write(self.style.WARNING("[EBSERH] Nenhum item encontrado; encerrando."))
                    break

                links = [it.link for it in items]
                existing = set(News.objects.filter(link__in=links).values_list("link", flat=True))

                to_create: list[News] = []
                stop_all = False

                for it in items:
                    if it.link in existing:
                        continue

                    # Se o listing já trouxe a data e ela já é menor que o limite inferior,
                    # podemos parar a varredura (assumindo ordem decrescente no listing).
                    if date_from and it.pub_date and it.pub_date < date_from:
                        stop_all = True
                        break

                    title = it.title
                    pub_date_value = it.pub_date
                    description = it.summary or it.title
                    content = it.summary or it.title

                    # Se precisamos aplicar intervalo e não temos pub_date do listing,
                    # buscamos o detalhe só para obter a data (mesmo no --no-detail).
                    must_fetch_detail_for_date = (pub_date_value is None) and (date_from is not None or date_to is not None)

                    if (not no_detail) or must_fetch_detail_for_date:
                        try:
                            detail = fetch_detail(
                                session,
                                it.link,
                                headers=headers,
                                connect_timeout=connect_timeout,
                                read_timeout=detail_timeout,
                                retries=retries,
                                backoff=backoff,
                            )
                            if detail.get("title"):
                                title = detail["title"]
                            if detail.get("pub_date"):
                                pub_date_value = detail["pub_date"]

                            if not no_detail:
                                if detail.get("description"):
                                    description = detail["description"]
                                if detail.get("content"):
                                    content = detail["content"]
                        except Exception as e:
                            # detalhe falhou => usa summary do listing e segue
                            logger.warning("Falha ao baixar detalhe (%s): %s", it.link, e)

                    # sem data => não dá pra filtrar por intervalo com segurança
                    if pub_date_value is None:
                        continue

                    # Filtro por intervalo (inclusive)
                    if date_from and pub_date_value < date_from:
                        stop_all = True
                        break

                    if date_to and pub_date_value > date_to:
                        # item mais novo que o teto: ignora e segue
                        continue

                    description = extrair_texto_limpo(description) or title
                    content = extrair_texto_limpo(content) or description

                    to_create.append(
                        News(
                            title=title[:500],
                            link=it.link,
                            pub_date=pub_date_value,
                            description=description,
                            content=content,
                            source="EBSERH",
                            important_words=DEFAULT_IMPORTANT_WORDS,
                            classification=dict(DEFAULT_CLASSIFICATION),
                        )
                    )

                    if max_items and (inserted_total + len(to_create)) >= max_items:
                        stop_all = True
                        break

                    if sleep_s > 0:
                        time.sleep(sleep_s)

                if to_create:
                    with transaction.atomic():
                        News.objects.bulk_create(to_create, batch_size=200, ignore_conflicts=True)
                    inserted_total += len(to_create)
                    self.stdout.write(self.style.SUCCESS(f"[EBSERH] Inseridas: {len(to_create)} (total={inserted_total})"))
                else:
                    self.stdout.write(self.style.NOTICE("[EBSERH] Nada novo nessa página (ou fora do intervalo)."))

                if max_items and inserted_total >= max_items:
                    self.stdout.write(self.style.NOTICE("[EBSERH] max-items atingido. Encerrando."))
                    break

                if stop_all:
                    self.stdout.write(self.style.NOTICE("[EBSERH] Intervalo inferior atingido; encerrando varredura."))
                    break

                # paginação: 0, 30, 60, 90, ...
                start += per_page

        self.stdout.write(self.style.SUCCESS(f"[EBSERH] Finalizado. Total inserido: {inserted_total}"))
