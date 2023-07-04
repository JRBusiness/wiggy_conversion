"""
@author: Kuro
"""
import contextlib
import logging
import math
import uuid
from datetime import datetime, timedelta
from enum import Enum
from operator import or_
from random import randint, choice
from types import SimpleNamespace
from typing import Type, Union, Tuple, List, Any, Generic
from typing import TypeVar

import pytz
from faker import Faker
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from sqlalchemy import (
    and_,
    create_engine,
    MetaData,
    DateTime,
    Float,
    String,
    Integer,
    Boolean,
    Interval,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry, sessionmaker, Query
from sqlalchemy_mixins import AllFeaturesMixin
from sqlalchemy_mixins.activerecord import ActiveRecordMixin
from sqlalchemy_mixins.inspection import InspectionMixin
from sqlalchemy_mixins.smartquery import SmartQueryMixin
from starlette.requests import Request
from app.shared.auth.password_handler import verify_password
from app.shared.exception.exceptions import PredicateConditionException
from app.shared.schemas.ResponseSchemas import BaseResponse
from app.shared.schemas.page_schema import PagedResponse
from settings import Config
from settings import base_dir

ModelType = TypeVar("ModelType", bound=AllFeaturesMixin)
T = TypeVar("T")

mapper_registry = registry()
DeclarativeBase = declarative_base()
# Base = mapper_registry.generate_base(
#     cls=AllFeaturesMixin
# )
#


class UserTypeEnum(Enum):
    """
    The UserTypeEnum is used to define the different types of users that can be created.
    """

    admin = "admin"
    agent = "agent"
    user = "user"


class ModelMixin(AllFeaturesMixin):
    """
    Generic Mixin Model to provide helper functions that all Model classes need
    """

    __abstract__ = True

    @classmethod
    def get_or_create(cls: ModelType, *_, **kwargs) -> ModelType:
        """
        The get_or_create function is a helper function that will
        either get an object or create it if it doesn't exist.
        For example, let's say we have a model called User with two
        fields: name and email.
        We want to be able to easily create new users based on their
        name and email address, but we also
        want our API endpoints (and other parts of our code) to check
        whether a user already exists before creating them.

        :param cls:ModelType: Used to Specify the model class that will
         be used to create or retrieve an instance.
        :param *_: Used to Ignore the first positional argument.
        :param **kwargs: Used to Pass in all the fields of the model.
        :return: A tuple containing the object and a boolean value indicating whether it was created.
        """
        try:
            if not cls.find(kwargs.get("id")):
                _object = cls(**kwargs)
                cls.session.add(_object)
                cls.session.commit()
                return _object
        except Exception as e:
            cls.session.rollback()
            logger.error(e)
            return

    @classmethod
    def map_to_model(cls, model: Type[BaseModel], db_response: Union[Row, List[Row]]):
        """
        The map_to_model function takes a model and a list of tuples,
        and returns the same list of tuples with each tuple converted into an instance
        of the given model. For example:

            map_to_model(User, [('user-id', 'username'), ('user-id2', 'username2')])
            # Returns [User(user_id='user-id', username='username'), User(...)]

        :param model:Type[BaseModel]: Used to Specify the model that is used to create a list of instances.
        :param db_response:Union[Row: Used to Determine if the db_response is a list of keyed tuples or just one.
        :param List[Row]]: Used to Check if the db_response is a list of keyed tuples.
        :return: An instance of the model class with properties mapped to value from the db_response.
        """

        def mapper(tuple_data: Row) -> BaseModel:
            """
            The mapper function takes a tuple of data which is keyed and returns a dictionary.

                {'id': '<id>', 'name': '<name>', ...}

            Each key-value pair in this returned dictionary corresponds to one column
            in the database schema

            :param tuple_data:Row: Used to Pass in the data that is being mapped.
            :return: A dictionary with the key being the name of the column, and the value the row
            """
            zipped_tuples = dict(zip(tuple_data.keys(), tuple_data))
            return model(**zipped_tuples)

        if isinstance(db_response, list):
            return [mapper(item) for item in db_response]
        return mapper(db_response)

    @classmethod
    def rebuild(cls, kwargs: dict) -> dict:
        """
        The rebuild function takes a dictionary of data and returns a new dictionary
        with the following changes:
            - The created_at field is set to the current time.
            - If an id value is not provided, one will be generated.

            Args:
                kwargs (dict): A dictionary of data to rebuild into a model instance.

            Returns:
                dict: A rebuilt model instance with all fields updated and any missing ids added.

        :param kwargs:dict: Used to Pass in the dictionary of arguments that is being passed into the function.
        :return: A dictionary.
        """
        timestamp = datetime.now(pytz.utc)
        new_kwargs = dict(kwargs)
        new_kwargs["created_at"] = timestamp
        return new_kwargs

    @classmethod
    def build_filters(cls, kwargs: dict, constraints: list = None) -> dict:
        """
        The build_filters function takes a dictionary of keyword arguments and returns a dictionary of
        filters that can be used to query the database. The returned filters are constrained by the
        keyword arguments passed in, which are also used as the keys for the returned filters. If no
        constraints are provided, all keyword arguments will be used as constraints.

        :param kwargs:dict: Used to Pass in the dictionary of parameters that we want to filter on.
        :param constraints:list=None: Used to Specify which constraints to apply.
        :return: A dictionary of filters.
        """
        if not constraints:
            constraints = list(kwargs.keys())
        return {k: v for k, v in kwargs.items() if k in constraints}

    @classmethod
    def get_owner_context(
        cls, request: Request, context: BaseModel
    ) -> Tuple[UUID, dict]:
        """
        The get_owner_context function accepts a request and context object as arguments.
        It returns the ownerId of the user making the request, and a dictionary containing
        the values from the context object that are not None or empty strings.

        :param request:Request: Used to Get the user id of the current logged-in user.
        :param context:BaseModel: Used to Get the fields of the model that are not none or empty strings.
        :return: The ownerId of the user making the request, and a dictionary containing.
        """
        ownerId: int = request.user.id
        context_dict = context.dict(exclude_unset=True)
        context_dict["ownerId"] = ownerId
        return ownerId, context_dict

    @classmethod
    def get_kwarg_dependencies(cls, kwargs):
        """
        The get_kwarg_dependencies function takes a dictionary of keyword arguments and removes any keyword
        arguments that do not contain an _id field, which is the default requirement of any user identity object.

        :param kwargs: Used to Store the arguments passed to a function.
        :return: A list of the dependencies for a given kwarg.
        """
        return [k for k in list(kwargs.keys()) if "_id" in k]

    @staticmethod
    def get_id_args(cls, *_, **kwargs):
        return {k: v for k, v in kwargs.items() if v and "_id" in k}

    @staticmethod
    def check_many_conditions(
        _or_: Union[list, dict] = None, _and_: list = Union[list, dict]
    ):
        """
        The check_many_conditions function checks to see if the conditions are met.
        It takes two arguments, _or_ and _and_. If both arguments are lists, it checks to see if
        either of the conditions in the list is true. If only one argument is a list, it checks
        to see if all the conditions in that list are true. If neither argument is a list, then
        check_many_conditions returns the input in a dictionary format

        :param _or_:Union[list: Used to Define a list of conditions that are all required to be true.
        :param dict]=None: Used to Check if the _or_ parameter is a list.
        :param _and_:list=Union[list: Used to Make sure that the _and_ parameter is a list.
        :param dict]: Used to Store the conditions that are to be checked.
        :return: A dictionary with the keys being the _and_ conditions and values being either a list of _or_
                conditions or a single _or_ condition.

        """

        if isinstance(_and_, list) and isinstance(_or_, list):
            raise PredicateConditionException

        if isinstance(_or_, list):
            return {and_: _or_}
        if isinstance(_and_, list):
            return {or_: _and_}
        return {or_: _and_ or _or_, and_: _or_ or _and_}

    @staticmethod
    def get_constraints(kwargs, constraints: List[str]):
        """
        It takes a dictionary of keyword arguments and a list of constraints, and returns a SimpleNamespace object with only the keys that are in the constraints list

        :param kwargs: The keyword arguments passed to the function
        :param constraints: A list of strings that represent the constraints that you want to be able to pass in
        :type constraints: List[str]
        :return: A SimpleNamespace object with the keys and values of the kwargs dictionary.
        """
        return {k: v or None for k, v in kwargs.items() if k in constraints}

    @classmethod
    def build_response(
        cls: ModelType = None,
        object_data: Any = None,
        error: str = None,
    ) -> BaseResponse:
        """
        The build_response function takes a list of database objects and returns a dictionary with the following structure:

        "success": True, or False if no data was returned from the database.
        "<Model Name>": [<database object>] The actual data that was returned from the database.
        :param overload: custom dictionary to overload the response with
        :param error: Custom Error message if any
        :param object_data: Optional data to include in the response
        :param cls: Used to Access variables that belongs to the class.
        :return: A dictionary with a key of success and the data.
        """

        if cls and error is None and object_data:
            return BaseResponse(success=True, response=object_data)
        return BaseResponse(
            success=False,
            error=error
            or f"unable to perform crud operation on {cls.__name__ or 'object'}",
        )

    @classmethod
    def user_claims(cls, *_, **kwargs) -> "UserClaim":
        """
        > This function takes a user_id and returns a UserClaim object

        :param user_email:  The user's email address
        :param cls: The class of the model that we're using
        :return: A UserClaim object with the user's id and email.
        """
        password = kwargs.get("password")
        filters = cls.get_constraints(kwargs, ["email", "phone"])
        user_lookup: ModelType = cls.read(**filters)
        if user_lookup and verify_password(password, user_lookup.password):
            keys = dict(id=user_lookup.id, username=user_lookup.username)
            keys[
                filters.get("email") and "email" or filters.get("phone") and "phone"
            ] = (
                filters.get("email")
                and user_lookup.email
                or filters.get("phone")
                and user_lookup.phone
            )
            return UserClaim()

    @classmethod
    def create(cls, *_, **kwargs) -> ModelType:
        """
        It takes a class, and a dictionary of arguments, and creates a new
        object of that class with the arguments

        :param cls: The class that the method is being called on
        :return: The id of the new object
        """
        object_data = cls.rebuild(kwargs)
        new_object = cls(**object_data)
        try:
            if cls.where(**object_data).first():
                return
            cls.session.add(new_object)
            cls.session.commit()
            return new_object
        except Exception as e:
            logger.debug(e)
            cls.session.rollback()
            return

    @classmethod
    def update(cls, *_, **kwargs) -> Query:
        """
        > Update an object in the database and return a response object

        :param cls: The class that inherits from BaseModel
        :return: The updated object.
        """
        filters = {
            k: v
            for k, v in kwargs.items()
            if k
            in [
                "id",
                "ownerId",
                "agentId",
                "adminId",
                "userId",
                "createdByAdminId",
                "createdByAgentId",
            ]
        }
        for key in filters:
            kwargs.pop(key)
        kwargs["updated_at"] = datetime.now(pytz.utc)
        try:
            updated_data = cls.where(**filters)
            updated_data.update(kwargs)
            cls.session.commit()
            return updated_data
        except Exception as e:
            logger.error(e)
            cls.session.rollback()
            return

    @classmethod
    def remove(cls, *_, **kwargs) -> BaseResponse:
        """
        > This function deletes an object from the database

        :param cls: The class of the model that is being used
        :return: The id of the deleted object.
        """
        object_id = kwargs.get("id")
        try:
            delete = cls.where(id=object_id).delete()
            return delete
        except Exception as e:
            logger.error(e)
            cls.session.rollback()
            return

    @classmethod
    def list_all(cls, page: int, num_items: int) -> PagedResponse:
        """
        > This function returns a list of all users in the database, paginated by the page and number of items per page

        :param cls: The class that the method is being called on
        :param page: The page number to return
        :type page: int
        :param num_items: The number of items to return per page
        :type num_items: int
        :return: A PagedBaseResponse object.
        """
        try:
            objects = cls.where()
            return paginate(objects, page, num_items)
        except Exception as e:
            logger.error(e)
            cls.session.rollback()
            return

    @classmethod
    def read(cls, **kwargs) -> ModelType:
        """
        > It takes a class and a dictionary of keyword arguments, and returns an
        instance of that class with the data from the database

        :param cls: The class that is calling the method
        :return: The first row of the table that matches the query.
        """
        return cls.where(**kwargs).first()

    @classmethod
    def read_all(cls, **kwargs) -> ModelType:
        """
        > It takes a class and a dictionary of keyword arguments, and returns an
        instance of that class with the data from the database

        :param cls: The class that is calling the method
        :return: The first row of the table that matches the query.
        """
        try:
            return cls.where(**kwargs).all()
        except Exception as e:
            logger.error(e)
            cls.session.rollback()
            return

    @classmethod
    def search(cls, *_, **kwargs) -> list:
        """
        The admin_search_users function allows an admin user to search for users by various criteria.
        The function accepts a dictionary of key-value pairs as input, and returns a list of dictionaries
        of matching users. The keys in the input dictionary can be any field in the User model, and each value
        can be either a single string or an iterable containing strings.

        note: the filter will search by phone OR email if provided, and if not,
        ALL criteria so pass explicit fields to search by.

        :param *_: Used to Catch any additional arguments that are passed in, but not used by the function.
        :param **kwargs: Used to Allow the caller to pass in a dictionary of key/value pairs that
        will be used as filters for the query.
        :return: A list of users that match the filters in kwargs.
        """
        try:
            if email := kwargs.get("email"):
                if results := cls.where().filter(cls.email.ilike(f"%{email}%")).all():
                    return results
            if username := kwargs.get("name"):
                if (
                    results := cls.where()
                    .filter(cls.username.ilike(f"%{username}%"))
                    .all()
                ):
                    return results
            if firstName := kwargs.get("firstName"):
                if (
                    results := cls.where()
                    .filter(cls.firstName.ilike(f"%{firstName}%"))
                    .all()
                ):
                    return results
        except Exception as e:
            logger.error(e)
            cls.session.rollback()
            return


class DataSeeder:
    """
    This class is used to seed the database with data
    """

    def __init__(self, number_of_records: int = 10, exclude_list: list = None) -> None:
        self.number_of_records = number_of_records
        engine = create_engine(f"postgresql+psycopg2://{Config.postgres_connection}")
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.fake = Faker()
        self.metadata = MetaData(bind=engine)
        self.metadata.reflect()
        self.mapped = {}
        # exclude models from generation
        self.exclude_list = exclude_list

    @staticmethod
    def snake_to_pascal_case(name: str) -> str:
        """
        It takes a string in snake case and returns a string in Pascal case

        :param name: The name of the class to be generated
        :type name: str
        :return: A string with the first letter of each word capitalized.
        """
        return "".join(word.capitalize() for word in name.split("_"))

    @staticmethod
    def save_model(model, row_data):
        """
        It takes a model and a dictionary of data, and saves the data to the database if it does not violate any constraints

        :param model: The model to save the data to
        :param row_data: A dictionary of the row data
        """
        try:
            model.get_or_create(model, **row_data)
            # commit changes to the database
            model.session.commit()
        except IntegrityError:
            # handle unique constraint violation by rolling back the transaction
            model.session.rollback()

    def get_model_class(self, table_name: str) -> ModelType:
        """
        It imports the module `app.api.{route}.models`
        and returns the class `{table_name}` from that module

        :param table_name: The name of the table you want to get the model class for
        :type table_name: str
        :return: The model class for the table name.
        """

        for route in APIPrefix.include:
            with contextlib.suppress(ImportError, AttributeError):
                module = __import__(f"app.api.{route}.models", fromlist=[table_name])
                # class_name = DataSeeder.snake_to_pascal_case(table_name)
                return getattr(module, table_name)

    def get_model_metadata(self):
        # import metadata for all routes to build the registry
        for route in APIPrefix.include:
            with contextlib.suppress(ImportError):
                if route != "auth":
                    exec(f"from app.api.{route}.models import ModelMixin as Base")

        # loop through models in registry
        for table in sorted(
            Base.metadata.sorted_tables, key=lambda t: t.name, reverse=True
        ):
            if (
                table.name not in self.metadata.tables
            ):  # or table.name in self.exclude_list:
                continue

            if model := self.get_model_class(table.name):
                model.name = model.__name__
                yield model, table

    def get_data_type_mapper(self) -> SimpleNamespace:
        """
        returns a list of objects that have a type and fake_type attribute

        :param table: The table name
        :return: A list of objects with the type and fake_type attributes.
        """
        return SimpleNamespace(
            type_maps=[
                SimpleNamespace(
                    type=DateTime,
                    fake_type=self.fake.date_time_between(
                        start_date="-30y", end_date="now"
                    ),
                ),
                SimpleNamespace(type=Boolean, fake_type=self.fake.boolean()),
                SimpleNamespace(type=Integer, fake_type=self.fake.random_int()),
                SimpleNamespace(type=Float, fake_type=self.fake.pyfloat(positive=True)),
                SimpleNamespace(
                    type=Interval, fake_type=timedelta(seconds=randint(0, 86400))
                ),
                SimpleNamespace(type=UUID, fake_type=str(uuid.uuid4())),
                SimpleNamespace(
                    type=String,
                    fake_type=f"{' '.join([self.fake.word() for _ in range(8)])}",
                ),
            ]
        )

    def get_table_data(self, table, column) -> List[ModelType]:
        """
        It returns a list of all the values in a given column of a given table

        :param table: The name of the table you want to query
        :param column: The column name to get data from
        :return: A list of all the values in the column of the table.
        """
        return self.session.query(getattr(self.get_model_class(table), column)).all()

    def generate_fake_row_data(self, table: MetaData) -> dict:
        """
        Loop through all table columns, check data types for all columns in a
        table and generate fake data, ensure pk is unique, loop through table
        relationships, link fk to existing record, or make one first then build relationship

        :param table: The table object that we're generating data for
        :return: A dictionary of column names and fake data.
        """

        # loop through all table columns
        row_data = {}
        for column in table.columns:
            # Check data types for all columns in a table and generate fake data
            data_type_mapper = self.get_data_type_mapper()
            for data_type in data_type_mapper.type_maps:
                if isinstance(column.type, data_type.type):
                    row_data[column.name] = data_type.fake_type

            # ensure pk is unique
            if column.primary_key and isinstance(column.type, UUID):
                row_data[column.name] = str(uuid.uuid4())
            if column.primary_key and isinstance(column.type, int):
                row_data[column.name] = self.fake.random_int() * self.fake.random_int()

            # loop through table relationships
            for fk in column.foreign_keys:
                fk_table = fk.column.table
                fk_column = fk.column

                # link fk to existing record, or make one first then build relationship
                if fk_records := self.get_table_data(fk_table.name, fk_column.name):
                    row_data[column.name] = choice(fk_records)[0]
                else:
                    new_data = self.generate_fake_row_data(fk_table)
                    self.save_model(self.get_model_class(fk_table.name), new_data)

        return row_data

    def generate(self):
        """
        For each model in the registry, generate a number
        of fake records equal to the number of records specified by
        the user, and save them to the database.
        """

        # loop through models in registry
        for model, table in list(self.get_model_metadata()):
            if table.name in self.exclude_list:
                continue
            for _ in range(self.number_of_records):
                row_data = self.generate_fake_row_data(table)
                self.save_model(model, row_data)
            print(model, f"{self.number_of_records} records added to db")


class Page(Generic[T]):
    """
    Pagination class to allow for paging of database data
    """

    def __init__(self, items: list, page: int = 1, page_size: int = 10, total: int = 0):
        self.items = items
        self.dict_items = [
            isinstance(_item, Row) and _item._asdict() or _item for _item in items
        ]
        self.page = page
        self.page_size = page_size
        self.total = total
        self.previous_page = None
        self.next_page = None
        self.has_previous = page > 1
        if self.has_previous:
            self.previous_page = page - 1
        previous_items = (page - 1) * page_size
        self.has_next = previous_items + len(items) < total
        if self.has_next:
            self.next_page = page + 1
        self.pages = int(math.ceil(total / float(page_size)))

    def __getitem__(self, parameters):
        return self._getitem(self, parameters)

    def as_dict(self):
        """
        The as_dict function returns a dictionary representation of the object.
        This is useful for JSON serialization, and also allows you to access all the
        properties on the object directly from the returned dictionary.

        :param self: Used to Reference the current instance of the class.
        :return: A dictionary that contains all the information about the object.
        """
        return self.__dict__

    def _getitem(self, self1, parameters):
        """
        The _getitem function is a helper function that is called by the getitem method.
        It takes in two parameters, self and parameters. The self parameter is automatically passed to the function when it's called, so you don't need to worry about this one too much. The second parameter is a dictionary of all of the keyword arguments that were passed into getitem (which was itself called from __getitem__). This means that if someone calls your class like:

        my_class["hello", "world"]  # <- This will be translated into `my_class._getitem({"key": ["hello", "world"]})` by Python before calling __getitem__.

        :param self: Used to Access variables that belongs to the class.
        :param self1: Used to Refer to the instance of the class.
        :param parameters: Used to Pass in the parameters of the function.
        :return: A list of the items in the set.
        """


def paginate(cls, page: int, page_size: int):
    """
    The paginate function takes a query, the page number and page size as arguments.
    It then returns a tuple of the items on that page and the total number of items.

    :param query: Used to Pass a query object to the paginate function.
    :param page: Used to Determine which page of results to return.
    :param page_size: Used to Determine how many items to show on each page.
    :return: A tuple containing the list of items for that page, and a total number of pages.
    """
    if page <= 0:
        raise HTTPException(400, detail="page needs to be >= 1")
    if page_size <= 0:
        raise HTTPException(400, detail="page_size needs to be >= 1")
    items: list[Row] = cls.where().limit(page_size).offset((page - 1) * page_size).all()
    total_items = cls.count()
    return Page(items, page, page_size, total_items)
