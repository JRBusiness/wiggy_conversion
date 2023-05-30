import importlib
from typing import List
from faker import Faker
from pydantic import BaseModel, BaseConfig
from typing import Any, List, Tuple

from app.shared.schemas.orm_schema import Schema


def get_pydantic_models(module_name: str) -> List[BaseModel]:
    """
    Given the name of a Pydantic schema module, this function
    returns a list of all its Pydantic models.
    """
    module = importlib.import_module(module_name)
    return [member for member in vars(module).values() if isinstance(member, type) and issubclass(member, BaseModel)]

def generate_data_for_model(model: BaseModel, fake: Faker) -> dict:
        """
        Given a Pydantic model and a Faker instance, this function generates
        a dictionary of fake data for that model, with all nested fields also populated.
        """
        if not issubclass(type(model), Schema.__class__):
            print(TypeError("Invalid argument: First argument must be a Pydantic model class"))
            return

        data = {}
        for key, value in model.__fields__.items():
            field_type = getattr(value.type_, "__supertype__", value.type_)
            if isinstance(field_type, BaseModel.__class__):
                if issubclass(field_type, BaseModel.__class__):
                    data[key] = generate_data_for_model(field_type, fake)  # created an instance of the model to handle private class members
                elif issubclass(field_type, List):
                    inner_type = getattr(field_type, "__args__")[0]
                    if issubclass(inner_type, BaseModel.__class__):
                        data[key] = [generate_data_for_model(inner_type, fake) for _ in range(3)]
                    else:
                        data[key] = [fake.parse(inner_type.__name__) for _ in range(3)]
                elif issubclass(field_type, Tuple):
                    inner_types = getattr(field_type, "__args__")
                    data[key] = tuple(fake.parse(inner_type.__name__) for inner_type in inner_types)
                else:
                    data[key] = fake.parse(field_type.__class__.__name__)
        return data

def generate_sample_data(module_name: str) -> dict:
    """
    Given the name of a Pydantic schema module, this function generates
    a dictionary of sample data for all its Pydantic models, with all nested fields
    also populated.
    """
    fake = Faker()
    models = get_pydantic_models(module_name)
    return {
        model.__name__: generate_data_for_model(model, fake)
        for model in models
    }

sample_data = generate_sample_data('app.api.user.schema')

print(sample_data)