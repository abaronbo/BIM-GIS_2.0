import requests
import uuid


def get_element_uri(global_id, repository_url, auth):
    print (global_id)
    """
    Retrieves the URI of the bot:Element associated with the given global_id.

    :param global_id: The GUID of the bot:Element.
    :param repository_url: The SPARQL endpoint of the repository.
    :param auth: Authentication tuple (username, password) for the repository.
    :return: The URI of the bot:Element or None if not found.
    """
    query = f"""
    PREFIX bot: <https://w3id.org/bot#>
    PREFIX inst: <http://linkedbuildingdata.net/ifc/resources/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX props:  <https://w3id.org/props#> 

    SELECT ?element
    WHERE {{
        ?element a bot:Element ;
                 props:hasCompressedGuid "{global_id}"^^xsd:string .
    }}
    """

    headers = {"Accept": "application/sparql-results+json"}
    params = {"query": query}
    
    # Use GET request with parameters
    response = requests.get(
        repository_url,
        headers=headers,
        params=params,
        auth=auth
    )

    if response.status_code == 200:
        results = response.json().get("results", {}).get("bindings", [])
        if results:
            return results[0]["element"]["value"]
    else:
        raise Exception(f"Failed to query element URI. HTTP {response.status_code}: {response.text}")

    return None

def add_flood_defense_triples(ref_bag_id, fdm_details):
    """
    Adds flood defense mechanism triples to the GraphDB repository.
    :param ref_bag_id: The refBagId of the building.
    :param fdm_details: A list of dictionaries containing FDM details.
    """
    repository_url = "url"
    graph_name = "urn:Test"
    auth = ("User", "Password")
    headers = {
        "Content-Type": "text/turtle",
        "Accept": "application/sparql-results+json"
    }
    params = {
        "context": f"<{graph_name}>"
    }

    # Define namespace prefixes
    prefixes = """
    @prefix abaronbo:  <https://abaronbo.com#> .
    @prefix bag_pand:  <http://bag.basisregistraties.overheid.nl/bag/id/pand/> .
    @prefix bgt: <https://bgt.basisregistraties.overheid.nl/bgt2/def/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix inst: <http://linkedbuildingdata.net/ifc/resources/> .
    @prefix aquo: <https://www.aquo.nl/index.php/Imwa_sim_22.1/doc/objecttype/> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    """

    # Create type and category translations
    type_translation = {
        "Flexible water barrier": "aquo:FlexibleWaterBarrier",
        "Wall construction": "aquo:WallConstruction",
        "Cofferdam": "aquo:Cofferdam",
        "Civil work": "aquo:CivilWork",
        "High grounds": "aquo:HighGrounds",
        "Dune": "aquo:Dune",
        "Dike": "aquo:Dike",
        "Dam": "aquo:Dam"
    }

    category_translation = {
        "Regional flood defense": "aquo:RegionalFloodDefense",
        "Primary flood defense": "aquo:PrimaryFloodDefense",
        "Other flood defenses": "aquo:OtherFloodDefenses",
        "Foreland barrier": "aquo:ForelandBarrier",
        "Compartmentalization barrier": "aquo:CompartmentalizationBarrier",
        "Barriers along regional rivers and canals": "aquo:BarriersAlongRegionalRiversAndCanals",
        "Polder dike": "aquo:PolderDike"
    }

    # Initialize triples
    triples = [prefixes]
    triples.append(f'bag_pand:{ref_bag_id} abaronbo:hasFDM true .')

    for fdm in fdm_details:
        print(f"Processing FDM detail: {fdm}")
        fdm_id = str(uuid.uuid4())
        translated_type = type_translation.get(fdm["type"], "aquo:Unknown")
        translated_category = category_translation.get(fdm["category"], "aquo:Unknown")
        year_of_review = fdm.get("year_of_review", "Unknown")

        # Query for the element URI
        element_uri = get_element_uri(fdm["global_id"], repository_url, auth)
        if not element_uri:
            raise Exception(f"Element with global_id {fdm['global_id']} not found in repository.")

        # Add triples for the FDM
        triples.append(f'bag_pand:{ref_bag_id} abaronbo:FDM abaronbo:{fdm_id} .')
        triples.append(f'abaronbo:{fdm_id} rdf:type aquo:Waterkering ;')
        triples.append(f'    aquo:TypeWaterkering {translated_type} ;')
        triples.append(f'    aquo:CategorieWaterkering {translated_category} ;')
        triples.append(f'    abaronbo:FDMHeight "{fdm["height"]}"^^xsd:string ;')
        triples.append(f'    abaronbo:FDMWidth "{fdm["width"]}"^^xsd:string ;')
        triples.append(f'    abaronbo:YearOfReview "{year_of_review}"^^xsd:gYear ;')
        triples.append(f'    abaronbo:attachedTo <{element_uri}> .')

    # Combine triples into Turtle format
    turtle_data = "\n".join(triples)

    print("Generated Turtle Data:\n", turtle_data)

    # POST the triples to GraphDB
    response = requests.post(
        f"{repository_url}/statements",
        data=turtle_data,
        headers=headers,
        params=params,
        auth=auth
    )

    if response.status_code == 204:
        return {"status": "success", "message": "Flood defense mechanism triples added successfully."}
    else:
        raise Exception(f"Failed to upload triples. HTTP {response.status_code}: {response.text}")
