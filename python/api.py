import requests


def translate(q):
    url = "https://api.pons.com/v1/dictionary"
    headers = {
        "X-Secret": "3d92e51ea6a1abbcbdc488d8591c14d820337659a5db98325578d05975f56f8c"
    }

    params = {
        "l": "dees",
        "q": q
    }

    response = requests.get(url, headers=headers, params=params)
    target = ""

    if response.status_code == 200:
        response_json = response.json()
        try:
            target = response_json[0]["hits"][0]["target"]
        except KeyError:
            target: str = response_json[0]["hits"][0]["roms"][0]["arabs"][0]["translations"][0]["target"]
        var = target.find("<span")
        if var != -1:
            target = target[0:var].strip()
    else:
        print("api error: request failed with status code:", response.status_code)

    return response.status_code, target
