import webbrowser
import asyncio
from utils.logger import logger

def open_subreddits(subreddit_name):
    url = "https://reddit.com/r/" + subreddit_name
    webbrowser.open(url, new=2)

async def main(**kwargs):
    subreddits = kwargs.get('subreddits')
    if subreddits is None:
        return {
            'status': 'error', 
            'message': 'Missing required argument: subreddits'
        }

    try: 
        logger.info(f"Opened {subreddits}")
        for site in subreddits:
            logger.info(f"Opened {site}")
            open_subreddits(site)  # Remove 'await' here
            await asyncio.sleep(.2) #delay to make sure website opens before opening the next one

        if len(subreddits) > 1:
            subreddits_str = ', '.join(subreddits[:-1]) + ' and ' + subreddits[-1]
        else:
            subreddits_str = subreddits[0]

        return { 
            'data': {
                'type': 'open_subreddit',
                'content': f'Opened {subreddits_str} '
            }   
        }
    except Exception as e:
        logger.error(f"Error opening subreddits: {e}")
        return {'response': {
            'type': 'open_subreddit_error',
            'content': f'Error opening subreddits: {e}'
        }}