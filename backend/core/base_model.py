"""Shared Pydantic base model."""

from pydantic import BaseModel, ConfigDict


class MasonBaseModel(BaseModel):
    """Shared model config for API and domain models."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

