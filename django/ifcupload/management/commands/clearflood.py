from django.core.management.base import BaseCommand
from ifcupload.models import FloodDefenseMechanism

class Command(BaseCommand):
    help = 'Clears all data from the FloodDefenseMechanism table'

    def handle(self, *args, **kwargs):
        FloodDefenseMechanism.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared data from FloodDefenseMechanism'))
