import csv
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import ifcopenshell
import os
from django.conf import settings

# Function to extract quantity value
def get_quantity_value(quantity):
    for attr in ['AreaValue', 'CountValue', 'LengthValue', 'TimeValue', 'VolumeValue', 'WeightValue']:
        value = getattr(quantity, attr, None)
        if value is not None:
            return value
    return None

@csrf_exempt
def get_ifc_attributes(request):
    ifc_url = request.POST.get('ifc_url')
    entity_type = request.POST.get('entity_type')
    file_path = os.path.join(settings.MEDIA_ROOT, ifc_url.split('/media/')[1])

    model = ifcopenshell.open(file_path)
    entities = model.by_type(entity_type)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = []
        headers = ['GlobalId', 'Name', 'Description', 'ObjectType']

        # Extract attributes
        for entity in entities:
            entity_properties = {
                'GlobalId': entity.GlobalId,
                'Name': entity.Name or '',
                'Description': entity.Description or '',
                'ObjectType': entity.ObjectType or '',
            }
            
            # Extract properties and/or quantities
            for relDefinesByProperties in entity.IsDefinedBy:
                if relDefinesByProperties.is_a('IfcRelDefinesByProperties'):
                    property_set = relDefinesByProperties.RelatingPropertyDefinition
                    
                    # Handle HasProperties
                    if property_set and hasattr(property_set, 'HasProperties'):
                        for prop in property_set.HasProperties:
                            entity_properties[prop.Name] = prop.NominalValue.wrappedValue if prop.NominalValue else ''

                    # Handle Quantities
                    if property_set and hasattr(property_set, 'Quantities'):
                        for quantity in property_set.Quantities:
                            quantity_value = get_quantity_value(quantity)
                            if quantity_value is not None:
                                entity_properties[quantity.Name] = quantity_value

            data.append(entity_properties)
            headers.extend([key for key in entity_properties.keys() if key not in headers])

        return JsonResponse({'headers': headers, 'data': data}, safe=False)

    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{entity_type}_attributes.csv"'

        writer = csv.writer(response)
        headers_written = False

        # Extract attributes
        for entity in entities:
            entity_properties = {
                'GlobalId': entity.GlobalId,
                'Name': entity.Name or '',
                'Description': entity.Description or '',
                'ObjectType': entity.ObjectType or '',
            }
            
            # Extract properties and/or quantities
            for relDefinesByProperties in entity.IsDefinedBy:
                if relDefinesByProperties.is_a('IfcRelDefinesByProperties'):
                    property_set = relDefinesByProperties.RelatingPropertyDefinition
                    
                    # Handle HasProperties
                    if property_set and hasattr(property_set, 'HasProperties'):
                        for prop in property_set.HasProperties:
                            entity_properties[prop.Name] = prop.NominalValue.wrappedValue if prop.NominalValue else ''

                    # Handle Quantities
                    if property_set and hasattr(property_set, 'Quantities'):
                        for quantity in property_set.Quantities:
                            quantity_value = get_quantity_value(quantity)
                            if quantity_value is not None:
                                entity_properties[quantity.Name] = quantity_value

            # Write headers
            if not headers_written:
                headers = list(entity_properties.keys())
                writer.writerow(headers)
                headers_written = True

            row_data = [entity_properties.get(key, '') for key in headers]
            writer.writerow(row_data)

        return response
