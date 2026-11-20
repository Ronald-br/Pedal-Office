
# 🚲 Pedal Office — Casa das Bicicletas

## Sobre o projeto

O Pedal Office é um sistema web desenvolvido para auxiliar no gerenciamento da Casa das Bicicletas.

O sistema possui um catálogo público para clientes e um painel administrativo para o gerenciamento de produtos, estoque, vendas e informações da loja.

Projeto desenvolvido como parte do Projeto Integrador do curso de Análise e Desenvolvimento de Sistemas do Instituto Federal do Ceará (IFCE), Campus Boa Viagem.

## Tecnologias utilizadas

- Python 3.14 (ambiente Docker)
- Django 5.2.18
- SQLite
- HTML, CSS e JavaScript
- Firebase Authentication para autenticação de clientes
- Autenticação do Django para administradores
- Pillow para processamento de imagens
- Docker e Docker Compose
- Git e GitHub

## Funcionalidades

### Área pública

- Catálogo de produtos
- Pesquisa e filtros por categoria
- Visualização de preços e promoções
- Funcionalidade de favoritos
- Informações e contato da loja

### Área administrativa

- Login administrativo
- Dashboard com indicadores
- Cadastro e gerenciamento de produtos
- Controle de estoque
- Histórico de movimentações
- Alertas de estoque baixo
- Registro de vendas
- Histórico de vendas
- Controle de pagamentos e vendas fiadas
- Configurações da loja
- Perfil do administrador

## Autenticação

O Pedal Office utiliza dois mecanismos de autenticação:

**Administradores:** autenticação do Django.

**Clientes:** Firebase Authentication.

Durante a fase acadêmica, o sistema utiliza contas e dados de teste.

As contas definitivas do proprietário e dos filhos serão configuradas após a avaliação do projeto. Cada responsável terá uma conta individual, com as mesmas permissões administrativas.


## Instalação e execução com Docker

### Pré-requisitos

- Git instalado
- Docker Desktop instalado e em execução
- Terminal PowerShell (Windows)

### 1. Clonar o repositório

```powershell
git clone https://github.com/Ronald-br/Pedal-Office.git
cd Pedal-Office
```

### 2. Preparar o armazenamento local

Na primeira instalação, crie a pasta de dados e um arquivo SQLite vazio:

```powershell
New-Item -ItemType Directory -Force docker-data/media
New-Item -ItemType File docker-data/db.sqlite3
```

**Atenção:** esses comandos de preparação são destinados a uma instalação nova. Não recrie ou substitua um banco de dados que já contém informações.


### 3. Configurar a chave secreta

Antes de iniciar o Docker, crie um arquivo `.env` na raiz do projeto com uma chave secreta exclusiva.

No PowerShell, execute:

```powershell
python -c "from pathlib import Path; import secrets; p=Path('.env'); assert not p.exists(), 'O arquivo .env ja existe; nada foi alterado'; p.write_text('DJANGO_SECRET_KEY=' + secrets.token_urlsafe(64) + '\n', encoding='utf-8'); print('Arquivo .env criado com sucesso.')"
```

O arquivo `.env` é ignorado pelo Git e não deve ser enviado ao GitHub.

**Importante:** execute esse comando apenas na primeira instalação. Não substitua a chave de uma instalação existente sem avaliar os efeitos sobre as sessões e os dados protegidos.


### 4. Construir a imagem Docker

```powershell
docker compose build
```

### 5. Aplicar as migrações

```powershell
docker compose run --rm web python backend/manage.py migrate --noinput
```

### 6. Criar o primeiro administrador

```powershell
docker compose run --rm web python backend/manage.py createsuperuser
```

Informe um nome de usuário e uma senha segura.

### 7. Iniciar o sistema

```powershell
docker compose up -d
```

Acesse:

http://127.0.0.1:8001

### 8. Encerrar o sistema

```powershell
docker compose down
```

Esse comando encerra os contêineres sem excluir o arquivo SQLite armazenado localmente.

### Observações

- O banco SQLite fica em `docker-data/db.sqlite3`.
- As imagens enviadas ficam em `docker-data/media`.
- Esses dados locais não são enviados ao GitHub.
- O sistema utiliza Django para autenticação administrativa e Firebase Authentication para clientes.
- A configuração dos serviços externos deve ser revisada no ambiente de destino.
- O servidor Django utilizado nessa configuração é destinado a desenvolvimento e demonstração local, não a hospedagem pública em produção.

Durante a apresentação acadêmica, são utilizadas contas e informações de teste. As contas definitivas do proprietário e dos filhos serão configuradas após a avaliação do projeto.


## Testes automatizados

O projeto possui 29 testes automatizados utilizando o framework de testes do Django.

Entre os cenários testados estão:

- Movimentações de estoque
- Registro de vendas
- Controle de permissões
- Pagamentos
- Vendas fiadas
- Preços promocionais

Para executar os testes a partir da raiz do projeto:

```bash
python backend/manage.py test core --verbosity 2
```

Na última execução verificada, os 29 testes passaram.

## Estrutura principal

- `backend/` — Código da aplicação Django
- `frontend/` — Templates e recursos da interface
- `Dockerfile` — Configuração da imagem Docker
- `compose.yaml` — Configuração do serviço Docker
- `requirements.txt` — Dependências Python
- `.gitignore` — Arquivos ignorados pelo Git

## Estado do projeto

O Pedal Office encontra-se em fase de validação e apresentação acadêmica.

Os registros de demonstração não representam necessariamente operações reais da loja.

A implantação definitiva, a configuração das contas dos responsáveis e a preparação dos dados de produção serão realizadas posteriormente.

O servidor de desenvolvimento do Django utilizado no Docker não deve ser exposto diretamente à internet como ambiente de produção.

## Informações acadêmicas

**Projeto:** Pedal Office — Casa das Bicicletas

**Curso:** Análise e Desenvolvimento de Sistemas

**Instituição:** Instituto Federal do Ceará — IFCE

**Campus:** Boa Viagem

**Desenvolvedor:** Ronald Vieira
