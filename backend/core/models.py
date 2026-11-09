
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Produto(models.Model):

    CATEGORIAS = [
        ('bike_nova', 'Bike nova'),
        ('bike_usada', 'Bike usada'),
        ('peca', 'Peça'),
        ('acessorio', 'Acessório'),
    ]

    nome = models.CharField(max_length=150)

    descricao = models.TextField(blank=True)

    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIAS
    )

    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    quantidade = models.PositiveIntegerField(default=0)

    estoque_minimo = models.PositiveIntegerField(default=3)

    imagem = models.ImageField(
        upload_to='produtos/',
        blank=True,
        null=True
    )

    em_promocao = models.BooleanField(default=False)

    preco_promocional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['nome']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'



class Loja(models.Model):
    nome = models.CharField(max_length=150)

    logo = models.ImageField(
        upload_to='lojas/',
        blank=True,
        null=True
    )

    endereco = models.CharField(
        max_length=255,
        blank=True
    )

    horario_funcionamento = models.CharField(
        max_length=200,
        blank=True
    )

    whatsapp = models.CharField(
        max_length=20,
        blank=True
    )

    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'

from django.conf import settings


class Venda(models.Model):
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='vendas'
    )

    quantidade = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    data_venda = models.DateTimeField(auto_now_add=True)

    
    FORMAS_PAGAMENTO = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'Pix'),
        ('debito', 'Cartão de débito'),
        ('credito', 'Cartão de crédito'),
        ('outro', 'Outro'),
    ]

    SITUACOES_PAGAMENTO = [
        ('pago', 'Pago'),
        ('fiado', 'Fiado'),
    ]

    nome_cliente = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMAS_PAGAMENTO,
        blank=True,
        default=''
    )

    situacao_pagamento = models.CharField(
        max_length=10,
        choices=SITUACOES_PAGAMENTO,
        default='pago'
    )

    data_pagamento = models.DateTimeField(
        blank=True,
        null=True
    )


    @property
    def total(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f'Venda #{self.pk} - {self.produto.nome}'

    class Meta:
        ordering = ['-data_venda']
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'