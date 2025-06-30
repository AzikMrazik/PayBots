import logging
import glob
import os
import importlib

ACTIVE_SYSTEMS = []

async def load_systems():
    global ACTIVE_SYSTEMS
    files = glob.glob(os.path.join("modules", "paysystem_*.py"))
    if not files:
        logging.warning("No systems found in the modules directory.")
        return
    for module in files:
        try:
            module = module.split("_")[1].replace(".py", "")
            ACTIVE_SYSTEMS[module] = module
            if await load_module(module):
                logging.info(f"System {module} loaded successfully.")
            else: 
                logging.warning(f"System {module} could not be loaded.")
                raise Exception(f"System {module} could not be loaded.")
        except Exception as e:
            logging.error(f"Error loading system {module}: {e}")
            continue

async def load_module(module: str):
    try:
        module = importlib.import_module(f"modules.paysystem_{module}")
        settings = module.settings
        if not settings:
            logging.error(f"Settings for system {module} are not defined.")
            return False
        try:
            name = settings.get("name")
            comission = settings.get("commission", 1)
            command = settings.get("command", module)
            custom_template = settings.get("custom_template", False)
            custom_order_id = settings.get("custom_order_id", False)
            link_type = settings.get("link_type", False)
            custom_headers = settings.get("custom_headers", False)
            callback_type = settings.get("callback_type", "json")
            secrets = settings.get("secrets")
        except Exception as e:
            logging.error(f"Error in settings for system {module}: {e}")
            return False
        ACTIVE_SYSTEMS[module] = {
            "name": name,
            "commission": comission,
            "custom_template": custom_template,
            "command": command,
            "custom_order_id": custom_order_id,
            "link_type": link_type,
            "custom_headers": custom_headers,
            "callback_type": callback_type,
            "secrets": secrets
        }
        return True
    except ImportError as e:
        logging.error(f"Failed to import module {module}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error while loading module {module}: {e}")
        return False