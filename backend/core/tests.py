
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Produto, Venda, MovimentacaoEstoque
from .services import (
    registrar_venda,
    quitar_fiado,
    registrar_entrada_estoque,
    registrar_saida_estoque,
)


# ==========================================================
# TESTES EXISTENTES: VENDAS E FIADO
# ==========================================================

class VendaTestCase(TestCase):

    def setUp(self):
        User = get_user_model()

        self.funcionario = User.objects.create_user(
            username="funcionario_teste",
            password="SenhaTeste123!",
            is_staff=True
        )

        self.cliente = User.objects.create_user(
            username="cliente_teste",
            password="SenhaTeste123!"
        )

        self.produto = Produto.objects.create(
            nome="Bicicleta Aro 29",
            categoria="bike_nova",
            preco=Decimal("1200.00"),
            quantidade=5,
            estoque_minimo=2
        )

    def test_registrar_venda_desconta_estoque(self):
        venda = registrar_venda(
            self.produto.id, 2, self.funcionario
        )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 3)
        self.assertEqual(venda.quantidade, 2)
        self.assertEqual(venda.total, Decimal("2400.00"))

    def test_impedir_venda_sem_estoque_suficiente(self):
        with self.assertRaises(ValidationError):
            registrar_venda(
                self.produto.id, 10, self.funcionario
            )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 5)
        self.assertEqual(Venda.objects.count(), 0)

    def test_impedir_quantidade_zero(self):
        with self.assertRaises(ValidationError):
            registrar_venda(
                self.produto.id, 0, self.funcionario
            )

        self.assertEqual(Venda.objects.count(), 0)

    def test_impedir_venda_por_usuario_nao_autorizado(self):
        with self.assertRaises(ValidationError):
            registrar_venda(
                self.produto.id, 1, self.cliente
            )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 5)
        self.assertEqual(Venda.objects.count(), 0)

    def test_registrar_venda_com_preco_promocional(self):
        self.produto.em_promocao = True
        self.produto.preco_promocional = Decimal("1000.00")
        self.produto.save()

        venda = registrar_venda(
            self.produto.id, 2, self.funcionario
        )

        self.assertEqual(
            venda.preco_unitario,
            Decimal("1000.00")
        )
        self.assertEqual(
            venda.total,
            Decimal("2000.00")
        )

    def test_impedir_venda_de_produto_inativo(self):
        self.produto.ativo = False
        self.produto.save()

        with self.assertRaises(ValidationError):
            registrar_venda(
                self.produto.id, 1, self.funcionario
            )

        self.assertEqual(Venda.objects.count(), 0)

    def test_venda_paga_registra_cliente_e_pagamento(self):
        venda = registrar_venda(
            produto_id=self.produto.id,
            quantidade=1,
            funcionario=self.funcionario,
            nome_cliente="Cliente Teste",
            forma_pagamento="pix",
            situacao_pagamento="pago"
        )

        self.assertEqual(
            venda.nome_cliente,
            "Cliente Teste"
        )
        self.assertEqual(
            venda.forma_pagamento,
            "pix"
        )
        self.assertEqual(
            venda.situacao_pagamento,
            "pago"
        )
        self.assertIsNotNone(venda.data_pagamento)

    def test_venda_fiada_registra_pendencia(self):
        venda = registrar_venda(
            produto_id=self.produto.id,
            quantidade=1,
            funcionario=self.funcionario,
            nome_cliente="Cliente Fiado",
            forma_pagamento="",
            situacao_pagamento="fiado"
        )

        self.assertEqual(
            venda.situacao_pagamento,
            "fiado"
        )
        self.assertIsNone(venda.data_pagamento)

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 4)

    def test_fiado_sem_cliente_e_bloqueado(self):
        with self.assertRaises(ValidationError):
            registrar_venda(
                produto_id=self.produto.id,
                quantidade=1,
                funcionario=self.funcionario,
                nome_cliente="",
                forma_pagamento="",
                situacao_pagamento="fiado"
            )

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 5)
        self.assertEqual(Venda.objects.count(), 0)

    def test_quitar_fiado_registra_pagamento(self):
        venda = registrar_venda(
            produto_id=self.produto.id,
            quantidade=1,
            funcionario=self.funcionario,
            nome_cliente="Cliente Fiado",
            forma_pagamento="",
            situacao_pagamento="fiado"
        )

        self.assertEqual(
            venda.situacao_pagamento,
            "fiado"
        )
        self.assertIsNone(venda.data_pagamento)

        quitar_fiado(
            venda_id=venda.id,
            forma_pagamento="pix",
            funcionario=self.funcionario
        )

        venda.refresh_from_db()

        self.assertEqual(
            venda.situacao_pagamento,
            "pago"
        )
        self.assertEqual(
            venda.forma_pagamento,
            "pix"
        )
        self.assertIsNotNone(venda.data_pagamento)

    def test_impedir_quitacao_duplicada(self):
        venda = registrar_venda(
            produto_id=self.produto.id,
            quantidade=1,
            funcionario=self.funcionario,
            nome_cliente="Cliente Fiado",
            situacao_pagamento="fiado"
        )

        quitar_fiado(
            venda_id=venda.id,
            forma_pagamento="dinheiro",
            funcionario=self.funcionario
        )

        with self.assertRaises(ValidationError):
            quitar_fiado(
                venda_id=venda.id,
                forma_pagamento="pix",
                funcionario=self.funcionario
            )

        venda.refresh_from_db()

        self.assertEqual(
            venda.situacao_pagamento,
            "pago"
        )
        self.assertEqual(
            venda.forma_pagamento,
            "dinheiro"
        )
        self.assertEqual(Venda.objects.count(), 1)

    def test_quitar_fiado_nao_altera_estoque(self):
        venda = registrar_venda(
            produto_id=self.produto.id,
            quantidade=1,
            funcionario=self.funcionario,
            nome_cliente="Cliente Fiado",
            situacao_pagamento="fiado"
        )

        self.produto.refresh_from_db()
        estoque_apos_venda = self.produto.quantidade

        self.assertEqual(estoque_apos_venda, 4)

        quitar_fiado(
            venda_id=venda.id,
            forma_pagamento="pix",
            funcionario=self.funcionario
        )

        self.produto.refresh_from_db()

        self.assertEqual(
            self.produto.quantidade,
            estoque_apos_venda
        )
        self.assertEqual(Venda.objects.count(), 1)


