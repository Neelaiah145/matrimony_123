from ninja import Schema
from datetime import datetime


class MatchResponseSchema(Schema):
    user_id: int
    first_name: str
    last_name: str
    profile_photo: str | None = None
    age: int | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    occupation: str
    education: str
    religion: str
    caste: str
    match_percentage: float
    matched_fields: list[str]
    is_mutual: bool
    
    
    
class InterestSendSchema(Schema):
    """ Send interest request. """
    to_user: int
    message: str | None = None
    
    
class InterestUpdateSchema(Schema):
    """ Accept / Reject / Withdraw interest. """
    status: str
    



class InterestResponseSchema(Schema):
    """ Interest details. """

    id: int
    from_user: int
    to_user: int
    first_name: str
    last_name: str
    profile_photo: str | None = None
    age: int | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    occupation: str | None = None
    education: str | None = None
    religion: str | None = None
    caste: str | None = None
    message: str | None = None
    status: str
    is_seen: bool
    created_at: datetime
    
    
class ShortlistCreateSchema(Schema):
    """Shortlist profile."""
    user: int
    
    
class IgnoreCreateSchema(Schema):
    """Ignore profile."""
    user: int
    reason: str | None = None
    
    


class BlockCreateSchema(Schema):
    """Block profile."""
    user: int
    reason: str | None = None
    
    
class MessageResponseSchema(Schema):
    """Common success response."""
    success: bool
    message: str