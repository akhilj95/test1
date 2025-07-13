from django.contrib import admin
from .models import RoverHardware, Sensor, Calibration, Mission, SensorDeployment, NavSample, LogFile


admin.site.register(RoverHardware)
admin.site.register(Sensor)
admin.site.register(Calibration)
admin.site.register(Mission)
admin.site.register(SensorDeployment)
admin.site.register(NavSample)
admin.site.register(LogFile)