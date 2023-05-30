"""
@author: Kuro
"""
import json
import datetime
from uuid import UUID
import dateutil.parser
from fastapi.logger import logger


def datetime_parser(json_dict):
    """
    The datetime_parser function attempts to parse any datetime strings in the JSON object.
    If a datetime string is successfully parsed, it is replaced with a Python datetime object.

    :param json_dict: Used to Pass the json_dict to be parsed.
    :return: A dictionary with the datetime objects.
    """
    for key, value in json_dict.items():
        try:
            json_dict[key] = dateutil.parser.parse(value)
        except (ValueError, AttributeError):
            pass
    return json_dict


class ModelEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        The default function is used to serialize objects that are not natively
        serializable by the JSON encoder. This function will be called on any object
        that is passed to the json.dumps() method.

        :param self: Used to Access variables that belongs to the class.
        :param obj: Used to Pass in the object to be serialized.
        :return: None.


        """
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return str(obj)
        return (
            None
            if isinstance(
                obj,
                (object),
            )
            else json.JSONEncoder.default(self, obj)
        )


class _JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        The default function is used to serialize objects that are not natively
        serializable by the JSON encoder. This function will be called on objects
        that are not serializable.

        :param self: Used to Access the attributes and methods of the class.
        :param obj: Used to Pass in the object that is being serialized.
        :return: The object itself.


        """
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def decode_model(cache_data):
    """
    The decode_model function takes a dictionary of the form returned by the
    encode_model function and converts it back to a list of dictionaries. This is
    useful for debugging, but also necessary when calling functions that expect an
    encoded model.

    :param cache_data: Used to Retrieve the data from the cache.
    :return: A list of dictionaries.
    """
    jdata = json.loads(cache_data)
    if any(isinstance(i, dict) for i in jdata.values()):
        data = list(jdata)
        return list(data)
    return jdata


class ModelDecoder(json.JSONDecoder):
    def default(self, obj):
        """
        The default function is used to serialize objects that do not have a
        serialize method. It serializes the object using json.dumps.

        :param self: Used to Reference the class itself.
        :param obj: Used to Pass in the object that is being encoded.
        :return: The object itself.


        """
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return str(datetime)
        if isinstance(obj, dict):
            obj["timestamp"] = str(obj["timestamp"])
        return json.JSONDecoder.default(self, obj)


class _JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        """
        The __init__ function is called when an instance of the class is created.
        It initializes all of the variables in a class and prepares them for use.

        :param self: Used to Reference the class instance itself.
        :param *args: Used to Send a non-keyworded variable length argument list to the function.
        :param **kwargs: Used to Pass a keyworded, variable-length argument list.
        :return: The object itself.


        """
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        """
        The object_hook function is used to convert the JSON object into a Python dictionary.
        The datetime and date objects are converted from ISO format strings to Python datetime objects.

        :param self: Used to Reference the class itself.
        :param obj: Used to Pass in the dictionary that is being decoded.
        :return: A dictionary of the key value pairs in the object.


        """
        return {
            key: datetime.datetime.fromisoformat(value)
            if isinstance(obj, (datetime.datetime, datetime.date))
            else value
            for key, value in obj.items()
        }


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        The default function is used to serialize objects that are not natively
        serializable by the JSON encoder. This function will be called on objects
        that aren't natively serializable by the encoder. The default function will
        be passed the object to convert and should return a serialized representation
        of that object.

        :param self: Used to Access variables that belongs to the class.
        :param obj: Used to Pass in the object to be serialized.
        :return: The default value for the object type.


        """
        if isinstance(obj, datetime.datetime):
            return str(obj)
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class CustomJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        """
        The __init__ function is called when an instance of the class is created.
        It initializes all of the variables in the class and prepares them for use.

        :param self: Used to Refer to the object itself.
        :param *args: Used to Send a non-keyworded variable length argument list to the function.
        :param **kwargs: Used to Specify any keyword arguments that are not defined by the function.
        :return: A reference to the newly created object.


        """
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @classmethod
    def object_hook(cls, source):
        """
        The object_hook function is used to convert the JSON string into a Python object.
        The datetime module is used to parse the date strings and convert them into a format that can be manipulated by Python.

        :param cls: Used to Pass the class of the object being created.
        :param source: Used to Pass the json object to be parsed.
        :return: The source dictionary.


        """
        for k, v in source.items():
            if isinstance(v, str):
                try:
                    source[k] = datetime.datetime.strptime(
                        str(v), "%a, %d %b %Y %H:%M:%S %Z"
                    )
                except Exception as e:
                    logger.info(e)

        return source
