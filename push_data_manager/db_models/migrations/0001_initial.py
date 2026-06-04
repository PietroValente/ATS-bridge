from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SyncState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("ats_source", models.CharField(max_length=50, unique=True)),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                ("total_pushed", models.IntegerField(default=0)),
                ("total_skipped", models.IntegerField(default=0)),
            ],
        ),
    ]
