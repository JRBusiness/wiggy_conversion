"""
@author: Kuro
"""
from fastapi_camelcase import CamelModel


class ORMCamelModel(CamelModel):
    class Config:
        orm_mode = True
