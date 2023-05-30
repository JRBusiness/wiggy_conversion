import os
from pydantic import BaseModel, parse_file_as
from faker import Faker



def generate_fake_data_from_schemas(schema_dir: str) -> dict:
    """
    Given a directory containing Pydantic schema files, this function loads each model
    in the schema and generates a dictionary of fake data for that model, with all nested
    fields also populated.
    """
    fake = Faker()

    # Get all the .py files in the specified folder
    file_dir = f"{base_dir}\\" + schema_dir.replace('.', '\\')
    files = [f for f in os.listdir(file_dir) if os.path.isfile(os.path.join(schema_dir, f)) and "schema" in f]

    # Load each Pydantic model in the schema and generate fake data for it
    data = {}
    for file in files:
        module_name = os.path.splitext(file)[0]
        module = __import__(f"{schema_dir}.{module_name}", fromlist=[module_name])
        for item in dir(module):
            obj = getattr(module, item)
            if isinstance(obj, type(BaseModel)) and obj != BaseModel:
                model = parse_file_as(os.path.join(schema_dir, file), item)
                print(model)

    return data

from settings import base_dir
generate_fake_data_from_schemas('app.api.user.schema')