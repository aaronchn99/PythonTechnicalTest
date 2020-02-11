import json
import random
import string
import copy
import time

with open("currency.json", "r", encoding="utf-8") as f:
	data = json.load(f)
	currencies = list(data.keys())

with open("lei_list.json", "r", encoding="utf-8") as f:
    legal_entities = json.load(f)

def random_date():
    format = "%Y-%m-%d"
    start = "2000-01-01"
    end = "2100-01-01"
    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))
    ptime = stime + random.random() * (etime - stime)
    date = time.strftime(format, time.localtime(ptime))
    return date

def random_isin():
    return  "".join(random.choice(string.ascii_uppercase) for _ in range(2)) + "".join(random.choice(string.digits) for _ in range(10))

data = list()

for _ in range(2):
    for i in range(len(legal_entities)):
        bond_in = {
            "isin": random_isin(),
            "size": random.randint(100, 10000000000),
            "currency": random.choice(currencies),
            "maturity": random_date(),
            "lei": legal_entities[i][0]
        }
        bond_out = copy.deepcopy(bond_in)
        bond_out["legal_name"] = legal_entities[i][1]
        
        data.append({"input": bond_in, "exp_output": bond_out})

with open("test_bonds.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(data))
