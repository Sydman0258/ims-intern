from django.db import migrations, models


class Migration(migrations.Migration):
    """Customers no longer have login accounts; a phone number is required."""

    dependencies = [
        ("customer", "0002_customer_user"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customer",
            name="user",
        ),
        # Existing rows without a phone get an empty string instead of NULL.
        migrations.AlterField(
            model_name="customer",
            name="phone",
            field=models.CharField(default="", max_length=20),
            preserve_default=False,
        ),
    ]
