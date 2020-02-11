import json
import urllib.request as urlreq
import ssl

import certifi
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Bond

GLEIF_URL = "https://leilookup.gleif.org/api/v2/leirecords"

class HelloWorld(APIView):
    def get(self, request):
        return Response("Hello World!")

    def post(self, request):
        print(request.data)
        return Response("<h1>Hello World!</h1>")

class BondAPI(APIView):
    def get(self, request):
        params = request.query_params
        # Filtering, only done if parameter and value exist in query
        # and field exist in table
        bond_fields = list(map(lambda f: f.name, Bond._meta.get_fields()))
        filter_params = {
            field: value for field, value in params.items()
            if value
            and field in bond_fields
        }
        q = Bond.objects
        q = q.filter(**filter_params)
        # Project all but id field
        results = q.values(
            "isin", "size",
            "currency", "maturity",
            "lei", "legal_name"
        )
        return Response(results)

    def post(self, request):
        input_data = request.data
        # Query data from GLEIF
        gleif_response = urlreq.urlopen(
            GLEIF_URL+"?lei="+input_data["lei"],
            context=ssl.create_default_context(cafile=certifi.where())
        )
        # Parse and select lei
        gleif_data = json.loads(gleif_response.read())
        legal_name = gleif_data[0]["Entity"]["LegalName"]["$"]
        # Create and insert bond
        bond = Bond(
            isin=input_data["isin"],
            size=input_data["size"],
            currency=input_data["currency"],
            maturity=input_data["maturity"],
            lei=input_data["lei"],
            legal_name=legal_name
        )
        bond.save()
        return Response(bond.json())
