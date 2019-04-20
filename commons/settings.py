import os
import json

from pathlib import Path
from commons.logger import logger


# =========== temporal fix to SSM Parameter Store concurrency issue ========== #
# Get all the settings from SSM
def _get_settings_from_local_file(file_name='settings.json'):
    logger.info('Loading settings from local file...')

    file_path = Path(__file__).parent / file_name
    loaded_settings = {}
    if file_path.exists() and file_path.is_file():
        with file_path.open() as file:
            loaded_settings.update(json.load(file))
    else:
        logger.error(f'Failed loading {file_path.absolute()} file')

    return loaded_settings['parameters']


# Get all the settings from SSM
settings = _get_settings_from_local_file()

# logging commit_hash and stage-params
commit_hash = settings.get('commit_hash')
if commit_hash:
    logger.info(
        f'Running commit: {commit_hash} and loaded params for stage:{os.environ.get("stage")}'
    )
else:
    logger.info('No commit hash on settings')

# Add environment variables comming from serverless

# Service ID
settings['SERVICE'] = os.environ.get('serviceId')

# Stage
settings['STAGE'] = os.environ.get('stage')
