import requests


_from = "919970059125"
_to = "919880734937"


for i in range(15,15):
    message= "025 %s.21.2013 hello%s"%(i, i)
    data = {"message": message, "from_msisdn": _from, "to_msisdn": _to}
    resp = requests.post("http://localhost:8000/submission", data)
    print resp.text

#for i in range(1,3):
#    message= "001 %s.11.21013"%i
#    data = {"message": message, "from_msisdn": _from, "to_msisdn": _to}
#    resp = requests.post("http://localhost:8000/submission", data)
#    print resp.text