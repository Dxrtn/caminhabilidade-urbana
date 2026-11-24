"""View vw_trechos_mapa, lida pelo model trechos.TrechoMapa (managed = False).

Fica em feedbacks porque depende da tabela feedback, além de trecho e bairro.
"""

from django.db import migrations

CRIAR = """
CREATE OR REPLACE VIEW vw_trechos_mapa AS
SELECT
    t.id,
    t.logradouro,
    b.id   AS bairro_id,
    b.nome AS bairro,
    t.referencia_inicio,
    t.referencia_fim,
    t.lado,
    t.lat_inicio, t.lng_inicio, t.lat_fim, t.lng_fim,
    t.classificacao,
    t.atualizado_em,
    (CURRENT_DATE - t.atualizado_em::date) AS dias_sem_atualizacao,
    COUNT(f.id) FILTER (WHERE f.status = 'EM_ANALISE') AS feedbacks_em_analise
FROM trecho t
JOIN bairro b ON b.id = t.bairro_id
LEFT JOIN feedback f ON f.trecho_id = t.id
WHERE t.ativo
GROUP BY t.id, b.id;
"""

REMOVER = "DROP VIEW IF EXISTS vw_trechos_mapa;"


class Migration(migrations.Migration):
    dependencies = [
        ("trechos", "0001_initial"),  # tabelas trecho e bairro
        ("feedbacks", "0001_initial"),  # tabela feedback
    ]

    operations = [
        migrations.RunSQL(sql=CRIAR, reverse_sql=REMOVER),
    ]
