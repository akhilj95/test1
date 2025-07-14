from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
import os
from datetime import datetime
import logging

# Import your models
from missions.models import (
    Mission, LogFile, NavSample, SensorDeployment, 
    ImuSample, CompassSample, PressureSample, Sensor
)

# Import pymavlink for parsing
try:
    from pymavlink import mavutil
    from pymavlink.DFReader import DFReader_binary
except ImportError:
    raise ImportError("pymavlink is required. Install with: pip install pymavlink")

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Parse ArduPilot .bin log files and extract sensor data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mission-id',
            type=int,
            required=True,
            help='Mission ID to process logs for'
        )
        parser.add_argument(
            '--log-file-id',
            type=int,
            help='Specific log file ID to process (optional)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for database inserts (default: 1000)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if data already exists'
        )

    def handle(self, *args, **options):
        mission_id = options['mission_id']
        log_file_id = options.get('log_file_id')
        batch_size = options['batch_size']
        force = options['force']

        try:
            mission = Mission.objects.get(id=mission_id)
        except Mission.DoesNotExist:
            raise CommandError(f'Mission with id {mission_id} does not exist')

        # Get log files to process
        log_files = mission.log_files.all()
        if log_file_id:
            log_files = log_files.filter(id=log_file_id)

        if not log_files.exists():
            raise CommandError('No log files found for processing')

        for log_file in log_files:
            if log_file.bin_path and os.path.exists(log_file.bin_path):
                self.stdout.write(f'Processing log file: {log_file.bin_path}')
                self.process_bin_file(log_file, batch_size, force)
            else:
                self.stdout.write(
                    self.style.WARNING(f'Bin file not found: {log_file.bin_path}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed logs for mission {mission_id}')
        )

    def process_bin_file(self, log_file, batch_size, force):
        """Process a single .bin log file"""
        mission = log_file.mission
        
        # Check if data already exists
        if not force:
            if (NavSample.objects.filter(mission=mission).exists() or
                ImuSample.objects.filter(log_file=log_file).exists()):
                self.stdout.write(
                    self.style.WARNING(f'Data already exists for {log_file.bin_path}. Use --force to reprocess.')
                )
                return

        # Get or create sensor deployments
        sensor_deployments = self.get_sensor_deployments(mission)

        try:
            # Parse the log file
            log_reader = DFReader_binary(log_file.bin_path)
            
            # Process messages in batches
            nav_samples = []
            imu_samples = []
            mag_samples = []
            pressure_samples = []
            
            message_count = 0
            
            while True:
                message = log_reader.recv_match()
                if message is None:
                    break
                
                message_count += 1
                if message_count % 10000 == 0:
                    self.stdout.write(f'Processed {message_count} messages...')
                
                # Convert timestamp to datetime
                timestamp = self.convert_timestamp(message.TimeUS)
                
                # Process different message types
                if message.get_type() == 'ATT':
                    nav_samples.append(self.create_nav_sample(message, mission, timestamp))
                
                elif message.get_type() == 'IMU':
                    imu_samples.append(self.create_imu_sample(
                        message, log_file, sensor_deployments.get('imu'), timestamp
                    ))
                
                elif message.get_type() == 'MAG':
                    mag_samples.append(self.create_mag_sample(
                        message, log_file, sensor_deployments.get('compass'), timestamp
                    ))
                
                elif message.get_type() == 'BARO':
                    pressure_samples.append(self.create_pressure_sample(
                        message, log_file, sensor_deployments.get('pressure'), timestamp
                    ))
                
                # Batch insert when batch size is reached
                if len(nav_samples) >= batch_size:
                    self.bulk_create_samples(NavSample, nav_samples)
                    nav_samples = []
                
                if len(imu_samples) >= batch_size:
                    self.bulk_create_samples(ImuSample, imu_samples)
                    imu_samples = []
                
                if len(mag_samples) >= batch_size:
                    self.bulk_create_samples(MagnetometerSample, mag_samples)
                    mag_samples = []
                
                if len(pressure_samples) >= batch_size:
                    self.bulk_create_samples(PressureSample, pressure_samples)
                    pressure_samples = []
            
            # Insert remaining samples
            if nav_samples:
                self.bulk_create_samples(NavSample, nav_samples)
            if imu_samples:
                self.bulk_create_samples(ImuSample, imu_samples)
            if mag_samples:
                self.bulk_create_samples(MagnetometerSample, mag_samples)
            if pressure_samples:
                self.bulk_create_samples(PressureSample, pressure_samples)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully processed {message_count} messages')
            )
            
        except Exception as e:
            logger.error(f'Error processing log file {log_file.bin_path}: {str(e)}')
            raise CommandError(f'Error processing log file: {str(e)}')

    def get_sensor_deployments(self, mission):
        """Get sensor deployments for the mission"""
        deployments = {}
        
        for deployment in mission.deployments.all():
            sensor_type = deployment.sensor.sensor_type
            if sensor_type == Sensor.SensorType.IMU:
                deployments['imu'] = deployment
            elif sensor_type == Sensor.SensorType.COMPASS:
                deployments['compass'] = deployment
            elif sensor_type == Sensor.SensorType.PRESSURE:
                deployments['pressure'] = deployment
        
        return deployments

    def convert_timestamp(self, time_us):
        """Convert ArduPilot timestamp (microseconds since boot) to datetime"""
        # Note: This is a simplified conversion. In practice, you might need
        # to correlate with GPS time or system time for absolute timestamps
        return timezone.now() - timezone.timedelta(microseconds=time_us)

    def create_nav_sample(self, message, mission, timestamp):
        """Create NavSample from ATT message"""
        return NavSample(
            mission=mission,
            timestamp=timestamp,
            roll_deg=message.Roll,
            pitch_deg=message.Pitch,
            yaw_deg=message.Yaw,
            # depth_m would come from other sensors or calculated
        )

    def create_imu_sample(self, message, log_file, deployment, timestamp):
        """Create ImuSample from IMU message"""
        if not deployment:
            return None
        
        return ImuSample(
            log_file=log_file,
            deployment=deployment,
            timestamp=timestamp,
            gx_rad_s=message.GyrX,
            gy_rad_s=message.GyrY,
            gz_rad_s=message.GyrZ,
            ax_m_s2=message.AccX,
            ay_m_s2=message.AccY,
            az_m_s2=message.AccZ,
        )

    def create_mag_sample(self, message, log_file, deployment, timestamp):
        """Create MagnetometerSample from MAG message"""
        if not deployment:
            return None
        
        return MagnetometerSample(
            log_file=log_file,
            deployment=deployment,
            timestamp=timestamp,
            mx_uT=message.MagX,
            my_uT=message.MagY,
            mz_uT=message.MagZ,
        )

    def create_pressure_sample(self, message, log_file, deployment, timestamp):
        """Create PressureSample from BARO message"""
        if not deployment:
            return None
        
        return PressureSample(
            log_file=log_file,
            deployment=deployment,
            timestamp=timestamp,
            pressure_pa=message.Press,
            temperature_C=message.Temp if hasattr(message, 'Temp') else None,
        )

    def bulk_create_samples(self, model_class, samples):
        """Bulk create samples with error handling"""
        samples = [s for s in samples if s is not None]  # Filter out None values
        if samples:
            try:
                with transaction.atomic():
                    model_class.objects.bulk_create(samples, ignore_conflicts=True)
                    self.stdout.write(f'Created {len(samples)} {model_class.__name__} records')
            except Exception as e:
                logger.error(f'Error bulk creating {model_class.__name__}: {str(e)}')
                # Fallback to individual creation
                for sample in samples:
                    try:
                        sample.save()
                    except Exception as save_error:
                        logger.error(f'Error saving individual {model_class.__name__}: {str(save_error)}')
