from typing import Optional

from pydantic import BaseModel, Field

from app.shared.schemas.ResponseSchemas import BaseResponse


class Error(BaseModel):
    message: Optional[str]

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message


class AuthenticationScopeMismatch(BaseResponse):
    error: str = Field(
        default="Authentication Scope Mismatch: "
        "You are probably not logged in as an Agent"
    )


class AgentQuotaExceeded(BaseResponse):
    error: str = Field(
        default="""
        Agent Quota Exceeded:
        The Agents Quota is less than the amount you want to credit the User with.
        Ask The Administration team to increase your quota by submitting a ticket to support 
        with the subject "Increase Agent Quota" and the amount you want to increase it with.
        Url: https://support.baohule.com
        """
    )


class NoUserBalanceObject(BaseResponse):
    error: Optional[str] = Field(
        default="No User Balance Object Found: "
        "Please create a balance object for this user "
        "with the endpoint: "
        "/api/credit/manage/create_user_credit"
    )


class QuotaNotUpdated(BaseResponse):
    error: Optional[str] = Field(
        default="Quota Not Updated:"
        "Due to a unique constraint or the object not existing "
        "in the database, the quota was not updated and the "
        "db session was rolled back. The most likely cause is "
        "that the agent does not exist in the database."
    )
