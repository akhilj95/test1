from rest_framework.routers import DefaultRouter
from missions.views import (
    RoverHardwareViewSet, SensorViewSet, CalibrationViewSet, MissionViewSet,
    SensorDeploymentViewSet, LogFileViewSet, NavSampleViewSet,
    ImuSampleViewSet, CompassSampleViewSet, PressureSampleViewSet,
)
from missions.views import MediaAssetViewSet, FrameIndexViewSet

router = DefaultRouter()
router.register(r"rovers", RoverHardwareViewSet)
router.register(r"sensors", SensorViewSet)
router.register(r"calibrations", CalibrationViewSet)
router.register(r"missions", MissionViewSet)
router.register(r"deployments", SensorDeploymentViewSet)
router.register(r"logfiles", LogFileViewSet)
router.register(r"navsamples", NavSampleViewSet)
router.register(r"imusamples", ImuSampleViewSet)
router.register(r"compasssamples", CompassSampleViewSet)
router.register(r"pressuresamples", PressureSampleViewSet)
router.register(r'media-assets', MediaAssetViewSet)
router.register(r'frame-indices', FrameIndexViewSet)

urlpatterns = router.urls