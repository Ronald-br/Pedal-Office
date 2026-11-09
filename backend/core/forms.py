
from decimal import Decimal

from django import forms
from .models import Produto


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'imagem',
            'nome',
            'categoria',
            'preco',
            'quantidade',
            'estoque_minimo',
            'em_promocao',
            'preco_promocional',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Ex.: Bike aro 29 21 marchas',
            }),
            'preco': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00',
            }),
            'quantidade': forms.NumberInput(attrs={
                'min': '0',
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'min': '0',
                'placeholder': 'Ex.: 2',
            }),
            'preco_promocional': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0,00',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        em_promocao = cleaned_data.get('em_promocao')
        preco = cleaned_data.get('preco')
        preco_promocional = cleaned_data.get('preco_promocional')

        if em_promocao:
            if preco_promocional is None:
                self.add_error(
                    'preco_promocional',
                    'Informe o preço promocional.'
                )
            elif preco_promocional <= Decimal('0'):
                self.add_error(
                    'preco_promocional',
                    'O preço promocional deve ser maior que zero.'
                )
            elif preco is not None and preco_promocional >= preco:
                self.add_error(
                    'preco_promocional',
                    'O preço promocional deve ser menor que o preço normal.'
                )
        else:
            cleaned_data['preco_promocional'] = None

        return cleaned_data


class VendaForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.none(),
        label='Produto',
        empty_label='Selecione um produto'
    )

    quantidade = forms.IntegerField(
        label='Quantidade vendida',
        min_value=1,
        initial=1
    )

    nome_cliente = forms.CharField(
        label='Nome do cliente',
        max_length=150,
        required=True
    )

    forma_pagamento = forms.ChoiceField(
        label='Forma de pagamento',
        choices=[
            ('', 'Selecione a forma de pagamento'),
            ('dinheiro', 'Dinheiro'),
            ('pix', 'Pix'),
            ('debito', 'Cartão de débito'),
            ('credito', 'Cartão de crédito'),
            ('outro', 'Outro'),
        ],
        required=False
    )

    situacao_pagamento = forms.ChoiceField(
        label='Situação do pagamento',
        choices=[
            ('pago', 'Pago'),
            ('fiado', 'Fiado'),
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['produto'].queryset = (
            Produto.objects.filter(
                ativo=True,
                quantidade__gt=0
            ).order_by('nome')
        )

    def clean(self):
        dados = super().clean()

        if (
            dados.get('situacao_pagamento') == 'pago'
            and not dados.get('forma_pagamento')
        ):
            self.add_error(
                'forma_pagamento',
                'Informe como o cliente pagou.'
            )

        return dados

