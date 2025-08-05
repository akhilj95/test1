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
from missions.filters import MissionFilter

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# DJANGO REST FRAMEWORK DEFAULT SETTINGS ARE SET IN core/settings.py
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ------------------------------------------------------------------
# Rover Hardware
# ------------------------------------------------------------------
class RoverHardwareViewSet(viewsets.ModelViewSet):
    queryset = RoverHardware.objects.all()
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
    search_fields = ["description", "location"]
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
    filterset_fields = ["mission", "depth_m"]
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
    ).all()
    serializer_class = MediaAssetSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['media_type', 'deployment__mission__location']
    search_fields = ['file_path', 'deployment__mission__location']
    ordering_fields = ['start_time']
    
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """
        Get all media assets from a specific location across missions.
        Supports filtering by depth and yaw from associated nav samples.
        """
        location = request.query_params.get('location')
        depth_min = request.query_params.get('depth_min')
        depth_max = request.query_params.get('depth_max')
        yaw_min = request.query_params.get('yaw_min')
        yaw_max = request.query_params.get('yaw_max')
        
        if not location:
            return Response({'error': 'location parameter is required'}, status=400)
        
        # Start with media assets from the specified location
        queryset = self.queryset.filter(deployment__mission__location=location)
        
        # Apply nav sample filtering if provided
        if any([depth_min, depth_max, yaw_min, yaw_max]):
            frame_filters = Q()
            
            if depth_min is not None:
                frame_filters &= Q(frames__closest_nav_sample__depth_m__gte=float(depth_min))
            if depth_max is not None:
                frame_filters &= Q(frames__closest_nav_sample__depth_m__lte=float(depth_max))
            if yaw_min is not None:
                frame_filters &= Q(frames__closest_nav_sample__yaw_deg__gte=float(yaw_min))
            if yaw_max is not None:
                frame_filters &= Q(frames__closest_nav_sample__yaw_deg__lte=float(yaw_max))
            
            queryset = queryset.filter(frame_filters).distinct()
        
        # Paginate the results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
        'media_asset', 'closest_nav_sample__depth_m', 'closest_nav_sample__yaw_deg'
    ]
    ordering_fields = ['timestamp', 'frame_number']
