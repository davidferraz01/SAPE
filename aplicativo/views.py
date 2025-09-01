from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import *
from rolepermissions.decorators import has_permission_decorator
import json
from auth_app.models import Usuario
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from django.views.decorators.http import require_POST
from dateutil import parser
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from openai import OpenAI
from django.conf import settings

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import string

@csrf_exempt
def home(request):
    return render(request, 'home.html')


### Nuvem de Palavras ###
def baixar_stopwords():
    try:
        _ = stopwords.words('portuguese')
    except LookupError:
        nltk.download('stopwords')

def extrair_palavras_importantes(texto, top_n=10):
    # Define stopwords e pontuação
    baixar_stopwords()
    stop_words = set(stopwords.words('portuguese'))
    pontuacao = set(string.punctuation)

    # Divide o texto em "documentos" (frases ou parágrafos)
    documentos = [frase.strip() for frase in texto.split('\n') if frase.strip()]

    # Função para pré-processar os textos
    def preprocess(texto):
        palavras = texto.lower().split()
        return ' '.join([p.strip(''.join(pontuacao)) for p in palavras if p not in stop_words and p not in pontuacao])

    documentos_limpos = [preprocess(doc) for doc in documentos]

    # Aplica TF-IDF
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(documentos_limpos)

    # Soma dos pesos TF-IDF por palavra
    scores = X.sum(axis=0).A1
    termos = vectorizer.get_feature_names_out()
    termos_com_peso = list(zip(termos, scores))

    # Ordena por peso (importância)
    termos_ordenados = sorted(termos_com_peso, key=lambda x: x[1], reverse=True)

    # Retorna os top N termos mais relevantes
    return termos_ordenados[:top_n]


@csrf_exempt
@login_required
@require_POST
def atualizar_important_words(request, id):
    noticia = get_object_or_404(News, id=id)
    
    texto_para_analisar = noticia.content
    palavras = extrair_palavras_importantes(texto_para_analisar)
    
    noticia.important_words = ", ".join([p[0] for p in palavras])

    noticia.save()
    
    messages.success(request, "Nuvem de Palavras geradas com sucesso.")
    return JsonResponse({"status": "ok"})



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

@csrf_exempt
@login_required
@require_POST
def atualizar_noticias(request):
    fontes = {
        "G1": "https://g1.globo.com/rss/g1/",
        "UOL": "https://rss.uol.com.br/feed/noticias.xml",
        "EBSERH": "https://www.gov.br/ebserh/pt-br/site-feed/RSS",
    }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    novas = 0

    for fonte, url in fontes.items():
        try:
            response = requests.get(url, headers=headers)
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
            print(f"Erro ao processar fonte {fonte}: {e}")
            continue

    return JsonResponse({"status": "ok", "novas": novas})


def processar_ebserh(root):
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

        if not News.objects.filter(link=link_text).exists():
            News.objects.create(
                title=title_text,
                link=link_text,
                pub_date=datetime.strptime(pub_date_text, "%Y-%m-%dT%H:%M:%SZ"),
                description=extrair_texto_limpo(description_text),
                content=extrair_texto_limpo(content_text),
                source="EBSERH",
                important_words="A Nuvem de Palavras ainda não foi gerada.",
                classification="A Classificação ainda não foi gerada."
            )
            novas += 1

    return novas


def processar_uol(root):
    novas = 0
    items = root.find("channel").findall("item")

    for item in items:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_raw = item.findtext("pubDate", "").strip()
        description = item.findtext("description", title).strip()

        if not News.objects.filter(link=link).exists():
            pub_date = parser.parse(pub_date_raw).replace(tzinfo=None)

            News.objects.create(
                title=title,
                link=link,
                pub_date=pub_date,
                description=extrair_texto_limpo(description),
                content="",
                source="UOL",
                important_words="A Nuvem de Palavras ainda não foi gerada.",
                classification="A Classificação ainda não foi gerada."
            )
            novas += 1

    return novas


