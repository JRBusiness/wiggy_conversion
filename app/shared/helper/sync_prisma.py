from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, UUID

from app import ModelMixin
from settings import Config

path = "igor/baohule/config/prisma-config/prisma/prisma/casino-prisma.prisma"
from sqlalchemy import (
    UniqueConstraint,
    ForeignKey,
    JSON,
    BOOLEAN,
    String,
    VARCHAR,
)

# Define a mapping of SQLAlchemy types to Prisma types
type_mapping = {
    # SQLAlchemy types
    "Integer": "Int",
    "BigInteger": "BigInt",
    "SmallInteger": "Int",
    "Float": "Float",
    "Numeric": "Decimal",
    "Boolean": "Boolean",
    "Date": "DateTime",
    "Time": "DateTime",
    "DateTime": "DateTime",
    "Interval": "Int",
    "String": "String",
    "Text": "String",
    "Unicode": "String",
    "UnicodeText": "String",
    "JSON": "Json",
    "ARRAY": "Json",  # Map PostgreSQL ARRAY to Json in Prisma
    "UUID": "String",  # Map UUID to String in Prisma
    # PostgreSQL specific types
    "BIT": "String",
    "VARBIT": "String",
    "BYTEA": "Bytes",
    "CIDR": "String",
    "INET": "String",
    "MACADDR": "String",
    "JSONB": "Json",
    "TSVECTOR": "String",
    "TSQUERY": "String",
    "INT4RANGE": "String",
    "INT8RANGE": "String",
    "NUMRANGE": "String",
    "TSRANGE": "String",
    "TSTZRANGE": "String",
}
from typing import Any


def prisma_generator(model: Any) -> str:
    if metadata := model.metadata:
        tables = metadata.sorted_tables
        prisma = ""
        for table in tables:
            prisma += f"model {table.name} {{\n"
            columns = table.columns
            for column in columns:
                column_name = column.name
                column_type = column.type

                # UUID (primary key)
                if isinstance(column_type, UUID) and column.primary_key:
                    prisma += (
                        f"    {column_name} String @id @default(uuid()) @db.Uuid\n"
                    )

                elif isinstance(column_type, UUID):
                    prisma += f"    {column_name} String @default(uuid()) @db.Uuid"
                    prisma += "\n"

                elif isinstance(column_type, (String, VARCHAR)):
                    prisma += (
                        f"    {column_name} String?"
                        if column.nullable
                        else f"    {column_name} String"
                    )
                    if column.unique:
                        prisma += f' @unique(map: "{table.name}_{column_name}")'
                    prisma += f" @db.VarChar({column.type.length})\n"

                elif isinstance(column_type, INTEGER):
                    prisma += (
                        f"    {column_name} Int?"
                        if column.nullable
                        else f"    {column_name} Int"
                    )
                    if column.unique:
                        prisma += " @unique"
                    prisma += "\n"

                elif isinstance(column_type, BOOLEAN):
                    prisma += f"    {column_name} Boolean @default(true)"
                    prisma += "\n"

                elif isinstance(column_type, TIMESTAMP):
                    if column.name == "created_at":
                        prisma += f"    {column_name} DateTime? @default(now())"
                        if not column.nullable:
                            prisma += f"    {column_name} DateTime @default(now())"
                    elif column.name == "updated_at":
                        prisma += f"    {column_name} DateTime?"
                    prisma += "\n"

                elif isinstance(column_type, JSON):
                    prisma += (
                        f"    {column_name} Json?"
                        if column.nullable
                        else f"    {column_name} Json"
                    )
                    prisma += "\n"

                elif isinstance(column_type, ForeignKey):
                    target_table = column_type.column.table.name
                    target_column = column_type.column.name
                    prisma += f"    {column_name} {target_table} @relation(fields: [{column_name}], references: [{target_column}])\n"

                else:
                    prisma += f"    {column_name} {str(column_type)}"
                    if not column.nullable:
                        prisma += f"    {column_name}? {str(column_type)}"
                    prisma += "\n"

            constraints = table.constraints
            for constraint in constraints:
                if isinstance(constraint, UniqueConstraint):
                    columns = constraint.columns
                    if len(columns) > 1:
                        columns = (
                            "{" + ", ".join([str(col.name) for col in columns]) + "}"
                        )
                    else:
                        columns = str(columns[0].name)
                    prisma += f"    @@unique([{columns}])\n"

            relationships = table.foreign_keys
            for relationship in relationships:
                local_column = relationship.parent
                foreign_column = relationship.column
                target_table = foreign_column.table.name
                target_column = foreign_column.name
                prisma += f"    {local_column.name.replace('Id', '')} {target_table} @relation(fields: [{local_column.name}], references: [{target_column}])\n"

            prisma += "}\n\n"

    return prisma


def is_valid_type(sqlalchemy_type):
    """
    Check if a given SQLAlchemy type can be mapped to a valid Prisma type.
    """
    valid_types = ["String", "Int", "Float", "Boolean", "DateTime", "Json"]
    return sqlalchemy_type.__class__.__name__ in valid_types


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(f"postgresql+psycopg2://{Config.postgres_connection}")
    Session = sessionmaker(bind=engine)
    session = Session()

    ModelMixin.metadata.reflect(engine)
    prisma = ""
    print(ModelMixin)
    prisma_output = prisma.join(prisma_generator(ModelMixin))

    # with open(path, 'w') as f:
    # f.write(prisma)
    print(prisma_output)
