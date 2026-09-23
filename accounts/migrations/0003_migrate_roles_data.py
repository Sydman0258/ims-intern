from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    # "Mall" role is now "Mall Manager".
    User.objects.filter(role="mall").update(role="mall_manager")

    # Customers no longer log in. Their Customer records (name/phone/purchases)
    # are untouched - customer.0003 already removed the link to the user - so
    # only the now-useless login accounts are removed. Staff/superusers are
    # never deleted; they just become admins.
    User.objects.filter(role="customer", is_staff=False, is_superuser=False).delete()
    User.objects.filter(role="customer").update(role="admin")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_role"),
        # Must run after the Customer -> User link is gone, otherwise deleting
        # customer users would cascade into their purchase history.
        ("customer", "0003_remove_customer_user_phone_required"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
