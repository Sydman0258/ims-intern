from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tenant", "0003_tenant_malls"),
    ]

    operations = [
        migrations.AddField(
            model_name="retailunit",
            name="monthly_rent",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True
            ),
        ),
        migrations.CreateModel(
            name="LeasePayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("paid_on", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("overdue", "Overdue"),
                            ("waived", "Waived"),
                        ],
                        default="pending",
                        max_length=30,
                    ),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "retail_unit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lease_payments",
                        to="tenant.retailunit",
                    ),
                ),
            ],
            options={"ordering": ["-period_end", "-created_at"]},
        ),
    ]
