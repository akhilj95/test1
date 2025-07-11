from django.db import models
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

#  ------------------------------------------------------------------
#  1. Hardware options
#  ------------------------------------------------------------------

class RoverHardware(models.Model):
    """
    Represents the hardware configuration versioning for a rover
    Only one active configuration per rover name is allowed at a time.
    """
    name            = models.CharField(max_length=100)
    
    # versioning / config
    effective_from = models.DateTimeField(default=timezone.now)
    hardware_config  = models.JSONField(default=dict, blank=True)
    active         = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(active=True),
                name="unique_active_roverhardware_per_name",
            )
        ]
        ordering = ["-effective_from"]

    def save(self, *args, **kwargs):
        # Ensure that, per rover `name`, only one row remains `active=True`.
        with transaction.atomic():
            # Wrap in a transaction so “unset olds” + “save new” is atomic
            if self.active:
                (RoverHardware.objects
                    .filter(name=self.name, active=True)
                    .exclude(pk=self.pk)                  # skip self on update
                    .update(active=False))
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.effective_from:%Y-%m-%d})"
    

#  ------------------------------------------------------------------
#  2. Sensors and calibrations
#  ------------------------------------------------------------------
    
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
    name            = models.CharField(max_length=100, unique=True)
    specification   = models.JSONField(blank=True, default=dict)

    def __str__(self):
        return self.name


class Calibration(models.Model):
    """
    Optional per-sensor (not per-mission) calibration history.
    Each sensor has calibration coefficients in JSON format.
    Only one calibration can be active at a time for a sensor.
    """
    sensor          = models.ForeignKey(
        "Sensor",
        on_delete=models.PROTECT,
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
            ),
        ]
        ordering = ["-effective_from"]

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


#  ------------------------------------------------------------------
#  3. Mission and mission specific deployments
#  ------------------------------------------------------------------

class Mission(models.Model):
    """
    Represents a misiion that inspects a single target.
    """
    class TargetType(models.TextChoices):
        PILLAR = "pillar", "Pillar"
        WALL   = "wall",   "Wall"

    rover        = models.ForeignKey(
        RoverHardware, on_delete=models.PROTECT, related_name="missions"
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

    def clean(self):
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")
    
    class Meta:
        indexes = [models.Index(fields=["start_time"])]
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.rover.name} @ {self.start_time:%Y-%m-%d}"

class SensorDeployment(models.Model):
    """
    Represents the specific deployment characteristics of a sensor on
    a specific mission.
    """
    mission     = models.ForeignKey(Mission, on_delete=models.CASCADE,
                                    related_name="deployments")
    sensor      = models.ForeignKey(Sensor, on_delete=models.PROTECT,
                                    related_name="deployments")
    calibration = models.ForeignKey(Calibration, on_delete=models.PROTECT,
                                    null=True, blank=True)
    position    = models.CharField(max_length=50)   # e.g. “bow-port”

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(calibration__isnull=True) |
                    models.Q(calibration__sensor=models.F("sensor"))
                ),
                name="calibration_matches_deployed_sensor",
            )
        ]
        indexes = [
            models.Index(fields=["mission"]),
            models.Index(fields=["sensor"]),
        ]
    
    def __str__(self):
        return f"{self.sensor} on {self.mission} ({self.position})"

#  ------------------------------------------------------------------
#  4. Da
#  ------------------------------------------------------------------

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