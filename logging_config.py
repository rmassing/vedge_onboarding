#  ----------------------------------------------------------------
# Copyright 2016 Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------

import logging
from logging.config import dictConfig
import os

def configure_logger(name, log_path):

    onboarding_log_path = os.path.abspath(os.curdir) + "/logs/viptela_onboarding.log"
    eman_log_path = os.path.abspath(os.curdir) + "/logs/ete_lib.log"

    if os.path.isdir("logs") is False:
        os.mkdir("logs")

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': "%(asctime)s %(levelname)-5s [%(filename)s:%(lineno)d] %(message)s"
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'eman': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'filename': eman_log_path,
                'maxBytes': 10*1024*1024,
                'backupCount': 3
            },
            'onboarding': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'filename': onboarding_log_path,
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            }
        },
        'loggers': {
            # '': {
            #     'level': 'INFO',
            #     'handlers': ['console', 'file']
            # },
            '__main__': {  # if __name__ == '__main__'
                'handlers': ['console', 'onboarding'],
                'level': 'DEBUG',
                'propagate': False
            },
            'eman': {
                'handlers': ['console', 'eman'],
                'level': 'INFO',
                'propagate': False
            },
            'onboarding': {
                'handlers': ['console', 'onboarding'],
                'level': 'INFO',
                  'propagate': False
            }
        },
    })
    return logging.getLogger(name)

if __name__ == "__main__":
    # dictConfig(LOGGING)
    # logger = logging.getLogger(__name__)

    log_path = os.path.abspath(os.curdir) + "/logs/log_testing.log"
    logger = configure_logger(log_path)

    logger.debug('debug message!')
    logger.info('info message!')
    logger.error('error message')
    logger.critical('critical message')
    logger.warning('warning message')