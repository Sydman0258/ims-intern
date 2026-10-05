# Generated manually — change CASCADE to PROTECT on sales FKs so history is preserved.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("customer", "0004_offline_purchase_retail_unit"),
        ("product", "0002_product_retail_unit"),
        ("tenant", "0005_alter_retailunit_leased_tenure_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customerpurchase",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="purchases",
                to="tenant.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="customerpurchase",
            name="retail_unit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="purchases",
                to="tenant.retailunit",
            ),
        ),
        migrations.AlterField(
            model_name="customerpurchaseitem",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="purchase_items",
                to="product.product",
            ),
        ),
    ]
