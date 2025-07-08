from django.contrib import admin
from .models import Rover, Sensor, Calibration, Mission, SensorDeployment


admin.site.register(Rover)
admin.site.register(Sensor)
admin.site.register(Calibration)
admin.site.register(Mission)
admin.site.register(SensorDeployment)