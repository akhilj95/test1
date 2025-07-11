from django.db import models
from django.utils import timezone
from django.db import transaction


# --- 1. Hardware options
class Rover(models.Model):
    name            = models.CharField(max_length=100)
    serial_number   = models.CharField(max_length=10, unique=True)
    hardware_config = models.JSONField(blank=True, default=dict)

    def __str__(self):
        return f"{self.name} ({self.serial_number})"
    
class Sensor(models.Model):
    """
    Represents a sensor that can be deployed on a rover.
    Each sensor has a type, name, and optional specification.
    """
    class SensorType(models.TextChoices):
        CAMERA = "camera", "Camera"
        COMPASS = "compass", "Compass"
        IMU = "imu", "IMU"
        PRESSURE = "pressure", "Pressure"
        SONAR = "sonar", "Sonar"

    sensor_type     = models.CharField(max_length=20, choices=SensorType.choices)
    name            = models.CharField(max_length=100)
    specification   = models.JSONField(blank=True, default=dict)

    def __str__(self):
        return self.name

class Calibration(models.Model):
    sensor          = models.ForeignKey(
        "Sensor",
        on_delete=models.CASCADE,
        related_name="calibrations"
    )
    effective_from  = models.DateTimeField(default=timezone.now)
    coefficients    = models.JSONField(blank=True, default=dict)
    active          = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sensor"],
                condition=models.Q(active=True),
                name="one_active_calibration_per_sensor",
            )
        ]

    def save(self, *args, **kwargs):
        # Wrap in a transaction so “unset olds” + “save new” is atomic
        with transaction.atomic():
            if self.active:
                (Calibration.objects
                   .filter(sensor=self.sensor, active=True)
                   .exclude(pk=self.pk)           # skip self on update
                   .update(active=False))
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sensor} since {self.effective_from:%Y-%m-%d}"


# --- 2.  Missions and sensor setup

class Mission(models.Model):
    class TargetType(models.TextChoices):
        PILLAR = "pillar", "Pillar"
        WALL   = "wall",   "Wall"

    rover        = models.ForeignKey(
        Rover, on_delete=models.PROTECT, related_name="missions"
    )
    start_time   = models.DateTimeField(default=timezone.now)
    end_time     = models.DateTimeField(null=True, blank=True)
    location     = models.CharField(max_length=255, blank=True)
    target_type  = models.CharField(
        max_length=12,                     # safety margin of 6
        choices=TargetType.choices,
        default=TargetType.WALL,
    )    
    max_depth    = models.FloatField(null=True, blank=True)
    description  = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["start_time"])]

class SensorDeployment(models.Model):
    mission     = models.ForeignKey(Mission, on_delete=models.CASCADE,
                                    related_name="deployments")
    sensor      = models.ForeignKey(Sensor, on_delete=models.PROTECT,
                                    related_name="deployments")
    calibration = models.ForeignKey(Calibration, on_delete=models.PROTECT,
                                    null=True, blank=True)
    position    = models.CharField(max_length=50)   # e.g. “bow-port”

# --- 3.  Time-series data --------------------------------------------------
# # common base (abstract; no DB table)
# class BaseReading(models.Model):
#     deployment = models.ForeignKey("SensorDeployment",
#                                    on_delete=models.CASCADE,
#                                    related_name="%(class)s")
#     timestamp  = models.DateTimeField()

#     class Meta:
#         abstract = True
#         indexes  = [
#             models.Index(fields=["deployment", "timestamp"]),
#         ]


# class TemperatureReading(BaseReading):
#     value = models.FloatField()


# class ImuReading(BaseReading):
#     x = models.FloatField()
#     y = models.FloatField()
#     z = models.FloatField()


# class CameraFrame(BaseReading):
#     file = models.FileField(upload_to=media_upload_to)
#     exposure_ms = models.PositiveIntegerField()