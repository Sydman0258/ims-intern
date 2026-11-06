from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone
from tablib import Dataset

from product.models import ImportJob, Product
from product.admin import ProductResource
from product.models import ExportJob
from tenant.filters import ProductFilter


@shared_task
def export_products_task(job_id):
    job = ExportJob.objects.get(id=job_id)

    try:
        job.status = "PROCESSING"
        job.save(update_fields=["status"])

        queryset = (
            Product.objects
            .filter(retail_unit__tenant=job.tenant)
            .select_related(
                "retail_unit",
                "category",
            )
            .prefetch_related("tags")
            .order_by("name")
        )

        product_filter = ProductFilter(
            data=job.filters,
            queryset=queryset,
        )

        queryset = product_filter.qs

        resource = ProductResource(tenant=job.tenant)
        dataset = resource.export(queryset)

        csv_content = dataset.csv

        filename = f"products_export_{job.id}.csv"

        job.file.save(
            filename,
            ContentFile(csv_content.encode("utf-8-sig")),
            save=False,
        )

        job.status = "COMPLETED"
        job.completed_at = timezone.now()
        job.save()

        return {
            "job_id": job.id,
            "status": job.status,
        }

    except Exception as exc:
        job.status = "FAILED"
        job.error_message = str(exc)
        job.save(
            update_fields=[
                "status",
                "error_message",
            ]
        )

        raise

@shared_task
def import_products_task(job_id):
    job = ImportJob.objects.get(id=job_id)

    try:
        job.status = "PROCESSING"
        job.save(update_fields=["status"])

        with job.file.open("rb") as csv_file:
            csv_content = csv_file.read().decode("utf-8-sig")

        dataset = Dataset()
        dataset.load(csv_content, format="csv")

        resource = ProductResource(tenant=job.tenant)

        preview = resource.import_data(
            dataset,
            dry_run=True,
            raise_errors=False,
            use_transactions=True,
        )

        if preview.has_errors() or preview.has_validation_errors():
            errors = []

        for row_number, errors_list in preview.row_errors():
            for error in errors_list:
                errors.append(
                    f"Row {row_number}: {error.error}"
        )

            if preview.has_validation_errors():
                errors.append("The CSV contains validation errors.")

            job.status = "FAILED"
            job.error_message = "\n".join(errors)[:10000]
            job.save(update_fields=["status", "error_message"])

            return {
                "job_id": job.id,
                "status": job.status,
                "errors": errors,
            }

        result = resource.import_data(
            dataset,
            dry_run=False,
            raise_errors=False,
            use_transactions=True,
        )

        if result.has_errors() or result.has_validation_errors():
            job.status = "FAILED"
            job.error_message = str(result.row_errors())[:10000]
        else:
            job.status = "COMPLETED"
            job.completed_at = timezone.now()

        job.save(
            update_fields=[
                "status",
                "error_message",
                "completed_at",
            ]
        )

        return {
            "job_id": job.id,
            "status": job.status,
        }

    except Exception as exc:
        job.status = "FAILED"
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message"])

        raise