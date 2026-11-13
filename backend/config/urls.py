
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from core.views import (
    inicio,
    login_view,
    dashboard,
    produtos,
    novo_produto,
    editar_produto,
    vendas,
    historico_vendas,
    quitar_venda_fiada,
    controle_estoque,
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Catálogo público
    path('', inicio, name='inicio'),

    # Autenticação
    path('login/', login_view, name='login'),

    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Produtos
    path('produtos/', produtos, name='produtos'),

    path(
        'produtos/novo/',
        novo_produto,
        name='novo_produto'
    ),

    path(
        'produtos/editar/<int:produto_id>/',
        editar_produto,
        name='editar_produto'
    ),

    # Vendas
    path(
        'vendas/',
        vendas,
        name='vendas'
    ),

    path(
        'vendas/historico/',
        historico_vendas,
        name='historico_vendas'
    ),

    path(
        'vendas/<int:venda_id>/quitar/',
        quitar_venda_fiada,
        name='quitar_venda_fiada'
    ),

    # Controle de estoque
    path(
        'estoque/',
        controle_estoque,
        name='controle_estoque'
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
