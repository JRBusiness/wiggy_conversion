"""
@author: Kuro
"""
from fastapi.logger import logger
from fastapi_cache import caches
from app.shared.middleware.json_encoders import decode_model


class RedisCache:
    """
    `RedisCache` is a class that is used to interact with a Redis cache.
    It contains functions that are used to check if a key exists in the cache,
    put a key-value pair in the cache,
    """

    def __init__(self):
        self.cache = caches.get("CACHE_KEY")

    async def check_cache(self, key):
        """
        This is an asynchronous Python function that checks if a key exists in a cache and returns the decoded model if it does.

        :param key: The key is a unique identifier used to retrieve a specific value from the cache. It is used to check if the value is already stored in the cache or not
        :return: The function `check_cache` returns either a decoded model object or `None`. If the key is found in the cache, it attempts to decode the cached value using the
        `decode_model` function. If decoding is successful, it returns the decoded model object. If decoding fails, it logs the error and returns `None`. If the key is not found in the
        cache, it returns `None`.
        """
        in_cache = await self.cache.get(key)
        if in_cache:
            try:
                model = decode_model(in_cache)
            except TypeError as e:
                logger.info(e)
                model = None
            return model
        return None

    async def put_in_cache(self, key, value, expire_time=None):
        """
        This function puts a key-value pair in a cache and sets an expiration time if specified.

        :param key: The key is a unique identifier for the data that is being stored in the cache. It is used to retrieve the data from the cache when needed
        :param value: The value to be stored in the cache with the given key
        :param expire_time: `expire_time` is an optional parameter that specifies the time-to-live (TTL) for the cached item. It is the amount of time for which the item will remain in
        the cache before it is automatically removed. If `expire_time` is not provided, the item will remain in the cache
        """
        in_cache = await self.check_cache(key)
        if not in_cache:
            await self.cache.set(key, value)
            if expire_time:
                await self.cache.expire(key=key, ttl=expire_time)

    async def get_from_cache(self, cache_key):
        """
        This function checks if data exists in cache and returns it if found, otherwise it returns None.

        :param cache_key: The `cache_key` parameter is a string that represents the unique identifier for the data that is being retrieved from the cache. It is used to check if the
        data is already present in the cache or not
        :return: the data stored in the cache for the given cache key. If there is no data in the cache for the given key, the function will return None.
        """
        cache_data: list = await self.check_cache(cache_key)
        if cache_data:
            logger.info(f"fetching {cache_key} from cache")
            return cache_data
