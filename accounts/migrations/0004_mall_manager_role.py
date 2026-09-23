from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_migrate_roles_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Admin"),
                    ("tenant", "Tenant"),
                    ("mall_manager", "Mall Manager"),
                ],
                default="tenant",
                max_length=20,
            ),
        ),
        migrations.DeleteModel(
            name="Customer",
        ),
        migrations.RenameModel(
            old_name="Mall",
            new_name="MallManager",
        ),
    ]
