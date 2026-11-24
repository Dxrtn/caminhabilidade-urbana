"""Trigger trg_trecho_historico: grava historico_trecho a cada mudança de classificação.

Depende de trechos/0001, que cria as tabelas trecho e historico_trecho. As colunas
do INSERT são as do model HistoricoTrecho.
"""

from django.db import migrations

CRIAR = """
CREATE OR REPLACE FUNCTION fn_registrar_historico_trecho()
RETURNS trigger AS $$
BEGIN
    -- Em uma alteração, só registra se a classificação realmente mudou.
    IF TG_OP = 'UPDATE' AND NEW.classificacao IS NOT DISTINCT FROM OLD.classificacao THEN
        RETURN NEW;
    END IF;

    INSERT INTO historico_trecho (trecho_id, classificacao_anterior, classificacao_nova, alterado_por_id, alterado_em)
    VALUES (
        NEW.id,
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.classificacao ELSE NULL END,
        NEW.classificacao,
        NEW.atualizado_por_id,
        now()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_trecho_historico
AFTER INSERT OR UPDATE OF classificacao ON trecho
FOR EACH ROW
EXECUTE FUNCTION fn_registrar_historico_trecho();
"""

REMOVER = """
DROP TRIGGER IF EXISTS trg_trecho_historico ON trecho;
DROP FUNCTION IF EXISTS fn_registrar_historico_trecho();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("trechos", "0001_initial"),
        ("trechos", "0002_dados_de_referencia"),
    ]

    operations = [
        migrations.RunSQL(sql=CRIAR, reverse_sql=REMOVER),
    ]
