
from django.core.management.base import BaseCommand
from ifcupload.models import BuildingIFC

class Command(BaseCommand):
    help = 'Clears all data from the BuildingIFC table'

    def handle(self, *args, **kwargs):
        BuildingIFC.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared data from BuildingIFC'))
