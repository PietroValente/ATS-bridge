from django.db import models


class SyncState(models.Model):
    ats_source = models.CharField(max_length=50, unique=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    total_pushed = models.IntegerField(default=0)
    total_skipped = models.IntegerField(default=0)

    class Meta:
        app_label = "db_models"
