from django.db import models
from django.contrib.auth.models import User


class CrimeData(models.Model):
    SEVERITY_CHOICES = (
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low')
    )

    # PNP data structure fields
    city = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100)
    date_committed = models.DateField()
    time_committed = models.TimeField(null=True, blank=True)
    offense = models.CharField(max_length=500)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Derived fields for analysis
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, null=True, blank=True)
    cluster = models.PositiveIntegerField(null=True, blank=True)  # For K-means clustering

    def __str__(self):
        return f"{self.offense} in {self.city}, {self.barangay} on {self.date_committed.strftime('%m/%d/%Y')}"


class UserActivity(models.Model):
    ACTION_CHOICES = (
        ('upload', 'Data Upload'),
        ('edit', 'Data Edit'),
        ('delete', 'Data Delete'),
        ('user', 'User Management'),
        ('login', 'User Login'),
        ('other', 'Other Action')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255)
    records_affected = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "User Activities"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"