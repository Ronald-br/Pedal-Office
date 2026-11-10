
from django.core.exceptions import ValidationError

from .forms import VendaForm
from .models import Venda
from .services import registrar_venda, quitar_fiado

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .models import Produto, Loja, Venda
from .forms import ProdutoForm
from django.views.decorators.http import require_POST


def inicio(request):
    lista_produtos = Produto.objects.filter(ativo=True).order_by('-id')

    loja = Loja.objects.filter(ativa=True).first()

    contexto = {
        'produtos': lista_produtos,
        'loja': loja,
    }

    return render(request, 'core/inicio.html', contexto)


def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('username')
        senha = request.POST.get('password')

        user = authenticate(
            request,
            username=usuario,
            password=senha
        )

        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('dashboard')

        return render(request, 'core/login.html', {
            'erro': 'Usuário ou senha inválidos, ou acesso não autorizado.'
        })

    return render(request, 'core/login.html')


@login_required(login_url='login')
@user_passes_test(lambda user: user.is_staff, login_url='login')
def dashboard(request):
    from django.db.models import F, Sum
    from django.utils import timezone

    hoje = timezone.localdate()

    produtos_ativos = Produto.objects.filter(ativo=True)

    vendas_do_mes = Venda.objects.filter(
        data_venda__year=hoje.year,
        data_venda__month=hoje.month
    )

    estoque_baixo = produtos_ativos.filter(
        quantidade__lte=F('estoque_minimo')
    ).order_by('quantidade', 'nome')

    ranking_vendas = (
        vendas_do_mes
        .values('produto__nome')
        .annotate(total_vendido=Sum('quantidade'))
        .order_by('-total_vendido')[:5]
    )

    produtos_mais_vendidos = [
        {
            'nome': item['produto__nome'],
            'total_vendido': item['total_vendido']
        }
        for item in ranking_vendas
    ]

    bikes_estoque = (
        produtos_ativos
        .filter(categoria__in=['bike_nova', 'bike_usada'])
        .aggregate(total=Sum('quantidade'))['total']
        or 0
    )

    contexto = {
        'vendas_mes': vendas_do_mes.count(),
        'bikes_estoque': bikes_estoque,
        'produtos_cadastrados': produtos_ativos.count(),
        'total_estoque_baixo': estoque_baixo.count(),
        'produtos_estoque_baixo': estoque_baixo[:5],
        'produtos_mais_vendidos': produtos_mais_vendidos,
    }

    return render(request, 'core/dashboard.html', contexto)


@login_required(login_url='login')
@user_passes_test(lambda user: user.is_staff, login_url='login')
def produtos(request):
    lista_produtos = Produto.objects.all()

    busca = request.GET.get('busca', '').strip()
    categoria = request.GET.get('categoria', 'todos')

    if busca:
        lista_produtos = lista_produtos.filter(
            nome__icontains=busca
        )

    categorias_validas = {
        'bike_nova',
        'bike_usada',
        'peca',
        'acessorio',
    }

    if categoria in categorias_validas:
        lista_produtos = lista_produtos.filter(
            categoria=categoria
        )

    contexto = {
        'produtos': lista_produtos,
        'total_produtos': Produto.objects.count(),
        'busca': busca,
        'categoria_atual': categoria,
    }

    return render(
        request,
        'core/produtos.html',
        contexto
    )


@login_required(login_url='login')
@user_passes_test(lambda user: user.is_staff, login_url='login')
def novo_produto(request):
    if request.method == 'POST':
        formulario = ProdutoForm(
            request.POST,
            request.FILES
        )

        if formulario.is_valid():
            formulario.save()

            messages.success(
                request,
                'Produto cadastrado com sucesso!'
            )

            return redirect('produtos')

    else:
        formulario = ProdutoForm()

    return render(
        request,
        'core/novo_produto.html',
        {'formulario': formulario}
    )


@login_required(login_url='login')
@user_passes_test(lambda user: user.is_staff, login_url='login')
def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == 'POST':
        formulario = ProdutoForm(
            request.POST,
            request.FILES,
            instance=produto
        )

        if formulario.is_valid():
            formulario.save()

            messages.success(
                request,
                'Produto atualizado com sucesso!'
            )

            return redirect('produtos')

    else:
        formulario = ProdutoForm(instance=produto)

    return render(
        request,
        'core/novo_produto.html',
        {
            'formulario': formulario,
            'produto': produto,
            'modo_edicao': True,
        }
    )


@login_required(login_url='login')
@user_passes_test(lambda user: user.is_staff, login_url='login')
def vendas(request):
    if request.method == 'POST':
        formulario = VendaForm(request.POST)

        if formulario.is_valid():
            produto = formulario.cleaned_data['produto']
            quantidade = formulario.cleaned_data['quantidade']

            try:
                registrar_venda(
                    produto_id=produto.id,
                    quantidade=quantidade,
                    funcionario=request.user,
                    nome_cliente=formulario.cleaned_data.get('nome_cliente'),
                    forma_pagamento=formulario.cleaned_data.get('forma_pagamento'),
                    situacao_pagamento=formulario.cleaned_data.get('situacao_pagamento'),
                )

                messages.success(
                    request,
                    'Venda registrada com sucesso! Estoque atualizado.'
                )

                return redirect('vendas')

            except ValidationError as erro:
                formulario.add_error(None, erro)

    else:
        formulario = VendaForm()

    historico = Venda.objects.select_related(
        'produto',
        'funcionario'
    ).order_by('-data_venda')[:20]

    produtos_disponiveis = Produto.objects.filter(
        ativo=True,
        quantidade__gt=0
    ).order_by('nome')

    precos_produtos = {
        str(produto.id): {
            'preco': str(
                produto.preco_promocional
                if produto.em_promocao
                and produto.preco_promocional is not None
                else produto.preco
            ),
            'estoque': produto.quantidade,
        }
        for produto in produtos_disponiveis
    }

    return render(
        request,
        'core/vendas.html',
        {
            'formulario': formulario,
            'historico': historico,
            'precos_produtos': precos_produtos,
        }
    )


@login_required(login_url='login')
@user_passes_test(
    lambda user: user.is_staff,
    login_url='login'
)
def historico_vendas(request):
    historico = (
        Venda.objects
        .select_related('produto', 'funcionario')
        .order_by('-data_venda')
    )

    return render(
        request,
        'core/historico_vendas.html',
        {
            'historico': historico,
        }
    )


@login_required(login_url='login')
@user_passes_test(
    lambda user: user.is_staff,
    login_url='login'
)
@require_POST
def quitar_venda_fiada(request, venda_id):
    forma_pagamento = request.POST.get(
        'forma_pagamento', ''
    )

    try:
        venda = quitar_fiado(
            venda_id=venda_id,
            forma_pagamento=forma_pagamento,
            funcionario=request.user
        )

        messages.success(
            request,
            f'Fiado do cliente {venda.nome_cliente} '
            'quitado com sucesso!'
        )

    except ValidationError as erro:
        messages.error(
            request,
            ' '.join(erro.messages)
        )

    return redirect('historico_vendas')
