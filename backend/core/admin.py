
from django.contrib import admin
from .models import Produto,Loja


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'categoria',
        'preco',
        'quantidade',
        'ativo',
    )

    list_filter = ('categoria', 'ativo')

    search_fields = ('nome', 'descricao')

    list_editable = ('ativo',)


@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'endereco',
        'horario_funcionamento',
        'ativa',
    )

    search_fields = ('nome', 'endereco')

    list_filter = ('ativa',)
