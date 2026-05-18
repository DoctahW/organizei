from decimal import Decimal

from django.db import migrations


def forwards(apps, schema_editor):
    Investment = apps.get_model("investments", "Investment")
    Movimentacao = apps.get_model("investments", "InvestmentMovimentacao")

    for inv in Investment.objects.all():
        if Movimentacao.objects.filter(investment=inv).exists():
            continue

        qtd = inv.quantidade or Decimal("0")
        valor_aplicado = inv.valor_aplicado or Decimal("0")
        valor_atual = inv.valor_atual or valor_aplicado

        pu_compra = None
        if qtd > 0:
            pu_compra = (valor_aplicado / qtd).quantize(Decimal("0.0001"))
            if inv.pu_atual is None and valor_atual > 0:
                inv.pu_atual = (valor_atual / qtd).quantize(Decimal("0.0001"))
                inv.save(update_fields=["pu_atual"])

        Movimentacao.objects.create(
            investment=inv,
            tipo="compra",
            data=inv.data_aplicacao,
            valor=valor_aplicado,
            quantidade=qtd,
            pu_na_data=pu_compra,
            observacao="Migração de dados — compra inicial",
        )


def backwards(apps, schema_editor):
    Movimentacao = apps.get_model("investments", "InvestmentMovimentacao")
    Movimentacao.objects.filter(observacao="Migração de dados — compra inicial").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("investments", "0004_investment_pu_atual_alter_investment_data_aplicacao_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
