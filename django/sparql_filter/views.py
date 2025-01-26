import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from SPARQLWrapper import SPARQLWrapper, JSON, DIGEST

# Helper function to escape literals
def escape_literal(value):
    return value.replace('"', '\\"').replace("'", "\\'")

# Validation function for integers 
def validate_integer(value):
    return value.isdigit()

# Validation function for street and city names 
def validate_street_or_city_name(value):
    return re.match(r"^[A-Za-z' ]+$", value)

# Validation function for postcode 
def validate_postcode(value):
    return re.match(r"^\d{4}[A-Z]{2}$", value)

# Validation function for Bouwjaar 
def validate_bouwjaar(value):
    return re.match(r"^\d{4}$", value)

# Validation function for distance 
def validate_distance(value):
    return re.match(r"^\d+(\.\d+)?$", value)

def validate_year(value):
    return re.match(r"^\d{4}$", value)

@csrf_exempt
def sparql_query(request):
    # External endpoint (Kadaster). Replace URL with the correct endpoint of the repository.
    endpoint_url = "url"

    # Get parameters from the request
    BAG_ID = request.GET.get('BAG_ID', '').strip()
    straatNaam = request.GET.get('straatNaam', '').strip()
    stad = request.GET.get('stad', '').strip()
    huisnummer = request.GET.get('huisnummer', '').strip()
    postcode = request.GET.get('postcode', '').strip()
    Bouwjaar = request.GET.get('Bouwjaar', '').strip()

    # Initialize an empty list to hold the pattern statements
    pattern_statements = []
    error_messages = []

    # Handle BAG_ID
    if BAG_ID and validate_integer(BAG_ID):
        pattern_statements.append(f'?pand bag:identificatie "{BAG_ID}".')
    elif BAG_ID:
        error_messages.append('Invalid BAG_ID format. Must be an integer.')

    # Handle straatNaam
    if straatNaam and validate_street_or_city_name(straatNaam):
        pattern_statements.append(f'?openbareRuimte skos:prefLabel "{straatNaam}".')
    elif straatNaam:
        error_messages.append('Invalid straatNaam format.')

    # Handle stad
    if stad and validate_street_or_city_name(stad):
        pattern_statements.append(f'?woonplaats skos:prefLabel "{stad}".')
    elif stad:
        error_messages.append('Invalid stad format.')

    # Handle huisnummer
    if huisnummer and validate_integer(huisnummer):
        pattern_statements.append(f'?nummeraanduiding bag:huisnummer {huisnummer}.')
    elif huisnummer:
        error_messages.append('Invalid huisnummer format.')

    # Handle postcode
    if postcode and validate_postcode(postcode):
        pattern_statements.append(f'?nummeraanduiding bag:postcode "{postcode}".')
    elif postcode:
        error_messages.append('Invalid postcode format.')

    # Handle Bouwjaar
    if Bouwjaar and validate_bouwjaar(Bouwjaar):
        pattern_statements.append(f'?pand bag:oorspronkelijkBouwjaar "{Bouwjaar}".')
    elif Bouwjaar:
        error_messages.append('Invalid Bouwjaar format.')

    # Return errors
    if error_messages:
        return JsonResponse({'error': True, 'messages': error_messages}, safe=False)

    # Join all the pattern statements
    pattern_clause = "\n".join(pattern_statements)

    # Construct the SPARQL query
    sparql_query = f"""
    PREFIX bag: <http://bag.basisregistraties.overheid.nl/def/bag#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>

    SELECT DISTINCT  
      ?BAG_ID 
      ?straatNaam 
      ?Bouwjaar 
      ?status 
      ?stad 
      ?pand
      ?huisnummer
      ?postcode
      ?polygon
      (GROUP_CONCAT(DISTINCT ?gebruiksdoel; separator=", ") AS ?gebruiksdoelen)
    WHERE {{
      ?openbareRuimte 
        bag:ligtIn ?woonplaats;
        skos:prefLabel ?straatNaam.
      
      ?woonplaats 
        skos:prefLabel ?stad.
      
      ?nummeraanduiding 
        bag:huisnummer ?huisnummer ;
        bag:ligtAan ?openbareRuimte;
        bag:postcode ?postcode.
      
      ?verblijfsobject 
        bag:hoofdadres ?nummeraanduiding;
        bag:gebruiksdoel ?gebruiksdoel;
        bag:maaktDeelUitVan ?pand.
      
      ?pand 
        a bag:Pand;
        bag:oorspronkelijkBouwjaar ?Bouwjaar;
        bag:status ?status;
        bag:geometrie/geo:asWKT ?polygon;
        bag:identificatie ?BAG_ID.

      {pattern_clause}
    }}
    GROUP BY  
      ?BAG_ID 
      ?straatNaam 
      ?Bouwjaar 
      ?status 
      ?stad 
      ?pand
      ?huisnummer
      ?postcode
      ?polygon
    ORDER BY ?huisnummer
    LIMIT 100
    """

    try:
        # Initialize SPARQLWrapper with the endpoint URL
        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        sparql.setCredentials("User", "Password")

        # Execute the query and convert the results to JSON
        results = sparql.query().convert()

        return JsonResponse(results, safe=False)

    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def sparql_query_municipality(request):
    endpoint_url = 'url'

    # Get parameters from the request
    BAG_ID = request.GET.get('BAG_ID', '').strip()
    straatNaam = request.GET.get('straatNaam', '').strip()
    stad = request.GET.get('stad', '').strip()
    huisnummer = request.GET.get('huisnummer', '').strip()
    postcode = request.GET.get('postcode', '').strip()
    Bouwjaar = request.GET.get('Bouwjaar', '').strip()
    include_flood_defense = request.GET.get('includeFloodDefense', '').strip().lower() == 'true'

    # Initialize pattern statements
    pattern_statements = []
    if BAG_ID:
        pattern_statements.append(f'?pand bag:identificatie "{BAG_ID}".')
    if straatNaam:
        pattern_statements.append(f'?openbareRuimte skos:prefLabel "{straatNaam}".')
    if stad:
        pattern_statements.append(f'?woonplaats skos:prefLabel "{stad}".')
    if huisnummer:
        pattern_statements.append(f'?nummeraanduiding bag:huisnummer {huisnummer}.')
    if postcode:
        pattern_statements.append(f'?nummeraanduiding bag:postcode "{postcode}".')
    if Bouwjaar:
        pattern_statements.append(f'?pand bag:oorspronkelijkBouwjaar "{Bouwjaar}".')

    pattern_clause = "\n".join(pattern_statements)

    # Add conditional match for flood defense
    flood_defense_clause = """
    ?pand abaronbo:hasFDM true.
    """ if include_flood_defense else ""

    # Construct the query
    sparql_query = f"""
    PREFIX bag: <http://bag.basisregistraties.overheid.nl/def/bag#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX abaronbo: <https://abaronbo.com#>

    SELECT DISTINCT  
      ?BAG_ID 
      ?straatNaam 
      ?Bouwjaar 
      ?status 
      ?stad 
      ?pand
      ?huisnummer
      ?postcode
      ?polygon
      (GROUP_CONCAT(DISTINCT ?gebruiksdoel; separator=", ") AS ?gebruiksdoelen)
    WHERE {{
      ?openbareRuimte 
        bag:ligtIn ?woonplaats;
        skos:prefLabel ?straatNaam.
      
      ?woonplaats 
        skos:prefLabel ?stad.
      
      ?nummeraanduiding 
        bag:huisnummer ?huisnummer ;
        bag:ligtAan ?openbareRuimte;
        bag:postcode ?postcode.
      
      ?verblijfsobject 
        bag:hoofdadres ?nummeraanduiding;
        bag:gebruiksdoel ?gebruiksdoel;
        bag:maaktDeelUitVan ?pand.
      
      ?pand 
        a bag:Pand;
        bag:oorspronkelijkBouwjaar ?Bouwjaar;
        bag:status ?status;
        bag:geometrie/geo:asWKT ?polygon;
        bag:identificatie ?BAG_ID.

      {pattern_clause}

      {flood_defense_clause}
    }}
    GROUP BY  
      ?BAG_ID 
      ?straatNaam 
      ?Bouwjaar 
      ?status 
      ?stad 
      ?pand
      ?huisnummer
      ?postcode
      ?polygon
    ORDER BY ?huisnummer
    LIMIT 100
    """
    print(f"SPARQL Query: {sparql_query}")
    try:
        # Initialize SPARQLWrapper with the endpoint URL
        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        sparql.setCredentials("Username", "Password")

        # Execute the query and convert the results to JSON
        results = sparql.query().convert()

        return JsonResponse(results, safe=False)

    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)
