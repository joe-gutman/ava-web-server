import webbrowser
import asyncio
from utils.logger import logger

def open_websites(websiteName):
    url = "https://" + websiteName + ".com"
    webbrowser.open(url, new=2)

async def main(**kwargs):
    websites = kwargs.get('websites')
    if websites is None:
        return {
            'status': 'error', 
            'message': 'Missing required argument: websites'
        }

    try: 
        logger.info(f"Opened {websites}")
        for site in websites:
            logger.info(f"Opened {site}")
            open_websites(site)  # Remove 'await' here
            await asyncio.sleep(.2) #delay to make sure website opens before opening the next one

        if len(websites) > 1:
            websites_str = ', '.join(websites[:-1]) + ' and ' + websites[-1]
        else:
            websites_str = websites[0]

        return { 
            'data': {
                'type': 'open_website',
                'content': f'Opened {websites_str} '
            }   
        }
    except Exception as e:
        logger.error(f"Error opening websites: {e}")
        return {'response': {
            'type': 'open_website_error',
            'content': f'Error opening websites: {e}'
        }}