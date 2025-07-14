import os
from pathlib import Path
from django.conf import settings
from datetime import datetime, timezone
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as django_timezone
from django.db import transaction
from missions.models import (
    Mission, LogFile, SensorDeployment, 
    NavSample, ImuSample, CompassSample, PressureSample
)
from pymavlink import mavutil
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Parse a log file by LogFile ID, unless already parsed (simplified version)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--logfile-id", 
            type=int, 
            required=True, 
            help="ID of the LogFile to parse."
        )
        parser.add_argument(
            "--batch-size", 
            type=int, 
            default=1000, 
            help="Batch size for bulk insert operations."
        )
        parser.add_argument(
            "--force", 
            action="store_true", 
            help="Force re-parsing even if already parsed."
        )
        parser.add_argument(
            "--imu-instances", 
            type=str, 
            default="0", 
            help="IMU instances to parse (comma-separated, e.g., '0,1')."
        )
        parser.add_argument(
            "--mag-instances", 
            type=str, 
            default="0,1", 
            help="MAG instances to parse (comma-separated, e.g., '0,1')."
        )
        parser.add_argument(
            "--baro-instances", 
            type=str, 
            default="1", 
            help="BARO instances to parse (comma-separated, e.g., '1')."
        )

    def handle(self, *args, **options):
        logfile_id = options["logfile_id"]
        batch_size = options["batch_size"]
        force = options["force"]
        
        # Parse instance arguments
        imu_instances = [int(x.strip()) for x in options["imu_instances"].split(",")]
        mag_instances = [int(x.strip()) for x in options["mag_instances"].split(",")]
        baro_instances = [int(x.strip()) for x in options["baro_instances"].split(",")]
        
        try:
            logfile = LogFile.objects.get(pk=logfile_id)
        except LogFile.DoesNotExist:
            raise CommandError(f"LogFile with id={logfile_id} does not exist.")

        if logfile.already_parsed and not force:
            raise CommandError(f"LogFile {logfile_id} has already been parsed. Use --force to re-parse.")
        
        # Get mission
        mission = logfile.mission
        if not mission.end_time:
            raise CommandError("Mission must have an end_time before import.")
        
        self.stdout.write(f"Mission found: {mission}")
        self.stdout.write(f"IMU instances: {imu_instances}")
        self.stdout.write(f"MAG instances: {mag_instances}")
        self.stdout.write(f"BARO instances: {baro_instances}")
        
        # Get deployments for linking samples
        deployments = SensorDeployment.objects.filter(mission=mission)
        deployments_by_sensor_type = {}
        for deployment in deployments:
            sensor_type = deployment.sensor.sensor_type
            if sensor_type not in deployments_by_sensor_type:
                deployments_by_sensor_type[sensor_type] = []
            deployments_by_sensor_type[sensor_type].append(deployment)
        
        # Initialize the simplified loader
        loader = SimplifiedBinLoader(
            logfile=logfile,
            mission=mission,
            deployments_by_sensor_type=deployments_by_sensor_type,
            imu_instances=imu_instances,
            mag_instances=mag_instances,
            baro_instances=baro_instances,
            batch_size=batch_size,
            stdout=self.stdout
        )
        
        # Run the parsing
        try:
            loader.run()
            # Mark as parsed
            logfile.already_parsed = True
            logfile.save()
            self.stdout.write(self.style.SUCCESS("Parsing completed successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Parsing failed: {str(e)}"))
            raise


