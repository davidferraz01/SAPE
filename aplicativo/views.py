from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import *
from rolepermissions.decorators import has_permission_decorator
import json
from auth_app.models import Usuario
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

@csrf_exempt
def home(request):
    return render(request, 'home.html')

# views.py
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import News


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

    for fonte_nome, url in fontes.items():
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                continue

            content = response.content
            if fonte_nome == "UOL":
                content = content.decode("iso-8859-1")
            root = ET.fromstring(content)

            # Formatação específica por fonte
            if fonte_nome == "EBSERH":
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
                            pub_date=pub_date_text,
                            description=description_text,
                            content=content_text,
                            source=fonte_nome
                        )
                        novas += 1

            else:
                channel = root.find("channel")
                items = channel.findall("item")

                for item in items:
                    title = item.find("title").text
                    link = item.find("link").text
                    pub_date = item.find("pubDate").text
                    description = item.find("description").text or title

                    if not News.objects.filter(link=link).exists():
                        News.objects.create(
                            title=title,
                            link=link,
                            pub_date=pub_date,
                            description=description,
                            content="",
                            source=fonte_nome
                        )
                        novas += 1

        except Exception as e:
            print(f"Erro ao processar fonte {fonte_nome}: {e}")
            continue

    return JsonResponse({"status": "ok", "novas": novas})




# Doacao
@login_required
def doar(request):
    if request.method == 'GET':
        noticias = News.objects.order_by('-id')  # Ordenando pela mais recente

        context = {'noticias': noticias}

        return render(request, 'pages/doacao/doar.html', context)
    

@login_required
def minhas_doacoes(request):
    if request.method == 'GET':
        # Filtrando as doacoes pelo usuario logado
        #doacao = Dashboard.objects.filter(fk_usuario=request.user).order_by('-id')

        #context = {'doacao': doacao}

        return render(request, 'pages/doacao/minhas_doacoes.html') #, context)

@login_required
def visualizar_campanha_doar(request, id):
    campanha = get_object_or_404(Campanha, pk=id)

    context = {
        'campanha': campanha
    }

    return render(request, 'pages/doacao/visualizar_campanha_doar.html', context)
    

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
        # Filtrando as campanhas pelo usuário logado
        campanhas = Campanha.objects.filter(fk_usuario=request.user).order_by('-id')

        context = {'campanhas': campanhas}

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

