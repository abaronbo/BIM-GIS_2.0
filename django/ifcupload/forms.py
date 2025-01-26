from django import forms

class DatasetUploadForm(forms.Form):
    dataset_file = forms.FileField()

class IFCUploadForm(forms.Form):
    ref_bag_id = forms.IntegerField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    ifc_file = forms.FileField()