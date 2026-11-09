
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Produto, Venda
from .services import registrar_venda, quitar_fiado


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

        self.assertEqual(venda.preco_unitario, Decimal("1000.00"))
        self.assertEqual(venda.total, Decimal("2000.00"))

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

        self.assertEqual(venda.nome_cliente, "Cliente Teste")
        self.assertEqual(venda.forma_pagamento, "pix")
        self.assertEqual(venda.situacao_pagamento, "pago")
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

        self.assertEqual(venda.situacao_pagamento, "fiado")
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

        self.assertEqual(venda.situacao_pagamento, "fiado")
        self.assertIsNone(venda.data_pagamento)

        quitar_fiado(
            venda_id=venda.id,
            forma_pagamento="pix",
            funcionario=self.funcionario
        )

        venda.refresh_from_db()

        self.assertEqual(venda.situacao_pagamento, "pago")
        self.assertEqual(venda.forma_pagamento, "pix")
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

        self.assertEqual(venda.situacao_pagamento, "pago")
        self.assertEqual(venda.forma_pagamento, "dinheiro")
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


