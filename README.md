# SAPE - Sistema de Avaliacao de Performance Editorial

Sistema solicitado pela **EBSERH** (Empresa Brasileira de Servicos Hospitalares) para monitorar e coletar automaticamente noticias de sites de interesse, classificar essas noticias segundo os Objetivos Estrategicos da organizacao utilizando Inteligencia Artificial, gerar Dashboards analiticos e calcular Indices de Performance Editorial.

---

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Stack Tecnologica](#stack-tecnologica)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Funcionalidades](#funcionalidades)
  - [Coleta Automatica de Noticias](#1-coleta-automatica-de-noticias)
  - [Classificacao por IA](#2-classificacao-por-ia-objetivos-estrategicos)
  - [Dashboards Analiticos](#3-dashboards-analiticos)
  - [Indices de Performance Editorial](#4-indices-de-performance-editorial)
  - [Nuvem de Palavras](#5-nuvem-de-palavras)
  - [Gestao de Usuarios](#6-gestao-de-usuarios)
- [Taxonomia - Objetivos Estrategicos](#taxonomia---objetivos-estrategicos)
- [Modelos de Dados](#modelos-de-dados)
- [Como Executar](#como-executar)
  - [Pre-requisitos](#pre-requisitos)
  - [Producao (Docker)](#producao-docker)
  - [Desenvolvimento Local](#desenvolvimento-local)
- [Variaveis de Ambiente](#variaveis-de-ambiente)
- [Comandos de Gerenciamento](#comandos-de-gerenciamento)
- [Endpoints Principais](#endpoints-principais)

---

## Visao Geral

O SAPE automatiza o fluxo completo de monitoramento editorial da EBSERH:

1. **Coleta** - Busca noticias via RSS dos portais G1, UOL e Portal EBSERH (gov.br) a cada hora
2. **Classificacao** - Utiliza a API do GPT-4o-mini para classificar cada noticia em um dos 25 Objetivos Estrategicos (OE01 a OE25) organizados em 7 Pilares
3. **Visualizacao** - Gera dashboards interativos com graficos de barras agrupados por Pilar, permitindo drill-down por OE
4. **Indices** - Calcula metricas editoriais (IRS, FRJ, IEC) baseadas em parametros de relevancia configuraveis por OE

---

## Arquitetura

```
                    +-------------+
                    |   Nginx     |  :80
                    |  (reverse   |
                    |   proxy)    |
                    +------+------+
                           |
                    +------+------+
                    |   Django    |  :8000 (Gunicorn)
                    |   (Web)     |
                    +------+------+
                           |
              +------------+------------+
              |            |            |
       +------+------+  +-+--------+ +-+-----------+
       | PostgreSQL   |  |  Redis   | | Celery      |
       | (banco de    |  | (broker) | | Worker +    |
       |  dados)      |  |          | | Beat        |
       +--------------+  +----------+ +-------------+
                                            |
                                      +-----+-----+
                                      | RSS Feeds  |
                                      | (G1, UOL,  |
                                      |  EBSERH)   |
                                      +-----------+
                                            |
                                      +-----+-----+
                                      | OpenAI API |
                                      | (GPT-4o-   |
                                      |  mini)     |
                                      +-----------+
```

### Fluxo de Dados

1. **Celery Beat** agenda a task `atualizar_noticias_task` a cada hora (crontab `minute=0`)
2. **Celery Worker** executa o job que faz fetch dos feeds RSS, parseia o XML, limpa o HTML e insere as noticias novas no PostgreSQL
3. O usuario cria um **Dashboard** definindo periodo e fontes
4. Ao clicar em "Gerar Indicadores com IA", uma task Celery processa cada noticia do periodo:
   - Envia titulo + conteudo para a API OpenAI
   - Recebe JSON com pilar, objetivo estrategico e justificativa
   - Salva a classificacao na noticia
5. O dashboard agrega as contagens por OE e exibe o grafico interativo
6. O usuario pode configurar **parametros de relevancia** por OE e o sistema calcula os indices editoriais

---

## Stack Tecnologica

| Camada | Tecnologia |
|--------|-----------|
| **Backend** | Python 3.12, Django 5.1.7 |
| **Task Queue** | Celery 5.6.2 + Redis 7 |
| **Banco de Dados** | PostgreSQL 16 |
| **IA / NLP** | OpenAI API (GPT-4o-mini), NLTK, scikit-learn (TF-IDF) |
| **Web Scraping** | BeautifulSoup4, Requests, xml.etree |
| **Frontend** | AdminLTE 3, Bootstrap 4, Chart.js, jQuery |
| **Servidor Web** | Gunicorn + Nginx |
| **Infraestrutura** | Docker Compose |
| **Autenticacao** | django-role-permissions (Analista / Supervisor) |

---

## Estrutura do Projeto

```
SAPE/
├── SAPE/                          # Configuracao do projeto Django
│   ├── settings/
│   │   ├── base.py                # Settings compartilhadas
│   │   ├── dev.py                 # Settings de desenvolvimento
│   │   └── prod.py                # Settings de producao (Celery, static root)
│   ├── celery.py                  # Configuracao do Celery + Beat schedule
│   ├── roles.py                   # Roles: AnalistaRole, SupervisorRole
│   ├── urls.py                    # Roteamento principal
│   └── wsgi.py / asgi.py
│
├── aplicativo/                    # App principal
│   ├── models.py                  # News, Dashboard
│   ├── views.py                   # Views (noticias, dashboards, indicadores)
│   ├── tasks.py                   # Celery tasks
│   ├── signals.py                 # Signals Django
│   ├── services/
│   │   ├── atualizar_noticias_job.py   # Scraping RSS (G1, UOL, EBSERH)
│   │   └── indicadores_service.py      # Classificacao IA + agregacao dashboard
│   ├── management/commands/
│   │   ├── atualizar_noticias.py       # Comando manual de atualizacao
│   │   └── import_ebserh_historico.py  # Import historico via scraping do listing
│   └── templates/
│       ├── pages/modulo_avaliacao/
│       │   ├── noticias.html              # Lista de noticias
│       │   ├── visualizar_noticia.html    # Detalhe da noticia + classificacao
│       │   ├── monitoramento.html         # Lista de dashboards
│       │   └── visualizar_dashboard.html  # Dashboard com grafico + indices
│       └── partials/
│           └── menu_lateral.html          # Menu de navegacao
│
├── auth_app/                      # App de autenticacao
│   ├── models.py                  # Usuario (AbstractUser customizado)
│   └── views.py                   # Login, cadastro, perfil, alteracao de senha
│
├── static/                        # Assets (AdminLTE, CSS, JS, plugins)
├── media/                         # Uploads (fotos de usuario)
├── nginx/default.conf             # Configuracao do Nginx
├── docker-compose.yml             # Orquestracao de todos os servicos
├── Dockerfile                     # Imagem Python 3.12 + Django
├── requirements.txt               # Dependencias Python
├── run.sh                         # Script para subir Docker
├── docker_up.sh                   # Script para iniciar Docker daemon
├── docker_down.sh                 # Script para parar Docker daemon
└── reset.sh                       # Script para resetar migrations
```

---

## Funcionalidades

### 1. Coleta Automatica de Noticias

O sistema coleta noticias de tres fontes via feeds RSS:

| Fonte | URL do Feed | Parser |
|-------|------------|--------|
| **EBSERH** | `gov.br/ebserh/.../RSS` | RSS 1.0 (namespaces Dublin Core + content:encoded) |
| **G1** | `g1.globo.com/rss/g1/` | RSS 2.0 padrao (atualmente desativado) |
| **UOL** | `rss.uol.com.br/feed/noticias.xml` | RSS 2.0 com encoding ISO-8859-1 (atualmente desativado) |

**Processo de coleta:**
- Execucao automatica a cada hora via Celery Beat
- Deteccao inteligente de encoding (UTF-8, ISO-8859-1, Windows-1252) com correcao de mojibake
- Deduplicacao por URL (`link` unique)
- Limpeza de HTML (remove scripts, styles, tags nao-textuais)
- Para UOL: enriquecimento via scraping da pagina quando a descricao do RSS e insuficiente
- Bulk insert atomico no banco com `ignore_conflicts`

**Import historico EBSERH:**
- Comando `import_ebserh_historico` para scraping paginado do listing de noticias
- Suporte a filtro por intervalo de datas (`--date-from`, `--date-to`)
- Retry com backoff exponencial para resiliencia de rede
- Extrai titulo, data, descricao e conteudo completo de cada pagina individual

### 2. Classificacao por IA (Objetivos Estrategicos)

Cada noticia e classificada utilizando a API da OpenAI (modelo `gpt-4o-mini`) em:

- **1 Pilar** (dos 7 pilares estrategicos)
- **1 Objetivo Estrategico** (dos 25 OEs)

A classificacao e feita com `temperature=0` e `response_format: json_object`, retornando:

```json
{
  "pilar": "Desenvolvimento Institucional",
  "objetivo_codigo": "OE16",
  "objetivo_titulo": "Fortalecer o reconhecimento e a imagem publica da Ebserh",
  "justificativa": "A noticia aborda acoes de comunicacao institucional..."
}
```

A classificacao pode ser acionada:
- **Individualmente**: na pagina de visualizacao de cada noticia (botao "Gerar Indicadores com IA")
- **Em lote**: ao atualizar um dashboard (classifica todas as noticias do periodo via Celery task com progresso em tempo real)

### 3. Dashboards Analiticos

Os dashboards permitem analisar a distribuicao das noticias por Objetivo Estrategico em um periodo definido:

- **Criacao**: definir titulo, descricao, periodo (data inicial/final) e fontes
- **Grafico de barras** (Chart.js): exibe contagem de noticias por OE, colorido por Pilar
- **Filtro por Pilar**: clicar na legenda filtra o grafico para exibir apenas os OEs daquele pilar
- **Drill-down por OE**: clicar em uma barra exibe a lista de noticias classificadas naquele OE
- **Progresso em tempo real**: barra de progresso durante a geracao de indicadores via polling de status da task Celery
- **Exportar**: suporte a exportacao em PDF

### 4. Indices de Performance Editorial

O sistema calcula metricas para avaliar a performance editorial com base em parametros configuraveis:

**Parametros de Relevancia (por OE):**
- Agenda Corporativa
- Agenda Publica
- Agenda Politica
- Audiencia Alunos
- Audiencia Pacientes
- Audiencia Profissionais
- Midias Sociais

**Metricas Calculadas:**

| Metrica | Descricao |
|---------|-----------|
| **FRJ-R Medio** | Media dos parametros de relevancia nao-zero para cada OE |
| **IRS Apurado** | Contagem real de noticias classificadas no OE |
| **FRJ Apurado** | Frequencia relativa ajustada pela producao |
| **IRS de Referencia** | Producao ideal baseada nos pesos de relevancia |
| **IEC** | Indice de Eficiencia de Cobertura (IRS Apurado / IRS Referencia) |
| **Capacidade de Producao** | Parametro global configuravel pelo usuario |

### 5. Nuvem de Palavras

Extrai as palavras mais relevantes do conteudo de cada noticia usando **TF-IDF** (scikit-learn):

- Remove stopwords em portugues (NLTK)
- Remove pontuacao
- Retorna os top 10 termos por peso TF-IDF
- Acessivel individualmente por noticia

### 6. Gestao de Usuarios

- **Tipos de usuario**: Analista e Supervisor
- **Autenticacao por email** (USERNAME_FIELD = email)
- **Role-based permissions** via `django-role-permissions`
- **Validacao de senha**: minimo 8 caracteres, maiuscula, minuscula e numero
- **Perfil**: edicao de dados pessoais e foto
- **Recuperacao de senha** via email

---

## Taxonomia - Objetivos Estrategicos

| Pilar | OEs |
|-------|-----|
| **Sociedade (usuario SUS)** | OE01: Rede de atencao a saude do SUS, OE02: Cuidado hospitalar, OE03: Cuidados oncologicos, OE04: Atencao Especializada/reducao de filas, OE25: Educacao em saude |
| **Sociedade (estudante)** | OE05: Condicoes de ensino, OE06: Enare, OE07: Docentes e preceptores, OE08: Vagas de residencia |
| **Sociedade (pesquisador)** | OE09: Pesquisa em saude, OE10: Saude digital (AGHU/telessaude) |
| **Resp. Ambiental, Social e Governanca** | OE11: Governanca corporativa, OE12: Sustentabilidade ambiental, OE13: Assedio e discriminacao, OE14: Infraestrutura |
| **Desenvolvimento Institucional** | OE15: Atuacao em Rede, OE16: Imagem publica, OE17: Gestao hospitalar, OE18: Inovacao digital |
| **Sustentabilidade Financeira** | OE19: Gestao do trabalho, OE20: Fontes de financiamento, OE21: Compras e contratacoes |
| **Desenvolvimento do Trabalhador** | OE22: Escuta e dialogo, OE23: Engajamento e valorizacao, OE24: Educacao permanente |

---

## Modelos de Dados

### News (Noticias)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `title` | CharField(500) | Titulo da noticia |
| `link` | URLField (unique) | URL original da noticia |
| `pub_date` | DateField | Data de publicacao |
| `description` | TextField | Descricao/resumo |
| `content` | TextField | Conteudo completo (texto limpo) |
| `source` | CharField(50) | Fonte: "G1", "UOL", "EBSERH" |
| `important_words` | TextField | Palavras-chave extraidas por TF-IDF |
| `classification` | JSONField | Classificacao IA (pilar, OE, justificativa) |

### Dashboard

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `title` | CharField(100) | Titulo do dashboard |
| `description` | CharField(100) | Descricao |
| `initial_date` | DateField | Data inicial do periodo |
| `final_date` | DateField | Data final do periodo |
| `sources` | JSONField (list) | Fontes filtradas (vazio = todas) |
| `oe_count` | JSONField (list) | Array[25] com contagens por OE |
| `oe_news_map` | JSONField (dict) | Mapa OE -> lista de noticias |
| `capacidade_producao` | IntegerField | Parametro de capacidade editorial |
| `oe_relevance_params` | JSONField (list) | Array[25] de parametros de relevancia por OE |

### Usuario

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `email` | EmailField (unique) | Email (usado como login) |
| `nome` | CharField(100) | Nome completo |
| `tipo_usuario` | CharField | "analista" ou "supervisor" |
| `cpf` | CharField(14) | CPF (unico, opcional) |
| `telefone` | CharField(16) | Telefone |
| `foto` | ImageField | Foto de perfil |

---

## Como Executar

### Pre-requisitos

- Docker e Docker Compose
- Chave de API da OpenAI (para classificacao por IA)

### Producao (Docker)

1. Clone o repositorio:
```bash
git clone <repo-url>
cd SAPE
```

2. Crie o arquivo `.env` na raiz:
```env
OPENAI_API_KEY=sk-...
SECRET_KEY=sua-chave-secreta
```

3. Inicie o Docker daemon (se necessario):
```bash
./docker_up.sh
```

4. Suba todos os servicos:
```bash
./run.sh
```

Isso executa `docker compose up -d --build`, subindo:
- **db**: PostgreSQL 16 (porta 5432)
- **redis**: Redis 7 (broker do Celery)
- **web**: Django + Gunicorn (porta 8000, exposto via Nginx)
- **celery_worker**: 4 workers concorrentes
- **celery_beat**: Agendador (atualiza noticias a cada hora)
- **nginx**: Reverse proxy (porta 80)

5. Execute as migrations (primeira vez):
```bash
docker compose exec web python manage.py migrate
```

6. Crie um superusuario:
```bash
docker compose exec web python manage.py createsuperuser
```

7. Acesse em `http://localhost`

### Desenvolvimento Local

1. Crie e ative o virtualenv:
```bash
python3.12 -m venv venv
source venv/bin/activate
```

2. Instale as dependencias:
```bash
pip install -r requirements.txt
```

3. Configure as variaveis de ambiente:
```bash
export DJANGO_SETTINGS_MODULE=SAPE.settings.dev
export OPENAI_API_KEY=sk-...
```

4. Tenha um PostgreSQL rodando (ou suba apenas o db via Docker):
```bash
docker compose up -d db
```

5. Execute migrations e rode o servidor:
```bash
python manage.py migrate
python manage.py runserver
```

6. Para o Celery (em terminais separados):
```bash
celery -A SAPE worker -l info
celery -A SAPE beat -l info
```

---

## Variaveis de Ambiente

| Variavel | Descricao | Padrao |
|----------|-----------|--------|
| `DJANGO_SETTINGS_MODULE` | Modulo de settings | `SAPE.settings.prod` |
| `OPENAI_API_KEY` | Chave da API OpenAI | - |
| `DB_NAME` | Nome do banco | `sape` |
| `DB_USER` | Usuario do banco | `sape` |
| `DB_PASSWORD` | Senha do banco | `sape` |
| `DB_HOST` | Host do banco | `localhost` |
| `DB_PORT` | Porta do banco | `5432` |
| `CELERY_BROKER_URL` | URL do broker Redis | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Backend de resultados | `redis://redis:6379/0` |

---

## Comandos de Gerenciamento

```bash
# Atualizar noticias manualmente (fora do schedule do Celery)
python manage.py atualizar_noticias

# Importar historico de noticias da EBSERH via scraping
python manage.py import_ebserh_historico --date-from 2024-01-01 --date-to 2024-12-31

# Opcoes do import historico:
#   --per-page 30        Itens por pagina
#   --max-pages 9999     Maximo de paginas
#   --sleep 0.2          Delay entre requests (segundos)
#   --no-detail          Nao acessa pagina individual (usa so resumo do listing)
#   --retries 3          Retries para falhas de rede
#   --max-items 500      Para apos N noticias inseridas
```

---

## Endpoints Principais

### Noticias
| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/noticias/` | Lista todas as noticias |
| GET | `/visualizar_noticia/<id>/` | Visualiza detalhes de uma noticia |
| POST | `/noticias/atualizar/iniciar/` | Inicia atualizacao async via Celery |
| POST | `/noticia/<id>/gerar_nuvens_palavras/` | Gera nuvem de palavras |
| POST | `/noticia/<id>/atualizar_indicadores/` | Classifica noticia via IA |

### Dashboards
| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/monitoramento/` | Lista todos os dashboards |
| POST | `/novo-dashboard/` | Cria novo dashboard |
| GET | `/visualizar_dashboard/<id>/` | Visualiza dashboard com grafico |
| POST | `/dashboard/<id>/iniciar/` | Inicia geracao de indicadores (Celery) |
| DELETE | `/dashboard/<id>/remover/` | Remove dashboard |
| POST | `/dashboard/<id>/indices-editoriais/` | Salva parametros de relevancia |
| GET | `/dashboard/<id>/indices-editoriais/get/` | Obtem parametros de relevancia |
| GET | `/task/<task_id>/status/` | Consulta progresso de uma task Celery |

### Autenticacao
| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/login/` | Tela de login |
| POST | `/auth/` | Autenticacao por email/senha |
| GET | `/logout/` | Logout |
| POST | `/cadastrar_usuario/` | Cadastro de novo usuario |
| GET | `/perfil/` | Pagina de perfil |
| POST | `/editar_perfil/` | Editar dados do perfil |
| POST | `/alterar_senha/` | Alterar senha |
