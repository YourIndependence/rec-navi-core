
"""user model."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class XUser(BaseModel):
    """load shared history item."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        extra="allow",
    )
    id: str = Field(..., description="user unique ID")
    mail: str = Field(..., description="mail string")
    is_admin: bool = Field(..., description="is admin")
