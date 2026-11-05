
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