def processar_g1(root):
    novas = 0
    items = root.find("channel").findall("item")

    for item in items:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date_raw = item.findtext("pubDate", "").strip()

        # Pega atom:subtitle para description (se existir)
        atom_subtitle = item.find("{http://www.w3.org/2005/Atom}subtitle")
        description_text = atom_subtitle.text.strip() if atom_subtitle is not None else ""

        # Pega description HTML para content (removendo img e limpando)
        description_html = item.findtext("description", "").strip()
        soup = BeautifulSoup(description_html, "html.parser")
        if soup.img:
            soup.img.decompose()  # Remove tag <img>
        content_text = soup.get_text(separator="\n").strip()

        if not News.objects.filter(link=link).exists():
            pub_date = parser.parse(pub_date_raw).replace(tzinfo=None)

            News.objects.create(
                title=title,
                link=link,
                pub_date=pub_date,
                description=description_text,
                content=content_text,
                source="G1",
                important_words="A Nuvem de Palavras ainda não foi gerada.",
                classification="A Classificação ainda não foi gerada."
            )
            novas += 1

    return novas
######

### Gerar Indicadores ###
@csrf_exempt
@login_required
@require_POST
def gerar_indicadores(request, id):
    noticia = get_object_or_404(News, id=id)
    
    texto_para_analisar = noticia.content
    titulo = noticia.title

    classificacao = classificar_noticia(titulo,texto_para_analisar)
    
    noticia.classification = classificacao

    noticia.save()
    
    messages.success(request, "Indicadores gerados com sucesso.")
    return JsonResponse({"status": "ok"})

