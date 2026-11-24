from decimal import Decimal

from django.test import SimpleTestCase

from comum.geo import distancia_em_metros


class DistanciaEmMetrosTests(SimpleTestCase):
    def test_mesmo_ponto_retorna_zero(self):
        distancia = distancia_em_metros(-9.6658, -35.7353, -9.6658, -35.7353)

        self.assertEqual(distancia, 0)

    def test_um_grau_de_latitude_mede_cerca_de_111_km(self):
        distancia = distancia_em_metros(0, 0, 1, 0)

        self.assertAlmostEqual(distancia, 111_195, delta=100)

    def test_aceita_decimal(self):
        distancia = distancia_em_metros(Decimal("0"), Decimal("0"), Decimal("1"), Decimal("0"))

        self.assertAlmostEqual(distancia, 111_195, delta=100)
