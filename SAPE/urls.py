"""
URL configuration for SAPE project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from aplicativo.views import *
from auth_app.views import *
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

urlpatterns = [

    path('', init),
    path('home/', home, name='home'),

    # Noticias
    path('noticias/', pagina_noticias, name='noticias'),
    path('visualizar_noticia/<int:id>/', visualizar_noticia, name='visualizar_noticia'),
    path('atualizar-noticias/', atualizar_noticias, name='atualizar_noticias'),
    path('noticia/<int:id>/gerar_nuvens_palavras/', atualizar_important_words, name='atualizar_important_words'),
    path('noticia/<int:id>/atualizar_indicadores/', gerar_indicadores, name='gerar_indicadores'),

    # Dashboard
    path('novo-dashboard/<str:initial_date>/<str:final_date>/<str:name>/<str:description>/', novo_dashboard, name='novo_dashboard'),
    path('noticia/<int:id>/atualizar_dashboard/', atualizar_dashboard, name='atualizar_dashboard'),
    path('visualizar_dashboard/<int:id>/', visualizar_dashboard, name='visualizar_dashboard'),
    path('monitoramento/', pagina_monitoramento, name='dashboards'),


    # Doacao
    path('cadastrar_doacao_request/', cadastrar_doacao_request, name='cadastrar_doacao_request'),
    path('cadastrar_doacao/<int:id>/', cadastrar_doacao, name='cadastrar_doacao'),

    # Campanhas
    path('minhas_campanhas/', minhas_campanhas, name='minhas_campanhas'),
    path('cadastrar_campanha/', cadastrar_campanha, name='cadastrar_campanha'),
    path('cadastrar_campanha_request/', cadastrar_campanha_request, name='cadastrar_campanha_request'),
    path('remover_campanha/<int:id>/', remover_campanha, name='remover_campanha'),
    path('visualizar_campanha/<int:id>/', visualizar_campanha, name='visualizar_campanha'),
   
    # Login
    path('cadastrar_usuario/', cadastrar_usuario, name='cadastrar_usuario'),
    path('auth/', autenticacao, name='auth'),
    path('login/', tela_login, name='login'),
    path('logout/', logout, name='logout'),
    path('solicitacao_de_acesso/', solicitacao_de_acesso, name='solicitacao_de_acesso'),
    path('solicitacao_de_acesso_instituicao/', solicitacao_de_acesso_instituicao, name='solicitacao_de_acesso_instituicao'),
    path('perfil/', perfil, name='perfil'),
    path('editar_perfil/', editar_perfil, name='editar_perfil'),
    path('alterar_senha/', alterar_senha, name='alterar_senha'), 
    path('recuperar_senha/', recuperar_senha, name='recuperar_senha'), 
    path('reset_password/', PasswordResetView.as_view(), name='password_reset'),
    path('reset_password/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset_password/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password/complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('send_email/', send_email, name="send_email"),
    path('pagina_em_desenvolvimento/', pagina_em_desenvolvimento, name='pagina_em_desenvolvimento'),
    
    path('admin/', admin.site.urls),
    
   

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