class SimplifiedBinLoader:
    """
    Simplified loader class for parsing ArduPilot .bin log files.
    
    This version directly maps message types to sample models without the complex
    deployment-based lookup system.
    """
    
    def __init__(self, logfile, mission, deployments_by_sensor_type, 
                 imu_instances, mag_instances, baro_instances, batch_size=1000, stdout=None):
        self.logfile = logfile
        self.mission = mission
        self.deployments_by_sensor_type = deployments_by_sensor_type
        self.imu_instances = imu_instances
        self.mag_instances = mag_instances
        self.baro_instances = baro_instances
        self.batch_size = batch_size
        self.stdout = stdout
        
        # Navigation state for combining ATT and AHR2 data
        self.nav_data_cache = {}
        
        self.stats = {
            "total_messages": 0,
            "filtered_messages": 0,
            "saved_samples": 0,
            "errors": 0,
            "by_type": {}
        }
        
        # Validate bin_path exists
        if not self.logfile.bin_path:
            raise CommandError("No bin_path specified in LogFile.")
        
        bin_path = settings.PROJECT_DIR / self.logfile.bin_path
        if not bin_path.exists():
            raise CommandError(f"Binary log file not found: {bin_path}")
        
        # Initialize pymavlink connection
        try:
            self.log_connection = mavutil.mavlink_connection(
                str(bin_path), 
                dialect="ardupilotmega"
            )
        except Exception as e:
            raise CommandError(f"Failed to open log file: {str(e)}")
    
    def log_message(self, message):
        """Helper to log messages to stdout if available."""
        if self.stdout:
            self.stdout.write(message)
    
    def run(self):
        """Main parsing loop with simplified logic."""
        self.log_message("Starting simplified log file parsing...")
        
        # Initialize batch containers
        batches = {
            ImuSample: [],
            CompassSample: [],
            PressureSample: [],
            NavSample: [],
        }
        
        # Get the log file creation time as baseline for timestamp conversion
        log_file_created = self.logfile.created_at
        
        # Process messages
        for msg in iter(self.log_connection.recv_match, None):
            if msg is None:
                break
                
            self.stats["total_messages"] += 1
            
            try:
                # Convert timestamp to timezone-aware datetime
                timestamp = self._resolve_timestamp(msg, log_file_created)
                
                # Check if timestamp is within mission bounds
                if not (self.mission.start_time <= timestamp <= self.mission.end_time):
                    continue
                
                self.stats["filtered_messages"] += 1
                
                # Process message based on type
                msg_type = msg.get_type()
                
                if msg_type == "IMU":
                    self._process_imu_message(msg, timestamp, batches)
                elif msg_type == "MAG":
                    self._process_mag_message(msg, timestamp, batches)
                elif msg_type == "BARO":
                    self._process_baro_message(msg, timestamp, batches)
                elif msg_type == "ATT":
                    self._process_att_message(msg, timestamp, batches)
                elif msg_type == "AHR2":
                    self._process_ahr2_message(msg, timestamp, batches)
                
                # Check if we need to flush batches
                for model_class, batch in batches.items():
                    if len(batch) >= self.batch_size:
                        self._flush_batch(model_class, batch)
                        batches[model_class] = []
                            
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Error processing message {msg.get_type()}: {str(e)}")
                continue
        
        # Flush any remaining batches
        for model_class, batch in batches.items():
            if batch:
                self._flush_batch(model_class, batch)
        
        # Print statistics
        self._print_statistics()
    
    def _process_imu_message(self, msg, timestamp, batches):
        """Process IMU messages for specified instances."""
        if not hasattr(msg, 'I'):
            return
        
        instance = msg.I
        if instance not in self.imu_instances:
            return
        
        # Get appropriate deployment
        deployment = self._get_deployment_for_sensor_type('imu', instance)
        if not deployment:
            return
        
        # Create IMU sample
        sample = ImuSample(
            log_file=self.logfile,
            deployment=deployment,
            timestamp=timestamp,
            gx_rad_s=getattr(msg, 'GyrX', 0.0),
            gy_rad_s=getattr(msg, 'GyrY', 0.0),
            gz_rad_s=getattr(msg, 'GyrZ', 0.0),
            ax_m_s2=getattr(msg, 'AccX', 0.0),
            ay_m_s2=getattr(msg, 'AccY', 0.0),
            az_m_s2=getattr(msg, 'AccZ', 0.0),
        )
        
        batches[ImuSample].append(sample)
        self.stats["saved_samples"] += 1
        self.stats["by_type"]["IMU"] = self.stats["by_type"].get("IMU", 0) + 1
    
    def _process_mag_message(self, msg, timestamp, batches):
        """Process MAG messages for specified instances."""
        if not hasattr(msg, 'I'):
            return
        
        instance = msg.I
        if instance not in self.mag_instances:
            return
        
        # Get appropriate deployment
        deployment = self._get_deployment_for_sensor_type('compass', instance)
        if not deployment:
            return
        
        # Create compass sample
        sample = CompassSample(
            log_file=self.logfile,
            deployment=deployment,
            timestamp=timestamp,
            mx_uT=getattr(msg, 'MagX', 0.0),
            my_uT=getattr(msg, 'MagY', 0.0),
            mz_uT=getattr(msg, 'MagZ', 0.0),
        )
        
        batches[CompassSample].append(sample)
        self.stats["saved_samples"] += 1
        self.stats["by_type"]["MAG"] = self.stats["by_type"].get("MAG", 0) + 1
    
    def _process_baro_message(self, msg, timestamp, batches):
        """Process BARO messages for specified instances."""
        if not hasattr(msg, 'I'):
            return
        
        instance = msg.I
        if instance not in self.baro_instances:
            return
        
        # Get appropriate deployment
        deployment = self._get_deployment_for_sensor_type('pressure', instance)
        if not deployment:
            return
        
        # Create pressure sample
        sample = PressureSample(
            log_file=self.logfile,
            deployment=deployment,
            timestamp=timestamp,
            pressure_pa=getattr(msg, 'Press', 0.0),
            temperature_C=getattr(msg, 'Temp', None),
        )
        
        batches[PressureSample].append(sample)
        self.stats["saved_samples"] += 1
        self.stats["by_type"]["BARO"] = self.stats["by_type"].get("BARO", 0) + 1
    
    def _process_att_message(self, msg, timestamp, batches):
        """Process ATT messages for navigation attitude data."""
        # Create navigation sample with attitude data
        sample = NavSample(
            mission=self.mission,
            timestamp=timestamp,
            roll_deg=getattr(msg, 'Roll', None),
            pitch_deg=getattr(msg, 'Pitch', None),
            yaw_deg=getattr(msg, 'Yaw', None),
            depth_m=None,  # Will be filled by AHR2 if available
        )
        
        batches[NavSample].append(sample)
        self.stats["saved_samples"] += 1
        self.stats["by_type"]["ATT"] = self.stats["by_type"].get("ATT", 0) + 1
    
    def _process_ahr2_message(self, msg, timestamp, batches):
        """Process AHR2 messages for navigation altitude data."""
        # Create navigation sample with altitude data
        sample = NavSample(
            mission=self.mission,
            timestamp=timestamp,
            roll_deg=getattr(msg, 'Roll', None),
            pitch_deg=getattr(msg, 'Pitch', None),
            yaw_deg=getattr(msg, 'Yaw', None),
            depth_m=getattr(msg, 'Alt', None),  # Altitude in meters
        )
        
        batches[NavSample].append(sample)
        self.stats["saved_samples"] += 1
        self.stats["by_type"]["AHR2"] = self.stats["by_type"].get("AHR2", 0) + 1
    
    def _get_deployment_for_sensor_type(self, sensor_type, instance):
        """Get deployment for a specific sensor type and instance."""
        deployments = self.deployments_by_sensor_type.get(sensor_type, [])
        
        # For now, we'll use the first deployment of each type
        # In a more sophisticated system, you might want to match by instance
        if deployments:
            return deployments[0]
        
        # Log warning if no deployment found
        logger.warning(f"No deployment found for sensor type '{sensor_type}' instance {instance}")
        return None
    
    def _resolve_timestamp(self, msg, log_file_created):
        """Convert message timestamp to timezone-aware datetime."""
        if hasattr(msg, 'TimeUS') and msg.TimeUS:
            # TimeUS is microseconds since boot
            time_offset_seconds = msg.TimeUS / 1_000_000
            return log_file_created + django_timezone.timedelta(seconds=time_offset_seconds)
        
        # Last resort: use log file creation time
        return log_file_created
    
    def _flush_batch(self, model_class, batch):
        """Flush a batch of samples to the database."""
        if not batch:
            return
        
        try:
            with transaction.atomic():
                model_class.objects.bulk_create(batch, ignore_conflicts=True)
            self.log_message(f"Saved {len(batch)} {model_class.__name__} samples")
        except Exception as e:
            logger.error(f"Error saving batch of {model_class.__name__}: {str(e)}")
            self.stats["errors"] += len(batch)
    
    def _print_statistics(self):
        """Print parsing statistics."""
        self.log_message(f"Parsing complete! Statistics:")
        self.log_message(f"  Total messages: {self.stats['total_messages']}")
        self.log_message(f"  Filtered messages: {self.stats['filtered_messages']}")
        self.log_message(f"  Saved samples: {self.stats['saved_samples']}")
        self.log_message(f"  Errors: {self.stats['errors']}")
        self.log_message(f"  By message type:")
        for msg_type, count in self.stats['by_type'].items():
            self.log_message(f"    {msg_type}: {count}")