# ==========================================================
# NOVOS TESTES: CONTROLE DE ESTOQUE
# ==========================================================

class EstoqueTestCase(TestCase):

    def setUp(self):
        User = get_user_model()

        self.funcionario = User.objects.create_user(
            username="estoquista_teste",
            password="SenhaTeste123!",
            is_staff=True
        )

        self.cliente = User.objects.create_user(
            username="usuario_comum_teste",
            password="SenhaTeste123!"
        )

        self.produto = Produto.objects.create(
            nome="Corrente 8 velocidades",
            categoria="peca",
            preco=Decimal("45.00"),
            quantidade=10,
            estoque_minimo=3
        )

    def test_entrada_aumenta_estoque(self):
        registrar_entrada_estoque(
            self.produto.id, 5, self.funcionario
        )

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 15)

    def test_entrada_cria_movimentacao(self):
        movimentacao = registrar_entrada_estoque(
            self.produto.id,
            3,
            self.funcionario,
            motivo='compra',
            observacao='Reposição do fornecedor'
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 1
        )
        self.assertEqual(movimentacao.tipo, 'entrada')
        self.assertEqual(movimentacao.motivo, 'compra')
        self.assertEqual(movimentacao.quantidade, 3)
        self.assertEqual(
            movimentacao.funcionario,
            self.funcionario
        )
        self.assertEqual(
            movimentacao.observacao,
            'Reposição do fornecedor'
        )

    def test_saida_diminui_estoque(self):
        registrar_saida_estoque(
            self.produto.id,
            4,
            self.funcionario,
            motivo='dano'
        )

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 6)

    def test_saida_cria_movimentacao(self):
        movimentacao = registrar_saida_estoque(
            self.produto.id,
            2,
            self.funcionario,
            motivo='perda'
        )

        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 1
        )
        self.assertEqual(movimentacao.tipo, 'saida')
        self.assertEqual(movimentacao.motivo, 'perda')
        self.assertEqual(movimentacao.quantidade, 2)

    def test_impedir_saida_sem_estoque(self):
        with self.assertRaises(ValidationError):
            registrar_saida_estoque(
                self.produto.id,
                20,
                self.funcionario,
                motivo='perda'
            )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 10)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 0
        )

    def test_impedir_quantidade_zero_na_entrada(self):
        with self.assertRaises(ValidationError):
            registrar_entrada_estoque(
                self.produto.id,
                0,
                self.funcionario
            )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 10)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 0
        )

    def test_impedir_quantidade_negativa_na_saida(self):
        with self.assertRaises(ValidationError):
            registrar_saida_estoque(
                self.produto.id,
                -2,
                self.funcionario
            )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 10)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 0
        )

    def test_impedir_movimentacao_nao_autorizada(self):
        with self.assertRaises(ValidationError):
            registrar_entrada_estoque(
                self.produto.id,
                5,
                self.cliente
            )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 10)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 0
        )

    def test_impedir_motivo_invalido(self):
        with self.assertRaises(ValidationError):
            registrar_saida_estoque(
                self.produto.id,
                2,
                self.funcionario,
                motivo='venda'
            )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 10)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 0
        )

    def test_venda_registra_saida_uma_unica_vez(self):
        venda = registrar_venda(
            self.produto.id,
            3,
            self.funcionario
        )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 7)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 1
        )

        movimentacao = MovimentacaoEstoque.objects.get(
            venda=venda
        )

        self.assertEqual(movimentacao.tipo, 'saida')
        self.assertEqual(movimentacao.motivo, 'venda')
        self.assertEqual(movimentacao.quantidade, 3)

    def test_fiado_registra_saida_e_quitacao_nao_duplica(self):
        venda = registrar_venda(
            produto_id=self.produto.id,
            quantidade=2,
            funcionario=self.funcionario,
            nome_cliente='Cliente Fiado',
            situacao_pagamento='fiado'
        )

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 8)

        quitar_fiado(
            venda_id=venda.id,
            forma_pagamento='pix',
            funcionario=self.funcionario
        )

        self.produto.refresh_from_db()

        self.assertEqual(self.produto.quantidade, 8)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 1
        )
        self.assertEqual(
            MovimentacaoEstoque.objects.get(
                venda=venda
            ).quantidade,
            2
        )

    def test_movimentacoes_somam_corretamente(self):
        registrar_entrada_estoque(
            self.produto.id,
            5,
            self.funcionario
        )

        registrar_saida_estoque(
            self.produto.id,
            3,
            self.funcionario,
            motivo='dano'
        )

        registrar_venda(
            self.produto.id,
            2,
            self.funcionario
        )

        self.produto.refresh_from_db()

        # Estoque inicial: 10
        # Entrada: +5
        # Saída por dano: -3
        # Venda: -2
        # Estoque final: 10

        self.assertEqual(self.produto.quantidade, 10)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(), 3
        )


