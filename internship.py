import requests


def queryInternship(query, pos):

    response = requests.get(f'https://www.levels.fyi/js/internshipData.json')
    results = [x for x in response.json() if x['company'].lower() == query.lower()]
    text = ""
    try:
        for i in results[pos:pos+5]:
            text += f"""{i['company']}, {i['season']} {i['yr']}
                        Location: {i['loc']}
                        Pay: {i['hourlySalary']}/hr or {i['monthlySalary']}"
                        More info: {i['moreInfo']}\n"""
    except:
        text = "No results found"
    return text

print(queryInternship("google", 0))
