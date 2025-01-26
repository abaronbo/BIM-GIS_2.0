
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .forms import DatasetUploadForm, IFCUploadForm
from django.http import JsonResponse, HttpResponse
from .models import BuildingIFC, FloodDefenseMechanism
import csv
from io import TextIOWrapper
import os
from django.conf import settings
from .ifc_converter import convertIFCSPFtoTTL
from .add_triples import add_flood_defense_triples
import json


# Handles requests to the upload form page. 
def upload_form(request):
    ref_bag_id = request.GET.get('ref_bag_id', '') 
    print("Received ref_bag_id:", ref_bag_id)

    # Initial value for ref_bag_id.
    form = IFCUploadForm(initial={'ref_bag_id': ref_bag_id}) if ref_bag_id else IFCUploadForm()
    
    # Creates a BuildingIFC Object.
    if request.method == 'POST':
        form = IFCUploadForm(request.POST, request.FILES)
        if form.is_valid():
            ref_bag_id = int(form.cleaned_data['ref_bag_id'])
            BuildingIFC.objects.update_or_create(
                ref_bag_id=ref_bag_id,
                defaults={'ifc_file': form.cleaned_data['ifc_file']}
            )
            return redirect('upload_success') 

    return render(request, 'ifcupload/upload_form.html', {'form': form})

# Handles requests to the upload file (IFC) page.
def upload_ifc(request):
    if request.method == 'POST':
        ref_bag_id = request.POST.get('ref_bag_id')
        ifc_file = request.FILES.get('ifc_file')

        # Save the uploaded IFC file
        building_ifc = BuildingIFC.objects.create(ref_bag_id=ref_bag_id, ifc_file=ifc_file)

        # Define the input and output file paths
        input_file_path = building_ifc.ifc_file.path 
        output_file_name = f"{building_ifc.ifc_file.name.split('.')[0]}.ttl"
        output_file_path = os.path.join(settings.MEDIA_ROOT, 'ttl_files', output_file_name)

        # Ensure the directory for TTL files exists
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        # Call the conversion function to convert IFC to RDF (TTL) and pass ref_bag_id
        convertIFCSPFtoTTL(input_file_path, output_file_path, ref_bag_id)

        # Render the success page
        return render(request, 'ifcupload/upload_success.html', {'rdf_file': output_file_path})
    
    return HttpResponse('Invalid request', status=400)

# Returns the URL of a building based on its bag_id when the building is clicked in Cesium 
def get_ifc_url(request):
    ref_bag_id = request.GET.get('ref_bag_id')
    try:
        building_ifc = BuildingIFC.objects.get(ref_bag_id=ref_bag_id)
        return JsonResponse({'status': 'success', 'ifc_url': building_ifc.ifc_file.url})
    except BuildingIFC.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)

@csrf_exempt
def save_flood_defense(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ref_bag_id = data.get("refBag")
            global_id = data.get("globalId")
            name = data.get("name")
            class_type = data.get("classType")
            fragment_id_map = data.get("fragmentIdMap")  
            fdm_type = data.get("type")  
            fdm_category = data.get("category")  # New field
            fdm_height = data.get("height") 
            fdm_width = data.get("width")  
            year_of_review = data.get("yearOfReview")  # New field
            
            # Validate fields
            if not (ref_bag_id and global_id):
                return JsonResponse({"status": "error", "message": "Missing refBag or globalId."}, status=400)

            fragment_ids = list(fragment_id_map.keys())
            fragment_ids_str = ','.join(fragment_ids)

            # Create a new FloodDefenseMechanism instance
            flood_defense = FloodDefenseMechanism(
                ref_bag_id=ref_bag_id,
                global_id=global_id,
                name=name,
                class_type=class_type,
                fragment_id_map=fragment_ids_str,
                type=fdm_type,  
                category=fdm_category,  # New field
                height=fdm_height,  
                width=fdm_width,  
                year_of_review=year_of_review  # New field
            )
            print("Saving FloodDefenseMechanism:", flood_defense)
            flood_defense.save()

            return JsonResponse({"status": "success", "message": "Flood defense mechanism saved successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)



def get_flood_defense_mechanisms(request):
    mechanisms = FloodDefenseMechanism.objects.all().values(
        "ref_bag_id", 
        "fragment_id_map", 
        "global_id", 
        "name", 
        "class_type", 
        "type",  
        "category",  # New field
        "height",  
        "width",
        "year_of_review"  # New field
    )
    grouped_data = {}
    for mechanism in mechanisms:
        ref_bag_id = mechanism["ref_bag_id"]
        if ref_bag_id not in grouped_data:
            grouped_data[ref_bag_id] = {"ref_bag_id": ref_bag_id, "details": []}
        grouped_data[ref_bag_id]["details"].append({
            "fragment_id_map": mechanism["fragment_id_map"],
            "global_id": mechanism["global_id"],
            "name": mechanism["name"],
            "class_type": mechanism["class_type"],
            "type": mechanism["type"],
            "category": mechanism["category"],  
            "height": mechanism["height"],
            "width": mechanism["width"],
            "year_of_review": mechanism["year_of_review"],  
        })
    return JsonResponse({"status": "success", "defense_mechanisms": list(grouped_data.values())})

    
# Handles the upload of CSV files.
def upload_dataset(request):
    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_dataset_file(request.FILES['dataset_file'])
            return render(request, 'upload_dataset_success.html')
    else:
        form = DatasetUploadForm()

    return render(request, 'upload_dataset.html', {'form': form})

# Processes CSV files, creating BuildingIFC objects.
def handle_dataset_file(f):
    text_file = TextIOWrapper(f, encoding='utf-8')
    reader = csv.reader(text_file)

    headers = next(reader, None)
    if headers is None:
        return
    try:
        ref_bag_id_index = headers.index('ref_bag_id')
        file_path_index = headers.index('file_path')
    except ValueError as e:
        print("Column names not found in CSV header. Error:", e)
        return
    for row in reader:
        try:
            ref_bag_id = int(row[ref_bag_id_index])
            file_path = row[file_path_index]
            BuildingIFC.objects.update_or_create(ref_bag_id=ref_bag_id, defaults={'ifc_file': file_path})
        except (ValueError, IndexError) as e:
            print("Error processing row:", row, "Error:", e)

    text_file.detach()

@csrf_exempt
def add_flood_defense_mechanism(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Received request data:", data)
            ref_bag_id = data.get("ref_bag_id")
            fdm_details = data.get("fdm_details", [])  
            print("FDM details passed to add_flood_defense_triples:", fdm_details)
            if not ref_bag_id:
                return JsonResponse({"status": "error", "message": "Missing ref_bag_id."})
            
            if not fdm_details:
                return JsonResponse({"status": "error", "message": "Missing FDM details."})

            # Call the script to add triples
            result = add_flood_defense_triples(ref_bag_id, fdm_details)
            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)