# ==========================================================
# TESTES DE SEGURANÇA: PERMISSÕES ADMINISTRATIVAS
# ==========================================================

class PermissoesAdministrativasTestCase(TestCase):

    def setUp(self):
        User = get_user_model()

        self.funcionario = User.objects.create_user(
            username="funcionario_permissoes",
            password="SenhaTeste123!",
            is_staff=True
        )

        self.cliente = User.objects.create_user(
            username="cliente_permissoes",
            password="SenhaTeste123!",
            is_staff=False
        )

        self.rotas_administrativas = [
            "dashboard",
            "produtos",
            "novo_produto",
            "vendas",
            "historico_vendas",
            "controle_estoque",
        ]

    def test_visitante_sem_login_e_redirecionado(self):
        for nome_rota in self.rotas_administrativas:
            with self.subTest(rota=nome_rota):
                resposta = self.client.get(reverse(nome_rota))

                self.assertEqual(resposta.status_code, 302)
                self.assertIn(
                    "/login/",
                    resposta.url
                )

    def test_cliente_comum_nao_acessa_area_administrativa(self):
        self.client.force_login(self.cliente)

        for nome_rota in self.rotas_administrativas:
            with self.subTest(rota=nome_rota):
                resposta = self.client.get(reverse(nome_rota))

                self.assertNotEqual(resposta.status_code, 200)

    def test_funcionario_acessa_area_administrativa(self):
        self.client.force_login(self.funcionario)

        for nome_rota in self.rotas_administrativas:
            with self.subTest(rota=nome_rota):
                resposta = self.client.get(reverse(nome_rota))

                self.assertEqual(resposta.status_code, 200)

    def test_cliente_nao_pode_cadastrar_produto(self):
        self.client.force_login(self.cliente)

        quantidade_antes = Produto.objects.count()

        resposta = self.client.post(
            reverse("novo_produto"),
            {
                "nome": "Produto não autorizado",
                "categoria": "peca",
                "preco": "50.00",
                "quantidade": 10,
                "estoque_minimo": 2,
            }
        )

        self.assertNotEqual(resposta.status_code, 200)
        self.assertEqual(
            Produto.objects.count(),
            quantidade_antes
        )

    def test_cliente_nao_pode_movimentar_estoque(self):
        produto = Produto.objects.create(
            nome="Produto protegido",
            categoria="peca",
            preco=Decimal("50.00"),
            quantidade=10,
            estoque_minimo=2
        )

        self.client.force_login(self.cliente)

        resposta = self.client.post(
            reverse("controle_estoque"),
            {
                "produto": produto.id,
                "tipo": "saida",
                "quantidade": 3,
                "motivo": "dano",
            }
        )

        produto.refresh_from_db()

        self.assertNotEqual(resposta.status_code, 200)
        self.assertEqual(produto.quantidade, 10)
        self.assertEqual(
            MovimentacaoEstoque.objects.count(),
            0
        )
