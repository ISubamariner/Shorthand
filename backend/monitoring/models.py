from django.db import models


class SystemSnapshot(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    cpu_percent = models.FloatField()
    memory_percent = models.FloatField()
    memory_used_mb = models.FloatField()
    memory_total_mb = models.FloatField()
    disk_percent = models.FloatField()
    disk_used_gb = models.FloatField()
    disk_total_gb = models.FloatField()
    process_uptime_seconds = models.FloatField()
    db_size_mb = models.FloatField()
    db_connections = models.IntegerField()
    table_stats = models.JSONField(default=list)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Snapshot {self.timestamp:%Y-%m-%d %H:%M}"
