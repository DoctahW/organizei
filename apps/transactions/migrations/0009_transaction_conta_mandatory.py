import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0008_create_subscription_category'),
        ('bank_accounts', '0002_conta_add_user_agency_nickname'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DELETE FROM transactions_transaction WHERE conta_id IS NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='conta',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='bank_accounts.conta',
                verbose_name='Conta Bancária',
            ),
        ),
    ]
