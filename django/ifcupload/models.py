from django.db import models

class BuildingIFC(models.Model):
    ref_bag_id = models.IntegerField(primary_key=True)
    ifc_file = models.FileField(upload_to='ifc_files/')

class FloodDefenseMechanism(models.Model):
    ref_bag_id = models.CharField(max_length=255)
    global_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)
    class_type = models.CharField(max_length=255, null=True, blank=True)
    fragment_id_map = models.JSONField(blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    height = models.FloatField(null=True, blank=True)
    width = models.FloatField(null=True, blank=True)
    year_of_review = models.IntegerField(null=True, blank=True) 

    def __str__(self):
        return f"Flood Defense: {self.ref_bag_id} - {self.global_id}"

