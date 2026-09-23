from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("customer", "0003_remove_customer_user_phone_required"),
        ("tenant", "0003_tenant_malls"),
    ]

    operations = [
        migrations.AddField(
            model_name="customerpurchase",
            name="retail_unit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="purchases",
                to="tenant.retailunit",
            ),
        ),
        migrations.AddField(
            model_name="customerpurchase",
            name="is_offline",
            field=models.BooleanField(
                default=True,
                help_text="True for in-store sales recorded by tenant (no online buying).",
            ),
        ),
    ]
