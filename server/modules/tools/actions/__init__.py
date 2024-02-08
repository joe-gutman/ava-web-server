import os
import importlib.util
from utils.logger import logger

import os
import importlib.util
from utils.logger import logger

def import_all_modules_in_directory(directory):
    main_functions = {}
    for filename in os.listdir(directory):
        logger.info(f"Checking file: {filename}")
        if filename.endswith('.py') and filename != '__init__.py':
            logger.info(f"Importing module: {filename}")
            module_name = filename[:-3]  # remove the .py extension
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(directory, filename))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'main'):
                main_functions[module_name] = module.main
                logger.info(f"Added main function from module: {module_name}")
            else:
                logger.warning(f"No main function found in module: {module_name}")
    logger.info(f"Main functions: {main_functions}")
    return main_functions

# Import the main function from all modules in the current directory
main_functions = import_all_modules_in_directory(os.path.dirname(__file__))
globals().update(main_functions)