from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import auth
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.hashers import make_password, check_password
from django.core import serializers
from django.core.mail import send_mail
import json
import re
from auth_app.models import Usuario

# Create your views here.

def init(request):
    return render(request, 'home.html')

@csrf_exempt
def tela_login(request):
        return render(request, 'pages/default/login.html')

class Login(LoginView):
    template_name = 'pages/default/login.html'
    #return render(request, 'pages/default/login.html')

@csrf_exempt
def autenticacao(request):
    if request.method == "POST":
        # Get data
        data = json.loads(request.POST.get('auth'))

        login = data['email']
        senha = data['senha']

        try:
            user = Usuario.objects.get(email=login)
        except Usuario.DoesNotExist:
            return JsonResponse({"status": 403})

        # Verifique a senha usando check_password
        if check_password(senha, user.password):
            # Se a autenticação foi válida, faz o login
            auth.login(request, user)
            return JsonResponse({"status": 200})
        else:
            # Se a autenticação não foi válida, retorna 403
            return JsonResponse({"status": 403})
 
@login_required
def logout(request):
    # Logout do usuário
    auth.logout(request)

    return JsonResponse({"status": 200})

@csrf_exempt
def cadastrar_usuario(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            tipo_usuario = data.get("tipo_usuario")

            # Verificar se o tipo é válido
            if tipo_usuario not in [Usuario.DOADOR, Usuario.INSTITUICAO]:
                return JsonResponse({"status": 400, "message": "Tipo de usuário inválido."})

            # Verificar se já existe um usuário com o mesmo email
            if Usuario.objects.filter(email=data["email"]).exists():
                return JsonResponse({"status": 400, "message": "Este e-mail já está cadastrado."})

            # Criar um novo usuário
            usuario = Usuario(
                first_name=data["nome"],
                username=data["email"],
                email=data["email"],
                telefone=data["telefone"],
                tipo_usuario=tipo_usuario,
                password=make_password(data["senha"])
            )

            # Configuração específica para Doador
            if tipo_usuario == Usuario.DOADOR:
                usuario.cpf = data.get("cpf")
                if Usuario.objects.filter(cpf=usuario.cpf).exists():
                    return JsonResponse({"status": 400, "message": "CPF já cadastrado."})

            # Configuração específica para Instituição
            elif tipo_usuario == Usuario.INSTITUICAO:
                usuario.cnpj = data.get("cnpj")
                usuario.nome_responsavel = data.get("nome_responsavel")
                usuario.cpf_responsavel = data.get("cpf_responsavel")

                if Usuario.objects.filter(cnpj=usuario.cnpj).exists():
                    return JsonResponse({"status": 400, "message": "CNPJ já cadastrado."})

            # Salvar usuário no banco
            usuario.save()

            return JsonResponse({"status": 201, "message": "Usuário cadastrado com sucesso."})

        except KeyError as e:
            return JsonResponse({"status": 400, "message": f"Campo obrigatório ausente: {str(e)}"})
        except Exception as e:
            return JsonResponse({"status": 500, "message": f"Erro interno: {str(e)}"})

    return JsonResponse({"status": 405, "message": "Método não permitido."})


@login_required
def editar_perfil(request):
    if request.method == 'POST':
        # Get variáveis da requisição
        data = json.loads(request.POST.get('usuario'))
        foto = request.FILES.get('foto')

        # Get Usuário
        usuario = Usuario.objects.get(pk=request.user.id)

        # Update campos
        if foto:
            usuario.foto = foto
            usuario.save()

        dados_atualizados = {}
        for chave in data:
            if getattr(usuario, chave) != data[chave]:
                dados_atualizados[chave] = data[chave]

        if dados_atualizados:
            Usuario.objects.filter(pk=request.user.id).update(**dados_atualizados)
            usuario.refresh_from_db()

        usuario.save()

        return JsonResponse({'usuario': serializers.serialize('json', [usuario])})
    else:
        return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def alterar_senha(request):
    # Get variáveis da requisição
    data = json.loads(request.POST.get('usuario'))

    senha_atual = data['senha_atual']
    nova_senha = data['nova_senha']

    # Verifique se a senha é forte
    # Pelo menos 8 caracteres de comprimento
    if len(nova_senha) < 8:
        return JsonResponse({"status": 404, "message": "A senha deve conter entre 8 e 12 caracteres."})

    # Pelo menos uma letra maiúscula
    if not re.search(r'[A-Z]', nova_senha):
        return JsonResponse({"status": 404, "message": "A senha deve conter pelo menos uma letra maiúscula."})

    # Pelo menos uma letra minúscula
    if not re.search(r'[a-z]', nova_senha):
        return JsonResponse({"status": 404, "message": "A senha deve conter pelo menos uma letra minúscula."})

    # Pelo menos um número
    if not re.search(r'[0-9]', nova_senha):
        return JsonResponse({"status": 404, "message": "A senha deve conter pelo menos um número."})

    # Get Usuário
    user = Usuario.objects.get(pk=request.user.id)

     # Verifique a senha usando check_password
    if check_password(senha_atual, user.password):
        # Se a autenticação foi válida, altera a senha
        user.password = make_password(nova_senha)
        user.save()
        return JsonResponse({"status": 200})
    else:
        # Se a autenticação não foi válida, retorna 403
        return JsonResponse({"status": 403})

@csrf_exempt
def send_email(request):
    if request.method == 'POST':
        # Extraia os dados
        data = request.POST
        recipients = data['recipients']
        subject = data['subject']
        message = data['message']

        # Email de destino
        destination = []
        destination.append(recipients)

        # Envia email
        send_mail(
            subject=subject,
            message=message,
            from_email='SAPE@.com.br',
            recipient_list=destination,
            fail_silently=False,
        )

        return JsonResponse({'success': True})
