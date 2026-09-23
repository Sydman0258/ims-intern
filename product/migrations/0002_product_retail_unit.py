# Product belongs to retail store, not tenant

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0001_initial"),
        ("tenant", "0003_tenant_malls"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="retail_unit",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="tenant.retailunit",
            ),
        ),
        migrations.RemoveField(
            model_name="product",
            name="shop",
        ),
    ]
