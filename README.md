# BIM-GIS_2.0

This repository contains the source code of the latest version of BIM-GIS 2.0. For a detailed installation guide, please visit [BIM-GIS](https://github.com/abaronbo/BIM-GIS/). The project consists of two main components: A platform based on Django and an web-based IFC viewer. 

## Django

The web platform contains four main applications, which are:

**Login:** Manages authentication and role-based access control.

**Cesiumapp:** Provides the city viewer for building selection and interaction.

**SPARQL-filter:** Handles federated queries across multiple databases.

**IFCUpload:** Manages IFC file uploads, RDF conversion, and FDM definitions.

### Step 1
Clone this GitHub Repository by executing the following command:

`git clone https://github.com/abaronbo/BIM-GIS_2.0`

### Step 2
Install the requirements by executing the following command:

`pip install -r requirements.txt`

### Step 3
Create a Cesium account and get an access token. A detailed tutorial is available [here.](https://cesium.com/learn/cesiumjs-learn/cesiumjs-quickstart/)

### Step 4
Create a GraphDB account, or you can use another triplestore. A detailed tutorial is available [here.](https://graphdb.ontotext.com)

### Step 5
Define the correct login credentials.

`BIM-GIS_2.0/django/cesiumapp/templates/cesium.html`

Replace the text "YOUR ACCESS TOKEN" found in line 365 with your actual access token.

`BIM-GIS_2.0/django/cesiumapp/templates/municipality_cesium.html`

Replace the text "YOUR ACCESS TOKEN" found in line 620 with your actual access token.

`BIM-GIS_2.0/django/ifcupload/add_triples.py`

1. Replace the text "url" found in line 54 with the URL of your GraphDB repository.
2. Define your "User" and "Password" found in line 56 with the URL of your GraphDB repository.

`BIM-GIS_2.0/django/sparql_filter/views.py`
1. Replace the text "url" found in line 36 with the URL of the (external) endpoint where the cadastral data is hosted.
2. Define your "User" and "Password" found in line 156 with the URL of your GraphDB (or external) repository.
3. Replace the text "url" found in line 170 with the URL of your GraphDB repository.
4. Define your "User" and "Password" found in line 269 with the URL of your GraphDB repository.

### Step 6
Navigate to `django` and start the project. A detailed Django tutorial is available [here.](https://www.w3schools.com/django/django_intro.php)

## IFC Viewer

The IFC viewer was developed using the Typescript libraries of [That Open Company.](https://docs.thatopen.com/intro). The complete documentation, instructions, and required dependencies can be found [here.](https://docs.thatopen.com/components/getting-started). 

The main file of the IFC viewer is located in:
`BIM-GIS_2.0/my-3d-world/src/main.ts`






