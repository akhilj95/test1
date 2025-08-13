from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from missions.models import (
    RoverHardware, Sensor, Calibration, Mission,
    SensorDeployment, LogFile, NavSample,
    ImuSample, CompassSample, PressureSample,
    MediaAsset, FrameIndex,
)
from missions.serializers import (
    RoverHardwareSerializer, SensorSerializer, CalibrationSerializer, MissionSerializer,
    SensorDeploymentSerializer, LogFileSerializer, NavSampleSerializer,
    ImuSampleSerializer, CompassSampleSerializer, PressureSampleSerializer,
    MediaAssetSerializer, FrameIndexSerializer,
)
from missions.filters import MissionFilter, MediaAssetFilter

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# DJANGO REST FRAMEWORK DEFAULT SETTINGS ARE SET IN core/settings.py
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ------------------------------------------------------------------
# Rover Hardware
# ------------------------------------------------------------------
class RoverHardwareViewSet(viewsets.ModelViewSet):
    queryset = RoverHardware.objects.prefetch_related("missions").all()
    serializer_class = RoverHardwareSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["name"]
    ordering_fields = ["effective_from", "name"]

# ------------------------------------------------------------------
# Sensor
# ------------------------------------------------------------------
class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.prefetch_related("calibrations").all()
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["name", "sensor_type"]
    ordering_fields = ["name", "sensor_type"]

# ------------------------------------------------------------------
# Calibration
# ------------------------------------------------------------------
class CalibrationViewSet(viewsets.ModelViewSet):
    queryset = Calibration.objects.select_related("sensor").all()
    serializer_class = CalibrationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["sensor", "active"]
    ordering_fields = ["effective_from"]

# ------------------------------------------------------------------
# Mission
# ------------------------------------------------------------------
class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.select_related("rover").all()
    serializer_class = MissionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = MissionFilter
    search_fields = ["notes", "location"]
    ordering_fields = ["start_time", "max_depth"]

# ------------------------------------------------------------------
# Sensor Deployment
# ------------------------------------------------------------------
class SensorDeploymentViewSet(viewsets.ModelViewSet):
    queryset = SensorDeployment.objects.select_related("sensor", "mission").all()
    serializer_class = SensorDeploymentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["sensor", "mission"]
    ordering_fields = ["mission", "sensor"]

# ------------------------------------------------------------------
# Log File
# ------------------------------------------------------------------
class LogFileViewSet(viewsets.ModelViewSet):
    queryset = LogFile.objects.select_related("mission").all()
    serializer_class = LogFileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["mission"]
    ordering_fields = ["created_at"]

# ------------------------------------------------------------------
# Navigation Sample
# ------------------------------------------------------------------
class NavSampleViewSet(viewsets.ModelViewSet):
    queryset = NavSample.objects.select_related("mission").all()
    serializer_class = NavSampleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["mission", "depth_m", "timestamp"]
    ordering_fields = ["timestamp", "depth_m"]

# ------------------------------------------------------------------
# IMU Sample
# ------------------------------------------------------------------
class ImuSampleViewSet(viewsets.ModelViewSet):
    queryset = ImuSample.objects.select_related("deployment").all()
    serializer_class = ImuSampleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["deployment"]
    ordering_fields = ["timestamp"]

# ------------------------------------------------------------------
# Compass Sample
# ------------------------------------------------------------------
class CompassSampleViewSet(viewsets.ModelViewSet):
    queryset = CompassSample.objects.select_related("deployment").all()
    serializer_class = CompassSampleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["deployment"]
    ordering_fields = ["timestamp"]

# ------------------------------------------------------------------
# Pressure Sample
# ------------------------------------------------------------------
class PressureSampleViewSet(viewsets.ModelViewSet):
    queryset = PressureSample.objects.select_related("deployment").all()
    serializer_class = PressureSampleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["deployment"]
    ordering_fields = ["timestamp"]

# ------------------------------------------------------------------
# Media Asset
# ------------------------------------------------------------------
class MediaAssetViewSet(viewsets.ModelViewSet):
    queryset = MediaAsset.objects.select_related(
        'deployment__mission', 'deployment__sensor'
    ).prefetch_related('frames').all()
    serializer_class = MediaAssetSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = MediaAssetFilter
    search_fields = ['deployment__mission__location',]
    ordering_fields = ['start_time']

# ------------------------------------------------------------------
# Frame Index
# ------------------------------------------------------------------
class FrameIndexViewSet(viewsets.ModelViewSet):
    queryset = FrameIndex.objects.select_related(
        'media_asset', 'closest_nav_sample'
    ).all()
    serializer_class = FrameIndexSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = [
        'media_asset',
        'frame_number',
        'closest_nav_sample__depth_m',
        'closest_nav_sample__yaw_deg',
    ]
    ordering_fields = ['timestamp', 'frame_number']

