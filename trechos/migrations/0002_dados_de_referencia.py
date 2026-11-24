"""Obstáculos e bairros de Maceió (spec 0003).

RunPython, e não fixture, para que os dados existam também no banco de testes.
"""

from django.db import migrations

OBSTACULOS = [
    ("degrau", "Degrau ou desnível"),
    ("buraco", "Buraco"),
    ("poste-placa", "Poste ou placa"),
    ("lixeira", "Lixeira"),
    ("mesa-cadeira", "Mesa ou cadeira"),
    ("veiculo", "Veículo estacionado"),
    ("rampa-ausente", "Rampa ausente"),
    ("inclinacao", "Calçada inclinada"),
    ("piso-irregular", "Piso irregular"),
    ("obra", "Obra"),
    ("sem-calcada", "Ausência de calçada"),
    ("outro", "Outro"),
]

BAIRROS = [
    "Antares", "Barro Duro", "Bebedouro", "Benedito Bentes", "Bom Parto", "Canaã", "Centro",
    "Chã da Jaqueira", "Chã de Bebedouro", "Cidade Universitária", "Clima Bom", "Cruz das Almas",
    "Farol", "Feitosa", "Fernão Velho", "Garça Torta", "Gruta de Lourdes", "Guaxuma", "Ipioca",
    "Jacarecica", "Jacintinho", "Jaraguá", "Jardim Petrópolis", "Jatiúca", "Levada", "Mangabeiras",
    "Mutange", "Ouro Preto", "Pajuçara", "Pescaria", "Petrópolis", "Pinheiro", "Pitanguinha", "Poço",
    "Ponta da Terra", "Ponta Grossa", "Ponta Verde", "Pontal da Barra", "Prado", "Riacho Doce",
    "Santa Amélia", "Santa Lúcia", "Santo Amaro", "Santos Dumont", "São Jorge", "Serraria",
    "Tabuleiro do Martins", "Trapiche da Barra", "Vergel do Lago",
]  # fmt: skip


def criar(apps, schema_editor):
    Obstaculo = apps.get_model("trechos", "Obstaculo")
    Bairro = apps.get_model("trechos", "Bairro")
    Obstaculo.objects.bulk_create([Obstaculo(codigo=codigo, nome=nome) for codigo, nome in OBSTACULOS])
    Bairro.objects.bulk_create([Bairro(nome=nome) for nome in BAIRROS])


def remover(apps, schema_editor):
    Obstaculo = apps.get_model("trechos", "Obstaculo")
    Bairro = apps.get_model("trechos", "Bairro")
    Obstaculo.objects.filter(codigo__in=[codigo for codigo, _ in OBSTACULOS]).delete()
    Bairro.objects.filter(nome__in=BAIRROS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("trechos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(criar, reverse_code=remover),
    ]
