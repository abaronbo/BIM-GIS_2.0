# BIM-GIS_2.0

This repository contains the source code of the latest version of BIM-GIS 2.0. For a detailed installation guide, please visit [BIM-GIS](https://github.com/abaronbo/BIM-GIS/). The project consists of two main components: A platform based on Django and an web-based IFC viewer. 

## Django

The web platform contains three main applications, which are:

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