def classificar_noticia(titulo, noticia):
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
    "confianca": <número entre 0 e 1>
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

    TÍTULO: {[titulo]}
    TEXTO COMPLETO: {[noticia]}

    Retorne apenas o JSON solicitado.
    """

    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    )
    print(resp.choices[0].message.content)
    return resp.choices[0].message.content
######

# Doacao
@login_required
def doar(request):
    if request.method == 'GET':
        noticias = News.objects.order_by('-id')  # Ordenando pela mais recente

        context = {'noticias': noticias}

        return render(request, 'pages/doacao/avaliacao_noticias.html', context)
    

@login_required
def minhas_doacoes(request):
    if request.method == 'GET':
        # Filtrando as doacoes pelo usuario logado
        #doacao = Dashboard.objects.filter(fk_usuario=request.user).order_by('-id')

        #context = {'doacao': doacao}

        return render(request, 'pages/doacao/minhas_doacoes.html') #, context)

@login_required
def visualizar_campanha_doar(request, id):
    noticia = get_object_or_404(News, pk=id)

    context = {
        'noticia': noticia
    }

    return render(request, 'pages/doacao/visualizar_noticia.html', context)
    

@login_required
def cadastrar_doacao(request, id):
    campanha = Campanha.objects.get(pk=id)

    context = {'campanha': campanha}

    return render(request, 'pages/doacao/cadastrar_doacao.html', context)


@login_required  
def cadastrar_doacao_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Converte JSON para dicionário Python
            
            campanha_id = data.get('campanha_id')
            campanha = Campanha.objects.get(id=campanha_id)  # Obtém a campanha correspondente

            # Cria a doação
            doacao = Doacao.objects.create(
                fk_usuario=request.user,
                fk_campanha=campanha,
                valor=data.get('valor', 0),
                alimentos_qtd=data.get('qtd_alimentos', 0),
                alimentos_desc=data.get('alimentos', ''),
                vestimentas_qtd=data.get('qtd_vestimentas', 0),
                vestimentas_desc=data.get('vestimentas', ''),
                moveis_qtd=data.get('qtd_moveis', 0),
                moveis_desc=data.get('moveis', ''),
                brinquedos_qtd=data.get('qtd_brinquedos', 0),
                brinquedos_desc=data.get('brinquedos', ''),
                livros_qtd=data.get('qtd_livros', 0),
                livros_desc=data.get('livros', ''),
                higiene_qtd=data.get('qtd_artigos_higiene', 0),
                higiene_desc=data.get('artigos_higiene', ''),
                cobertores_qtd=data.get('qtd_cobertores', 0),
                cobertores_desc=data.get('cobertores', ''),
                eletronicos_qtd=data.get('qtd_eletronicos', 0),
                eletronicos_desc=data.get('eletronicos', ''),
                escola_qtd=data.get('qtd_artigos_escolares', 0),
                escola_desc=data.get('artigos_escolares', ''),
                hospitalares_qtd=data.get('qtd_artigos_hospitalares', 0),
                hospitalares_desc=data.get('artigos_hospitalares', ''),
                outros_qtd=data.get('qtd_outros', 0),
                outros_desc=data.get('outros', ''),
                mensagem=data.get('mensagem', '')
            )

            return JsonResponse({'success': True, 'message': 'Doação cadastrada com sucesso!'})

        except Campanha.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Campanha não encontrada.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Erro ao processar os dados. Envie um JSON válido.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)



# Campanha
@login_required
@has_permission_decorator('instituicao')
def minhas_campanhas(request):
    if request.method == 'GET':
        # Filtrando as noticias pelo usuário logado
        noticias = News.objects.filter(fk_usuario=request.user).order_by('-id')

        context = {'noticias': noticias}

        return render(request, 'pages/campanha/minhas_campanhas.html', context)


@login_required
@has_permission_decorator('instituicao')
def cadastrar_campanha(request):
    return render(request, 'pages/campanha/cadastrar_campanha.html')


@login_required
@has_permission_decorator('instituicao')
def cadastrar_campanha_request(request):
    if request.method == 'POST':
        try:
            # Obtendo os dados do formulário
            data = request.POST
            imagem = request.FILES.get('imagem', None)  # Obtendo a imagem (se enviada)

            # Criando o endereço
            endereco = Endereco.objects.create(
                cep=data.get('cep', ''),
                estado=data.get('estado', ''),
                cidade=data.get('cidade', ''),
                bairro=data.get('bairro', ''),
                logradouro=data.get('logradouro', ''),
                numero=data.get('numero', ''),
                complemento=data.get('complemento', '')
            )

            # Criando os contatos
            contato = Contato.objects.create(
                telefone=data.get('telefone', ''),
                email=data.get('email', ''),
                instagram=data.get('instagram', ''),
                facebook=data.get('facebook', ''),
                twitter=data.get('twitter', ''),
                chave_pix=data.get('chave_pix', '')
            )

            # Obtendo o usuário logado (Isso pode variar dependendo da autenticação)
            usuario = Usuario.objects.get(pk=request.user.id)

            # Criando a campanha
            campanha = Campanha.objects.create(
                titulo=data.get('titulo', ''),
                descricao=data.get('descricao', ''),
                endereco=endereco,
                contato=contato,
                imagem=imagem,
                meta_de_arrecadacao=data.get('meta_de_arrecadacao', 0.00),
                valor_arrecadado=data.get('valor_arrecadado', 0.00),
                inicio_campanha=data.get('inicio_campanha'),
                fim_campanha=data.get('fim_campanha'),
                fk_usuario=usuario
            )

            return JsonResponse({'status': 201, 'message': 'Campanha cadastrada com sucesso!'})

        except Exception as e:
            return JsonResponse({'status': 500, 'message': f'Erro ao cadastrar campanha: {str(e)}'})

    return JsonResponse({'status': 405, 'message': 'Método não permitido'}, status=405)



@csrf_exempt
@has_permission_decorator('instituicao')
def remover_campanha(request, id):
    if request.method == 'DELETE':
        campanha = get_object_or_404(Campanha, id=id, fk_usuario=request.user)
        campanha.delete()
        return JsonResponse({"success": True, "message": "Campanha removida com sucesso!"})
    
    return JsonResponse({"success": False, "message": "Método não permitido."}, status=405)



@login_required
@has_permission_decorator('instituicao')
def visualizar_campanha(request, id):
    campanha = get_object_or_404(Campanha, pk=id)
    doacao = Doacao.objects.filter(fk_campanha=campanha.id).order_by('-id')

    context = {'campanha': campanha, 'doacao': doacao}

    return render(request, 'pages/campanha/visualizar_campanha.html', context)




#  Usuario

@csrf_exempt
def solicitacao_de_acesso(request):

    return render(request, 'pages/default/solicitacao_de_acesso.html')

@csrf_exempt
def solicitacao_de_acesso_instituicao(request):

    return render(request, 'pages/default/solicitacao_de_acesso_instituicao.html')

@csrf_exempt
def recuperar_senha(request):

    return render(request, 'pages/default/esqueceuasenha.html')

@csrf_exempt
def pagina_em_desenvolvimento(request):

    return render(request, 'pagina_em_desenvolvimento.html')

@login_required
def perfil(request):
    return render(request,'pages/default/perfil.html')

