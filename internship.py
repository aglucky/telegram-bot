import requests


def queryInternship(query, pos):

    response = requests.get(f'https://www.levels.fyi/js/internshipData.json')
    results = [x for x in response.json() if x['company'].lower() == query.lower()]
    text = ""
    try:
        for i in results[pos:min(pos+3, len(results)-1)]:
            text += f"""- {i['company']}, {i['season']} {i['yr']}
                        Location: {i['loc']}
                        Pay: {i['hourlySalary']}/hr or {i['monthlySalary']}"
                        More info: {i['moreInfo']}\n\n"""
    except:
        text = "Error handling request"
    if text == "":
        text = "No results found"
    return text

print(queryInternship("ffffsa", 10))
