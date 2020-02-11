import json
import urllib.request as urlreq
import ssl

import certifi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from .models import Bond

GLEIF_URL = "https://leilookup.gleif.org/api/v2/leirecords"


class HelloWorld(APIView):
    def get(self, request):
        return Response("Hello World!")

    def post(self, request):
        print(request.data)
        return Response("<h1>Hello World!</h1>")


class BondAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        # Filtering, only done if parameter and value exist in query
        # and field exist in table
        bond_fields = list(map(lambda f: f.name, Bond._meta.get_fields()))
        filter_params = {
            field: value for field, value in params.items()
            if value and field in bond_fields
        }
        # Fetch user
        user = User.objects.get(username=request.user)
        filter_params["owner"] = user
        q = Bond.objects
        q = q.filter(**filter_params)
        # Project all but id and owner field
        results = q.values(
            "isin", "size",
            "currency", "maturity",
            "lei", "legal_name"
        )
        return Response(results)

    def post(self, request):
        try:
            # Fetch user
            user = User.objects.get(username=request.user)
            input_data = request.data
            BondAPI.check_fields(input_data)
            legal_name = BondAPI.get_legal_name(input_data["lei"])
            # Create and insert bond to DB
            bond = Bond(
                owner=user,
                legal_name=legal_name,
                **input_data
            )
            bond.save()
            return Response(bond.json())
        except KeyError as ke:
            return Response({"msg": str(ke)}, status=400)

    @staticmethod
    def get_legal_name(lei):
        # Query data from GLEIF
        gleif_response = urlreq.urlopen(
            GLEIF_URL+"?lei="+lei,
            context=ssl.create_default_context(cafile=certifi.where())
        )
        # Parse and select lei field
        gleif_data = json.loads(gleif_response.read().decode('utf-8'))
        legal_name = gleif_data[0]["Entity"]["LegalName"]["$"]
        return legal_name

    @staticmethod
    def check_fields(data):
        missing_fields = list()
        for k in ("isin", "size", "currency", "maturity", "lei"):
            if k not in data.keys():
                missing_fields.append(k)

        if len(missing_fields) > 0:
            raise KeyError("Missing fields: "+str(missing_fields))
