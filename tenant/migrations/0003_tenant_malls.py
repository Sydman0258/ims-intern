from django.db import migrations, models


def assign_tenants_to_malls_of_their_units(apps, schema_editor):
    """Existing retail units already tie a tenant to a mall - carry that over."""
    RetailUnit = apps.get_model("tenant", "RetailUnit")
    for unit in RetailUnit.objects.select_related("tenant", "mall"):
        unit.tenant.malls.add(unit.mall)


class Migration(migrations.Migration):

    dependencies = [
        ("mall", "0003_mall_user_email_phone"),
        ("tenant", "0002_tenant_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="malls",
            field=models.ManyToManyField(
                blank=True, related_name="tenants", to="mall.mall"
            ),
        ),
        migrations.RunPython(
            assign_tenants_to_malls_of_their_units, migrations.RunPython.noop
        ),
    ]
