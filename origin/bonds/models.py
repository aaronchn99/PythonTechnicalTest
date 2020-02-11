from django.db import models
import json


class Bond(models.Model):
    isin = models.CharField(max_length=12)
    size = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    maturity = models.DateField()
    lei = models.CharField(max_length=20)
    legal_name = models.CharField(max_length=30)

    def json(self):
        obj = {
            "isin": self.isin,
            "size": self.size,
            "currency": self.currency,
            "maturity": self.maturity,
            "lei": self.lei,
            "legal_name": self.legal_name
        }
        return json.dumps(obj)
