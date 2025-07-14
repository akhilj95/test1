from django.contrib import admin
from .models import RoverHardware, Sensor, Calibration, Mission, SensorDeployment, NavSample, LogFile
from .models import MediaAsset, FrameIndex, ImuSample, CompassSample, PressureSample

admin.site.register(RoverHardware)
admin.site.register(Sensor)
admin.site.register(Calibration)
admin.site.register(Mission)
admin.site.register(SensorDeployment)
admin.site.register(NavSample)
admin.site.register(LogFile)
admin.site.register(MediaAsset)
admin.site.register(FrameIndex)
admin.site.register(ImuSample)
admin.site.register(CompassSample)
admin.site.register(PressureSample)