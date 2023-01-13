import requests


def queryInternship(query, pos):
    response = requests.get(f'https://www.levels.fyi/js/internshipData.json')
    results = [x for x in response.json() if 'company' in x and x['company'].lower() == query.lower()]
    text = ""
    try:
        for i in results[pos:min(pos+3, len(results))]:
            text += f"""- {i.setdefault('company', 'N/A')}, {i['season']} {i['yr']}
                        Location: {i.setdefault('loc', 'N/A')}
                        Pay: {i['hourlySalary']}/hr or {i['monthlySalary']}/month
                        More info: {i.setdefault('moreInfo','N/A')}\n\n"""
    except:
        text = "Error handling request"
    if text == "":
        text = "No results found"
    return text

response = requests.get(f'https://www.levels.fyi/js/internshipData.json')
j = response.json()


print(queryInternship("facebook", 0))