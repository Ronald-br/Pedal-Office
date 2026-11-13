
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Produto, Venda, MovimentacaoEstoque


# ==========================================================
# VALIDAÇÕES DO CONTROLE DE ESTOQUE
# ==========================================================

def validar_funcionario(funcionario):
    if (
        not funcionario
        or not funcionario.is_authenticated
        or not funcionario.is_staff
    ):
        raise ValidationError(
            "Somente funcionários autorizados podem realizar esta operação."
        )


def validar_quantidade(quantidade):
    if type(quantidade) is not int or quantidade <= 0:
        raise ValidationError(
            "A quantidade deve ser um inteiro maior que zero."
        )


# ==========================================================
# ENTRADA DE MERCADORIAS
# ==========================================================

@transaction.atomic
def registrar_entrada_estoque(
    produto_id,
    quantidade,
    funcionario,
    motivo='compra',
    observacao=''
):
    validar_funcionario(funcionario)
    validar_quantidade(quantidade)

    motivos_validos = {'compra', 'ajuste', 'outro'}

    if motivo not in motivos_validos:
        raise ValidationError(
            "Motivo inválido para entrada de estoque."
        )

    if not isinstance(observacao, str):
        raise ValidationError("A observação deve ser um texto.")

    produto = Produto.objects.filter(
        pk=produto_id,
        ativo=True
    ).first()

    if produto is None:
        raise ValidationError(
            "Produto não encontrado ou inativo."
        )

    Produto.objects.filter(
        pk=produto.pk
    ).update(
        quantidade=F('quantidade') + quantidade
    )

    movimentacao = MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo='entrada',
        motivo=motivo,
        quantidade=quantidade,
        funcionario=funcionario,
        observacao=observacao.strip()
    )

    return movimentacao


# ==========================================================
# SAÍDA MANUAL DE MERCADORIAS
# ==========================================================

@transaction.atomic
def registrar_saida_estoque(
    produto_id,
    quantidade,
    funcionario,
    motivo='outro',
    observacao=''
):
    validar_funcionario(funcionario)
    validar_quantidade(quantidade)

    motivos_validos = {'perda', 'dano', 'ajuste', 'outro'}

    if motivo not in motivos_validos:
        raise ValidationError(
            "Motivo inválido para saída manual de estoque."
        )

    if not isinstance(observacao, str):
        raise ValidationError("A observação deve ser um texto.")

    produto = Produto.objects.filter(
        pk=produto_id,
        ativo=True
    ).first()

    if produto is None:
        raise ValidationError(
            "Produto não encontrado ou inativo."
        )

    atualizado = Produto.objects.filter(
        pk=produto.pk,
        ativo=True,
        quantidade__gte=quantidade
    ).update(
        quantidade=F('quantidade') - quantidade
    )

    if atualizado == 0:
        raise ValidationError(
            "Estoque insuficiente para realizar a saída."
        )

    movimentacao = MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo='saida',
        motivo=motivo,
        quantidade=quantidade,
        funcionario=funcionario,
        observacao=observacao.strip()
    )

    return movimentacao


# ==========================================================
# REGISTRO DE VENDAS
# ==========================================================

@transaction.atomic
def registrar_venda(
    produto_id,
    quantidade,
    funcionario,
    nome_cliente='',
    forma_pagamento='',
    situacao_pagamento='pago'
):
    validar_quantidade(quantidade)
    validar_funcionario(funcionario)

    nome_cliente = nome_cliente.strip()
    forma_pagamento = forma_pagamento.strip()

    if len(nome_cliente) > 150:
        raise ValidationError("Nome do cliente muito longo.")

    formas_validas = {
        'dinheiro', 'pix', 'debito', 'credito', 'outro'
    }

    if situacao_pagamento not in {'pago', 'fiado'}:
        raise ValidationError("Situação de pagamento inválida.")

    if forma_pagamento and forma_pagamento not in formas_validas:
        raise ValidationError("Forma de pagamento inválida.")

    if situacao_pagamento == 'pago' and nome_cliente and not forma_pagamento:
        raise ValidationError("Informe a forma de pagamento.")

    if situacao_pagamento == 'fiado' and not nome_cliente:
        raise ValidationError(
            "Informe o nome do cliente para vendas fiadas."
        )

    if situacao_pagamento == 'fiado' and forma_pagamento:
        raise ValidationError(
            "Uma venda fiada ainda não possui forma de pagamento."
        )

    produto = Produto.objects.filter(
        pk=produto_id,
        ativo=True
    ).first()

    if produto is None:
        raise ValidationError("Produto não encontrado ou inativo.")

    preco = produto.preco

    if produto.em_promocao:
        if (
            produto.preco_promocional is None
            or produto.preco_promocional <= Decimal("0")
        ):
            raise ValidationError(
                "O preço promocional é inválido."
            )

        preco = produto.preco_promocional

    atualizado = Produto.objects.filter(
        pk=produto.pk,
        ativo=True,
        quantidade__gte=quantidade
    ).update(
        quantidade=F("quantidade") - quantidade
    )

    if atualizado == 0:
        raise ValidationError(
            "Estoque insuficiente para realizar a venda."
        )

    venda = Venda.objects.create(
        produto=produto,
        quantidade=quantidade,
        preco_unitario=preco,
        funcionario=funcionario,
        nome_cliente=nome_cliente,
        forma_pagamento=forma_pagamento,
        situacao_pagamento=situacao_pagamento,
        data_pagamento=(
            timezone.now()
            if situacao_pagamento == 'pago'
            else None
        )
    )

    # Registra a saída no histórico, sem descontar novamente.
    MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo='saida',
        motivo='venda',
        quantidade=quantidade,
        funcionario=funcionario,
        venda=venda,
        observacao=f'Venda #{venda.pk}'
    )

    return venda


# ==========================================================
# QUITAÇÃO DE VENDAS FIADAS
# ==========================================================

@transaction.atomic
def quitar_fiado(venda_id, forma_pagamento, funcionario):
    """
    Registra o pagamento de uma venda fiada existente,
    sem criar outra venda ou alterar o estoque.
    """

    if (
        not funcionario
        or not funcionario.is_authenticated
        or not funcionario.is_staff
    ):
        raise ValidationError(
            "Somente funcionários autorizados podem quitar fiados."
        )

    if not isinstance(forma_pagamento, str):
        raise ValidationError(
            "Informe uma forma de pagamento válida."
        )

    forma_pagamento = forma_pagamento.strip()

    formas_validas = {
        codigo for codigo, nome in Venda.FORMAS_PAGAMENTO
    }

    if forma_pagamento not in formas_validas:
        raise ValidationError(
            "Selecione uma forma de pagamento válida."
        )

    atualizado = Venda.objects.filter(
        pk=venda_id,
        situacao_pagamento='fiado',
        data_pagamento__isnull=True
    ).update(
        situacao_pagamento='pago',
        forma_pagamento=forma_pagamento,
        data_pagamento=timezone.now()
    )

    if atualizado == 0:
        if not Venda.objects.filter(pk=venda_id).exists():
            raise ValidationError(
                "Venda não encontrada."
            )

        raise ValidationError(
            "Esta venda não está pendente de pagamento."
        )

    return Venda.objects.get(pk=venda_id)
