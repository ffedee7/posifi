import inspect
import json
import logging
import traceback
from functools import partial, wraps

from pythonjsonlogger import jsonlogger

# LOG_LEVEL = "INFO" if settings['STAGE'] == 'prod' else "DEBUG"
LOG_LEVEL = "DEBUG"


class LogFormatter(jsonlogger.JsonFormatter):
    """
    Override of the JSONFormatter that pops up the 'message' field from the logs if it's null
    This is done because all logs written by the logged decorator doesn't have a message field
    """

    def process_log_record(self, log_record):
        """
        Override method to avoid logging a message when there is none
        """
        if log_record.get('message') is None:
            log_record.pop('message')
        return log_record


class PartnersLogger(object):
    """
    Class that encapsulates the system log
    Needed so we can use the AWS Logger that automatically adds the requestId to all logs
    """

    def __init__(self):
        self.logger = logging.getLogger()
        if not self.logger.hasHandlers():
            self.logger.addHandler(logging.StreamHandler())

        log_handler = self.logger.handlers[0]
        formatter = LogFormatter()
        log_handler.setFormatter(formatter)

        self.logger.setLevel(logging.INFO)

        # Set context for the logger
        # This dictionary will hold keys that must be logged for all calls
        # (e.g.: order_id or lu_location_id)
        self.context = {}

    def clear_context(self):
        self.context = {}

    def update_context(self, context):
        self.context.update(**context)

    def debug(self, msg, *args, **kwargs):
        if LOG_LEVEL == 'DEBUG':
            msg = self._contextualize(msg, log_level='DEBUG')
            self.logger.info(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        msg = self._contextualize(msg, log_level='INFO')
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = self._contextualize(msg, log_level='WARNING')
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg = self._contextualize(msg, log_level='ERROR')
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        msg = self._contextualize(msg, log_level='EXCEPTION')
        self.logger.exception(msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg, *args, **kwargs):
        msg = self._contextualize(msg, log_level='CRITICAL')
        self.logger.critical(msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        msg = self._contextualize(msg)
        self.logger.log(level, msg, *args, **kwargs)

    def _contextualize(self, msg, log_level='INFO'):
        if not isinstance(msg, dict):
            msg = {'message': msg, 'log_name': log_level}
        return {
            **{'log_name': log_level},
            **msg,
            **{'context': self.context}
        }


# The maximum length in characters of the logs written by
# the logged decorator when truncate_long_messages is True
MAX_MESSAGE_LENGTH = 500


def logged(method=None, truncate_long_messages=True):
    """
    A decorator that wraps the passed in function and logs exceptions should one occur
    """
    # If called without method, we've been called with optional arguments.
    # We return a decorator with the optional arguments filled in.
    # Next time round we'll be decorating method.
    if method is None:
        return partial(
            logged, truncate_long_messages=truncate_long_messages
        )

    @wraps(method)
    def function(*args, **kwargs):
        args_list = [arg for arg in args]
        full_arg_spec = inspect.getfullargspec(method)
        if full_arg_spec.defaults:
            args_list.extend([default for default in full_arg_spec.defaults])
        parameters = dict(zip(full_arg_spec.args, args_list))
        parameters.update(kwargs)
        parameters.pop('self', '')

        for name, value in parameters.items():
            try:
                value_dumps = json.dumps(value)
            except Exception:
                continue

            if truncate_long_messages and len(value_dumps) > MAX_MESSAGE_LENGTH:
                parameters[name] = f'{value_dumps[:MAX_MESSAGE_LENGTH]} ... truncated'

        try:
            parameters = {
                parameter: value
                for (parameter, value) in parameters.items()
            }
            method_name = f'{method.__name__}'
            method_module = f"{method.__module__.replace('.', '/')}"
            (logger.debug if truncate_long_messages else logger.info)({
                "status": "START",
                "function": method_name,
                "module": method_module,
                "parameters": parameters
            })
            method_result = method(*args, **kwargs)

            log_result = method_result
            if truncate_long_messages:
                try:
                    result_dumps = json.dumps(log_result)
                    if len(result_dumps) > MAX_MESSAGE_LENGTH:
                        log_result = f'{result_dumps[:MAX_MESSAGE_LENGTH]} ... truncated'
                except Exception:
                    pass

            (logger.debug if truncate_long_messages else logger.info)({
                "status": "FINISHED",
                "function": method_name,
                "module": method_module,
                "parameters": parameters,
                "returns": log_result
            })
        except Exception as exception:
            # log the exception
            logger.error({
                "status": "ERROR",
                "function": method_name,
                "module": method_module,
                "parameters": parameters,
                "type": type(exception),
                "message": str(exception),
                "traceback": traceback.format_exc()
            })
            # re-raise the exception
            raise
        return method_result
    return function


# The maximum length in characters of the requests logs to be written by
# the api_logged decorator for the api methods defined in REST_METHODS_TO_TRUNCATE_LOGS
MAX_REQUEST_MESSAGE_LENGTH = 5000


def api_logged(method):
    """
    A decorator that wraps the passed in function and logs exceptions should one occur
    """
    # If called without method, we've been called with optional arguments.
    # We return a decorator with the optional arguments filled in.
    # Next time round we'll be decorating method.
    @wraps(method)
    def api_call(self, request):
        response = method(self, request)

        try:
            # Try to get the name of the function that called the API method by looking 2 levels
            # back on the stack (It's fine since we are using this only for logging purposes)
            operation = inspect.stack()[3].function.replace("_", " ")
            operation = f'{operation} in {self.INTEGRATION}'.upper()
        except Exception:
            operation = None

        try:
            response_content = response.json()
        except Exception:
            response_content = response.text

        body_content = request.json
        if request.method in self.REST_METHODS_TO_TRUNCATE_LOGS:
            try:
                result_dumps = json.dumps(body_content)
                if len(result_dumps) > MAX_REQUEST_MESSAGE_LENGTH:
                    body_content = f'{result_dumps[:MAX_MESSAGE_LENGTH]} ... truncated'
            except Exception:
                pass

            try:
                if len(response.content) > MAX_REQUEST_MESSAGE_LENGTH:
                    response_content = f'{response.content[:MAX_MESSAGE_LENGTH]} ... truncated'
            except Exception:
                pass

        logger.info({
            "operation": operation,
            "status_code": response.status_code,
            "request": {
                "path": request.url.replace(self.base_url, ''),
                "base_url": self.base_url,
                "method": request.method,
                "body": body_content,
                "headers": request.headers
            },
            "response": {
                "body": response_content,
                "headers": dict(response.headers)  # type(response.headers) is CaseInsensitiveDict
            },
            "meta": {
                "integration": self.INTEGRATION,
                "elapsed_time": response.elapsed.total_seconds() if response.elapsed else None
            },
        })

        return response
    return api_call

# The logger instance to be used across the system
logger = PartnersLogger()