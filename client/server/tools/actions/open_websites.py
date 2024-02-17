import webbrowser
import asyncio
from utils.logger import logger

def open_websites(websiteName):
    url = "https://" + websiteName + ".com"
    webbrowser.open(url, new=2)

async def main(websites):
    try: 
        logger.info(f"Opening {websites} in your default browser")
        for site in websites:
            logger.info(f"Opening {site} in your default browser")
            open_websites(site)  # Remove 'await' here
            await asyncio.sleep(1) #delay to make sure website opens before opening the next one

        if len(websites) > 1:
            websites_str = ', '.join(websites[:-1]) + ' and ' + websites[-1]
        else:
            websites_str = websites[0]

        return {'response': {
            'type': 'open_website',
            'content': f'Opening {websites_str} in your default browser'
        }}
    except Exception as e:
        logger.error(f"Error opening websites: {e}")
        return {'response': {
            'type': 'open_website',
            'content': f'Error opening websites: {e}'
        }}