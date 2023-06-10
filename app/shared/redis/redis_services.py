"""
@author: Kuro
"""
from typing import Any

from py_linq import Enumerable
from redis_om import JsonModel, EmbeddedJsonModel


class Query(Enumerable):
    __abstract__ = True

    def where(self, *args, filter_arg=None, **kwargs):
        expr = lambda x: all(getattr(x, key) == value for key, value in kwargs.items())
        filter_arg = filter_arg or expr
        # need to convert kwargs lookup: arg=value to lamba expression: lambda x: x.arg == value
        return super().where(filter_arg)


class RedisMixin(JsonModel):
    @classmethod
    def filter_expr(cls, **filters: dict) -> list:
        """
        The filter_expr function takes a class and filters as keyword arguments.
        It returns a list of expressions that can be used to filter the class by the given filters.
        For example, if you have an Employee model with first_name and last_name attributes,
        you could use this function to generate an expression like:

        Args:
            cls: Specify the class that is being filtered
            **filters: dict: Pass a dictionary of filters to the function

        Returns:
            A list of expressions

        """
        return [getattr(cls, key) == value for key, value in filters.items()]

    @classmethod
    def query(cls, enumerable: list, **filters: Any) -> Query:
        """
        The query function is a class method that returns a Query object.
        It takes an enumerable and filters as arguments, and it uses the filter_expr function to create the where clause of the query.


        Args:
            cls: Access the class attributes
            enumerable: Any: Specify the type of enumerable that will be passed in
            **filters: Any: Pass in a dictionary of filters

        Returns:
            A query object
        """
        return Query(enumerable)


class JsonMixin(EmbeddedJsonModel):
    """
    The JsonMixin class is a class that represents a JSON mixin.
    """


#
# class RedisController(RedisMixin):
#     #
#     # @classproperty
#     # def filterable_attributes(cls) -> List[str]: ...
#     #
#     #
#     # @classproperty
#     # def sortable_attributes(cls) -> List[str]: ...
#
#
#
#
# @classmethod
# def order_expr(cls_or_alias, *columns: str) -> list: ...
