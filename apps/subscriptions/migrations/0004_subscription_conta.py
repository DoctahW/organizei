import django.db.models.deletion
from django.db import migrations, models


def assign_default_conta(apps, schema_editor):
    Subscription = apps.get_model('subscriptions', 'Subscription')
    Conta = apps.get_model('bank_accounts', 'Conta')
    for sub in Subscription.objects.filter(conta__isnull=True):
        conta = Conta.objects.filter(usuario=sub.user).first()
        if conta:
            sub.conta = conta
            sub.save()
        else:
            sub.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_subscription_end_date'),
        ('bank_accounts', '0002_conta_add_user_agency_nickname'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='conta',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='bank_accounts.conta',
                verbose_name='Conta Bancária',
            ),
        ),
        migrations.RunPython(assign_default_conta),
        migrations.AlterField(
            model_name='subscription',
            name='conta',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='bank_accounts.conta',
                verbose_name='Conta Bancária',
            ),
        ),
    ]
