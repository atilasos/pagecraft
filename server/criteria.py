"""Child-facing reflection criteria shared by activity registration and classroom hosts."""
from typing import Annotated

from pydantic import BaseModel, Field


class Criterion(BaseModel):
    id: Annotated[str, Field(pattern=r'^[a-z0-9_-]{1,40}$')]
    pt: Annotated[str, Field(min_length=1, max_length=300)]
    en: Annotated[str, Field(max_length=300)] = ''

