

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .models import Produto,Loja
from .forms import ProdutoForm



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
    return render(request, 'core/dashboard.html')


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
