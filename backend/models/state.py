from typing import Optional
from pydantic import BaseModel, Field


class Executor(BaseModel):
    name: Optional[str] = Field(default=None, description="The full name of the executor.")
    relationship: Optional[str] = Field(default=None, description="The executor's relationship to the user.")


class PersonalWishesState(BaseModel):
    full_name: Optional[str] = Field(default=None, description="The user's full name.")
    home_address: Optional[str] = Field(default=None, description="The user's home address.")
    covers_worldwide_assets: Optional[bool] = Field(
        default=None, description="Whether the document covers worldwide assets."
    )
    has_children: Optional[bool] = Field(
        default=None, description="Whether the user has children."
    )
    children_names: list[str] = Field(
        default_factory=list, description="Names of the children, if applicable."
    )
    executor: Executor = Field(
        default_factory=Executor, description="The designated executor."
    )
    specific_gifts: Optional[list[str]] = Field(
        default=None, description="Any specific gifts to be made. None means not answered, [] means explicitly none."
    )
    additional_wishes: Optional[str] = Field(
        default=None, description="Any additional wishes or instructions."
    )
