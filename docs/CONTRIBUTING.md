# Guia de Contribuição

Este documento descreve como você pode contribuir com o projeto.

## Como posso contribuir

### 1. Verificar Issues Existentes

Antes de iniciar qualquer desenvolvimento:

1. Acesse a [aba Issues do repositório](https://github.com/DoctahW/organizei/issues)
2. Procure por uma issue relacionada à funcionalidade que você deseja implementar
3. Se já existe uma issue aberta, verifique se alguém já está trabalhando nela

### 2. Criar uma Nova Issue (se necessário)

Se a funcionalidade ainda não tem uma issue:

1. Clique em "New Issue"
2. Descreva a funcionalidade ou bug de forma clara
3. Use labels apropriadas (bug, enhancement, feature, etc.)
4. Aguarde feedback dos desenvolvedores antes de começar o desenvolvimento

### 3. Fork do Repositório

1. Clique no botão "Fork" no topo da página do repositório
2. Isso criará uma cópia do projeto na sua conta

### 4. Clone seu Fork Localmente

```bash
git clone https://github.com/SEU_USUARIO/organizei.git
cd organizei
```

### 5. Criar uma Branch

Crie uma branch com um nome descritivo relacionado à issue:

```bash
git checkout -b feature/sua-feature
# ou
git checkout -b fix/descricao-do-bug
```

**Convenção de nomes:**
- `feature/nome-da-feature` - para novas funcionalidades
- `fix/descricao-do-bug` - para correções de bugs
- `docs/descricao` - para documentação

---

## Setup do Projeto

### Pré-requisitos

- Python 3.10+
- Git
- pip 

### 1. Clonar o Repositório

```bash
git clone https://github.com/DoctahW/organizei.git
cd organizei
```

### 2. Criar Ambiente Virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

O arquivo `.env` já contém configurações padrão para desenvolvimento:

```env
DEBUG=True
SECRET_KEY=django-insecure-change-me
ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
USE_I18N=True
USE_TZ=True
```

Se precisar de configurações diferentes, você pode criar um `.env.local`.

### 5. Aplicar Migrações do Banco de Dados

```bash
python manage.py migrate
```

---

## Executar o Projeto

### Iniciar o Servidor de Desenvolvimento

```bash
python manage.py runserver
```

O servidor será iniciado em `http://127.0.0.1:8000`

**Credenciais de Teste:**
- Usuário: `admin`
- Senha: `1234`

---

## Testes

### Executar Testes E2E (Selenium)

```bash
python manage.py test
```

### Testes Específicos

```bash
# Testes de um app específico
python manage.py test apps.transactions

# Teste de uma classe específica
python manage.py test apps.transactions.tests.TestClassName

# Teste de um método específico
python manage.py test apps.transactions.tests.TestClassName.test_method_name
```

---

## Linting e Formatação

### Executar Ruff (Linter)

```bash
ruff check .
```

### Corrigir Automaticamente Problemas de Linting

```bash
ruff check --fix .
```

---

## Processo de Pull Request

### 1. Commit suas Mudanças

Faça commits com mensagens claras e descritivas:

```bash
git add .
git commit -m "feat: adiciona nova funcionalidade"
```

**Convenção de mensagens:**
- `feat:` - nova funcionalidade
- `fix:` - correção de bug
- `docs:` - documentação
- `style:` - formatação, sem mudanças de código
- `refactor:` - refatoração de código
- `test:` - adição ou modificação de testes
- `chore:` - mudanças em build, dependências, etc.

### 2. Push para seu Fork

```bash
git push origin feature/sua-feature
```

### 3. Abrir um Pull Request

1. Vá para o repositório original (https://github.com/DoctahW/organizei)
2. Você verá um banner sugerindo abrir um PR
3. Clique em "Compare & Pull Request"
4. Preencha a descrição do PR:
   - Descreva as mudanças realizadas
   - Referencie a issue: `Closes #123`
   - Explique o motivo das mudanças
   - Incluindo screenshots se aplicável

### 4. Aguardar Revisão

- Um revisor analisará seu código
- Pode ser solicitadas mudanças
- Uma vez aprovado, seu PR será mergeado

---

## Padrões de Código

### Geral

- Mantenha o código limpo e legível
- Siga a convenção de nomenclatura do projeto
- Use nomes descritivos para variáveis e funções

### HTML/CSS/JavaScript

- Use indentação consistente
- Mantenha o código semântico
- Prefira classes CSS a IDs para styling
- Comente seções complexas

---

## Estrutura do Projeto

```
organizei/
├── apps/                  # Aplicações Django
│   ├── accounts/         # Gerenciamento de contas
│   ├── transactions/     # Transações
│   ├── categories/       # Categorias
│   ├── goals/           # Metas
│   ├── investments/     # Investimentos
│   └── subscriptions/   # Assinaturas
├── project/             # Configurações do Django
├── static/              # Arquivos estáticos (CSS, JS)
├── templates/           # Templates HTML
├── manage.py            # Script de gerenciamento Django
├── requirements.txt     # Dependências Python
├── .env                 # Variáveis de ambiente
└── README.md            # Documentação principal
```

---

## Boas Práticas

1. **Sempre crie uma branch** - Nunca faça commits diretamente em `main`
2. **Mantenha seu fork atualizado** - Sincronize com o repositório original regularmente
3. **Escreva testes** - Ao adicionar nova funcionalidade, inclua testes
4. **Revise seu próprio código** - Antes de fazer PR, revise suas mudanças
5. **Mencione issues** - Referencie issues relacionadas nos commits e PRs
6. **Seja descritivo** - Em commits, PRs e comments, seja claro e conciso

---

## Precisa de Ajuda?

- Leia o [README.md](README.md) para mais informações sobre o projeto
- Consulte a [documentação do Django](https://docs.djangoproject.com/)
- Abra uma [discussão no GitHub](https://github.com/DoctahW/organizei/discussions)
- Entre em contato com os mantedores

---

## Código de Conduta

Por favor, seja respeitoso e inclusivo ao interagir com a comunidade. Todos são bem-vindos!

Obrigado por contribuir! 🎉
