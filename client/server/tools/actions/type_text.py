# markdown parser that outputs AST (abstract syntax tree) for markdown and can help with converting markdown to keyboard inputs
# import mistune 

# allowed keys json for pyguiauto
# ["\t", "\n", "\r", " ", "!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "^", "_", "`", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~", "accept", "add", "alt", "altleft", "altright", "apps", "backspace", "browserback", "browserfavorites", "browserforward", "browserhome", "browserrefresh", "browsersearch", "browserstop", "capslock", "clear", "convert", "ctrl", "ctrlleft", "ctrlright", "decimal", "del", "delete", "divide", "down", "end", "enter", "esc", "escape", "execute", "f1", "f10", "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19", "f2", "f20", "f21", "f22", "f23", "f24", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "final", "fn", "hanguel", "hangul", "hanja", "help", "home", "insert", "junja", "kana", "kanji", "launchapp1", "launchapp2", "launchmail", "launchmediaselect", "left", "modechange", "multiply", "nexttrack", "nonconvert", "num0", "num1", "num2", "num3", "num4", "num5", "num6", "num7", "num8", "num9", "numlock", "pagedown", "pageup", "pause", "pgdn", "pgup", "playpause", "prevtrack", "print", "printscreen", "prntscrn", "prtsc", "prtscr", "return", "right", "scrolllock", "select", "separator", "shift", "shiftleft", "shiftright", "sleep", "space", "stop", "subtract", "tab", "up", "volumedown", "volumemute", "volumeup", "win", "winleft", "winright", "yen", "command", "option", "optionleft", "optionright"]

import re
import pyautogui
import pyperclip
from utils.logger import logger

async def type_text(text):
    logger.info(f'Typing: {text}')
    text = text = re.sub(r'\t', '    ', text)
    separated_text = re.split(r'(\n)', text)
    
    for line in separated_text:
        if line == '\n':
            pyautogui.press('enter')
        else:
            pyperclip.copy(line)
            pyautogui.hotkey('ctrl', 'v')
            

async def main(**kwargs):
    text = kwargs.get('text')
    logger.info(f'Received text to type: {text}')
    if text is None:
        return {
            'status': 'error',
            'message': 'Missing required argument: text'
        }
    try:
        
        await type_text(text)
        return {
            'status': 'text_typed',
            'message': f'Typed {text}'
        }
    except Exception as e:
        return {
            'status': 'type_text_error',
            'message': f'Error typing text: {e}'
        }
