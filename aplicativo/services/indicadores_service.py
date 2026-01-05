import json
import os
import re
from openai import OpenAI
from django.shortcuts import get_object_or_404
from ..models import News, Dashboard

_OE_MAX = 25

def _objetivo_codigo_para_index(obj_codigo: str):
    if not obj_codigo:
        return None
    s = str(obj_codigo).strip().upper()
    m = re.search(r"(\d{1,2})", s)
    if not m:
        return None
    n = int(m.group(1))
    return n - 1 if 1 <= n <= _OE_MAX else None

def classificar_noticia(titulo: str, noticia: str) -> dict:
    system_prompt = """
    Você é um classificador de notícias da Rede Ebserh. Sua tarefa é ler uma notícia e escolher:
    1) exatamente 1 PILAR, dentre a lista abaixo;
    2) exatamente 1 OBJETIVO ESTRATÉGICO pertencente ao PILAR escolhido.

    REGRAS
    - Selecione o objetivo mais específico que reflita a ação central da notícia.
    - Em empate, prefira: maior especificidade > maior presença de termos do objetivo > impacto para o SUS/Ebserh.
    - Nunca escolha objetivo de um pilar diferente do pilar selecionado.
    - Saída OBRIGATÓRIA em JSON no formato definido abaixo, sem texto extra.
    - Se o texto estiver em outro idioma, traduza mentalmente e classifique normalmente.

    FORMATO DE SAÍDA (JSON)
    {
    "pilar": "<nome do pilar, exatamente como na lista>",
    "objetivo_codigo": "<ex.: OE04>",
    "objetivo_titulo": "<título curto do objetivo>",
    "justificativa": "<1 ou 2 frases objetivas indicando os trechos/termos que motivaram a escolha>",
    }

    TAXONOMIA
    - Sociedade (usuário SUS):
    - OE01: Ampliar e qualificar a participação dos hospitais na rede de atenção à saúde do SUS
    - OE02: Qualificar o cuidado hospitalar
    - OE03: Ampliar e qualificar a participação na rede nacional de cuidados oncológicos
    - OE04: Participar da implementação da Política Nacional de Atenção Especializada e do esforço de redução de filas
    - OE25: Educação e informação em saúde para a população
    - Sociedade (estudante):
    - OE05: Aprimorar as condições de ensino e os cenários de prática
    - OE06: Consolidar o Exame Nacional de Residência (Enare) como forma prioritária de ingresso
    - OE07: Apoiar a qualificação de docentes e preceptores
    - OE08: Qualificar o dimensionamento e a oferta de vagas de residência
    - Sociedade (pesquisador):
    - OE09: Criar ambiente favorável à gestão e à pesquisa em saúde
    - OE10: Contribuir com a estratégia de saúde digital (ex.: AGHU, telessaúde)
    - Responsabilidade Ambiental, Social e Governança:
    - OE11: Aprimorar a governança corporativa da Rede
    - OE12: Promover sustentabilidade ambiental e responsabilidade social
    - OE13: Prevenir e enfrentar assédio e discriminação
    - OE14: Melhorias em infraestrutura e condições de trabalho
    - Desenvolvimento Institucional:
    - OE15: Atuação integrada dos hospitais em Rede
    - OE16: Fortalecer o reconhecimento e a imagem pública da Ebserh
    - OE17: Desenvolver capacidade institucional em gestão hospitalar
    - OE18: Promover inovação e transformação digital na Rede
    - Sustentabilidade Financeira:
    - OE19: Promover eficiência nos processos de gestão do trabalho
    - OE20: Ampliar e diversificar as fontes de financiamento
    - OE21: Aprimorar processos de compras e contratações
    - Desenvolvimento do Trabalhador:
    - OE22: Promover escuta e diálogo permanentes com trabalhadores
    - OE23: Promover engajamento e valorização dos trabalhadores
    - OE24: Desenvolver estratégias de educação permanente e continuada
    """

    user_prompt = f"""Classifique a notícia a seguir conforme o sistema e a taxonomia fornecidos.

TÍTULO: {titulo}
TEXTO COMPLETO: {noticia}

Retorne apenas o JSON solicitado.
"""

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return json.loads(resp.choices[0].message.content)

def gerar_indicadores_por_noticia_id(nid: int) -> bool:
    noticia = get_object_or_404(News, id=nid)

    cls = noticia.classification or {}
    if cls and cls.get("pilar") and cls.get("pilar") != "Classificação ainda não foi gerada.":
        return False

    classificacao = classificar_noticia(noticia.title or "", noticia.content or "")
    noticia.classification = classificacao
    noticia.save(update_fields=["classification"])
    return True

def atualizar_dashboard_por_id(dashboard_id: int, progress_cb=None) -> dict:
    dashboard = get_object_or_404(Dashboard, id=dashboard_id)

    initial = dashboard.initial_date
    final = dashboard.final_date
    sources = dashboard.sources or []

    news_filter = {"pub_date__range": (initial, final)}
    if sources:
        news_filter["source__in"] = sources

    news_ids = News.objects.filter(**news_filter).values_list("id", flat=True)
    total = news_ids.count()

    done = 0
    for nid in news_ids.iterator():
        gerar_indicadores_por_noticia_id(int(nid))
        done += 1

        if progress_cb and (done == 1 or done % 5 == 0 or done == total):
            progress_cb(done, total)

    counts = [0] * _OE_MAX
    oe_news_map: dict[str, list[dict]] = {}

    qs = News.objects.filter(**news_filter, classification__isnull=False).only(
        "id", "title", "source", "classification"
    )

    for n in qs.iterator():
        cls = n.classification or {}
        idx = _objetivo_codigo_para_index(cls.get("objetivo_codigo"))
        if idx is None:
            continue

        counts[idx] += 1
        oe_key = f"OE{idx + 1:02d}"
        oe_news_map.setdefault(oe_key, []).append({
            "id": n.id,
            "title": n.title,
            "source": n.source,
        })

    dashboard.oe_count = counts
    dashboard.oe_news_map = oe_news_map
    dashboard.save(update_fields=["oe_count", "oe_news_map"])

    return {"ok": True, "dashboard_id": dashboard_id, "total": total}
