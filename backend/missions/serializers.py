from rest_framework import serializers
from missions.models import (
    RoverHardware, Sensor, Calibration, Mission,
    SensorDeployment, LogFile, NavSample,
    ImuSample, CompassSample, PressureSample,
    MediaAsset, FrameIndex,
)

class RoverHardwareSerializer(serializers.ModelSerializer):
    effective_from_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RoverHardware
        fields = (
            "id",
            "name",
            "effective_from",
            "effective_from_display",
            "hardware_config",
            "active",
        )
        read_only_fields = ("id", "effective_from_display", "active")

    def get_effective_from_display(self, obj):
        # Preserve microseconds in ISO 8601
        if not obj.effective_from:
            return None
        return obj.effective_from.isoformat()


class CalibrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calibration
        fields = (
            "id",
            "effective_from",
            "coefficients",
            "active",
        )
        read_only_fields = ("id", "effective_from", "active")


class SensorSerializer(serializers.ModelSerializer):
    active_calibration = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Sensor
        fields = ("id", "name", "sensor_type", "specification", "active_calibration")
        read_only_fields = ("id", "active_calibration")

    def get_active_calibration(self, obj):
        active = getattr(obj, "_prefetched_objects_cache", {}).get("calibrations")
        if active is None:
            active = obj.calibrations.filter(active=True)
        calib = active.first()
        return CalibrationSerializer(calib).data if calib else None


class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = (
            "id",
            "rover",
            "start_time",
            "end_time",
            "location",
            "target_type",
            "max_depth",
            "visibility",
            "cloud_cover",
            "tide_level",
            "notes",
        )

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )
        return attrs

    def validate_max_depth(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Depth must be positive in metres.")
        return value


class SensorDeploymentSerializer(serializers.ModelSerializer):
    latest_coefficients = serializers.SerializerMethodField(read_only=True)
    sensor_name = serializers.CharField(source="sensor.name", read_only=True)
    instance = serializers.ChoiceField(choices=[(0, '0'), (1, '1')], default=0)

    class Meta:
        model = SensorDeployment
        fields = (
            "id",
            "mission",
            "sensor",
            "sensor_name",
            "position",
            "calibration",
            "latest_coefficients",
            "instance",
        )

    def get_latest_coefficients(self, obj):
        calib = obj.calibration or obj.sensor.calibrations.filter(active=True).first()
        return calib.coefficients if calib else None


class LogFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogFile
        fields = (
            "id",
            "mission",
            "bin_path",
            "tlog_path",
            "created_at",
            "notes",
        )

    def validate(self, attrs):
        bin_path = attrs.get("bin_path") or getattr(self.instance, "bin_path", None)
        tlog_path = attrs.get("tlog_path") or getattr(self.instance, "tlog_path", None)
        if not bin_path and not tlog_path:
            raise serializers.ValidationError(
                "At least one of bin_path or tlog_path must be provided."
            )
        return attrs

class NavSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavSample
        fields = ('id', 'mission', 'timestamp', 'depth_m', 'roll_deg', 'pitch_deg', 'yaw_deg')
        read_only_fields = ('id',)


class _BaseSampleSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "deployment", "timestamp")
        read_only_fields = ("id",)

class ImuSampleSerializer(_BaseSampleSerializer):
    class Meta(_BaseSampleSerializer.Meta):
        model = ImuSample
        fields = _BaseSampleSerializer.Meta.fields + (
            "gx_rad_s",
            "gy_rad_s",
            "gz_rad_s",
            "ax_m_s2",
            "ay_m_s2",
            "az_m_s2",
        )

class CompassSampleSerializer(_BaseSampleSerializer):
    class Meta(_BaseSampleSerializer.Meta):
        model = CompassSample
        fields = _BaseSampleSerializer.Meta.fields + (
            "mx_uT",
            "my_uT",
            "mz_uT",
        )

class PressureSampleSerializer(_BaseSampleSerializer):
    class Meta(_BaseSampleSerializer.Meta):
        model = PressureSample
        fields = _BaseSampleSerializer.Meta.fields + (
            "pressure_pa",
            "temperature_C",
        )

class MediaAssetSerializer(serializers.ModelSerializer):
    deployment_details = serializers.SerializerMethodField(read_only=True)
    mission_location = serializers.CharField(source='deployment.mission.location', read_only=True)
    
    class Meta:
        model = MediaAsset
        fields = (
            'id', 'deployment', 'media_type', 'file_path', 'start_time', 
            'end_time', 'fps', 'file_metadata', 'notes', 'deployment_details',
            'mission_location'
        )
        read_only_fields = ('id',)
    
    def get_deployment_details(self, obj):
        return {
            'sensor_name': obj.deployment.sensor.name,
            'mission_id': obj.deployment.mission.id,
            'mission_location': obj.deployment.mission.location
        }

class FrameIndexSerializer(serializers.ModelSerializer):
    media_asset_path = serializers.CharField(source='media_asset.file_path', read_only=True)
    nav_sample_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FrameIndex
        fields = (
            'id', 'media_asset', 'frame_number', 'timestamp', 'servo_pitch_deg',
            'closest_nav_sample', 'nav_match_time_diff_ms', 'media_asset_path',
            'nav_sample_details'
        )
        read_only_fields = ('id',)
    
    def get_nav_sample_details(self, obj):
        if obj.closest_nav_sample:
            return {
                'depth_m': obj.closest_nav_sample.depth_m,
                'yaw_deg': obj.closest_nav_sample.yaw_deg,
                'pitch_deg': obj.closest_nav_sample.pitch_deg,
                'roll_deg': obj.closest_nav_sample.roll_deg
            }
        return None