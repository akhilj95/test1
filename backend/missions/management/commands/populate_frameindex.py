from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from missions.models import MediaAsset, FrameIndex, NavSample
from datetime import timedelta
from bisect import bisect_left

class Command(BaseCommand):
    help = "Populate FrameIndex for a video MediaAsset by calculating frame timestamps and linking closest NavSample."

    def add_arguments(self, parser):
        parser.add_argument('mediaasset_id', type=int, help='ID of the MediaAsset to process')

    def handle(self, *args, **options):
        mediaasset_id = options['mediaasset_id']
        try:
            media = MediaAsset.objects.get(pk=mediaasset_id)
        except MediaAsset.DoesNotExist:
            raise CommandError(f'MediaAsset with id={mediaasset_id} does not exist.')

        if media.media_type != MediaAsset.MediaType.VIDEO:
            raise CommandError('MediaAsset must be a video.')

        if not (media.start_time and media.end_time and media.fps):
            raise CommandError('MediaAsset start_time, end_time, and fps must be set.')

        # Frame parameters
        fps = float(media.fps)
        interval = timedelta(seconds=1 / fps)
        duration_seconds = (media.end_time - media.start_time).total_seconds()
        total_frames = int(duration_seconds * fps)

        # Get mission from related deployment
        mission = media.deployment.mission

        # Get all NavSamples sorted by timestamp for binary search
        navsamples = list(NavSample.objects.filter(mission=mission).order_by('timestamp').values('id', 'timestamp'))

        def find_closest_navsample_id(target_timestamp):
            # Binary search for closest timestamp
            timestamps = [ns['timestamp'] for ns in navsamples]
            pos = bisect_left(timestamps, target_timestamp)
            if not timestamps:
                return None
            if pos == 0:
                return navsamples[0]['id']
            if pos == len(timestamps):
                return navsamples[-1]['id']
            before = navsamples[pos - 1]
            after = navsamples[pos]
            if abs((target_timestamp - before['timestamp']).total_seconds()) <= abs((after['timestamp'] - target_timestamp).total_seconds()):
                return before['id']
            else:
                return after['id']

        # Remove previous frame indexes
        FrameIndex.objects.filter(media_asset=media).delete()

        to_create = []
        for frame_number in range(total_frames):
            timestamp = media.start_time + frame_number * interval
            closest_nav_id = find_closest_navsample_id(timestamp) if navsamples else None
            to_create.append(
                FrameIndex(
                    media_asset=media,
                    frame_number=frame_number,
                    timestamp=timestamp,
                    closest_nav_sample_id=closest_nav_id,
                )
            )
            if len(to_create) >= 1000:
                FrameIndex.objects.bulk_create(to_create)
                to_create = []

        if to_create:
            FrameIndex.objects.bulk_create(to_create)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully populated {total_frames} frames for MediaAsset {mediaasset_id}."
        ))