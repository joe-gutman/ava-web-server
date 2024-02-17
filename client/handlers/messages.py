import aiohttp
from utils.logger import logger
from utils.text_to_speech import text_to_speech as tts


class MessageHandler:
    @staticmethod
    def speak(text):
        logger.info(f'Speeking: {text}')
        tts(text)

    @staticmethod
    async def send_message(message):
        try: 
            async with aiohttp.ClientSession() as session:
                async with session.post(f'http://localhost:5000/messages/{message.user_id}', json=message.data) as response:
                    logger.info('Sending request...')
                    response = json.loads(await response.text())
                    logger.debug(f"Response: {response}")
                    return response
        except Exception as e:
            logger.error(f'Error in send_request: {e}')
            return None
            
    @staticmethod
    async def handle_response(self, message):
        try:
            response = await self.send_request(message)
            if response:
                status = response['status']
                type = response['data']['type']
                if status == 'success' and type == 'text':
                    response_text = response['data']['content']
                    logger.info(f'Response: {response_text}')
                    self.speak(response_text)
                else:
                    logger.error(f'Error in response: {response["message"]}')
            else:
                logger.error(f'Error in response')
        except Exception as e:
            logger.error(f'Error in send_tool_response: {e}')
            return None
