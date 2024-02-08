import webbrowser

def open_website(websiteName):
    url = "https://" + websiteName + ".com"
    webbrowser.open(url, new=2)

async def main(user, websites):
    for site in websites:
        open_website(site)  # Remove 'await' here

    if len(websites) > 1:
        websites_str = ', '.join(websites[:-1]) + ' and ' + websites[-1]
    else:
        websites_str = websites[0]

    return {'response': {
        'type': 'open_website',
        'content': f'Opening {websites_str} in your default browser'
    }}