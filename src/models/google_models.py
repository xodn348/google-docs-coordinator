"""Google API response models using Pydantic."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """Google user representation."""

    display_name: str
    email: Optional[str] = None
    photo_link: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "User":
        """Parse from Google API user object."""
        return cls(
            display_name=data.get("displayName", "Unknown"),
            email=data.get("emailAddress"),
            photo_link=data.get("photoLink"),
        )


class Reply(BaseModel):
    """Comment reply."""

    id: str
    content: str
    author: User
    created_time: datetime
    modified_time: Optional[datetime] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "Reply":
        """Parse from API response."""
        return cls(
            id=data["id"],
            content=data.get("content", ""),
            author=User.from_api_response(data.get("author", {})),
            created_time=datetime.fromisoformat(
                data["createdTime"].replace("Z", "+00:00")
            ),
            modified_time=datetime.fromisoformat(
                data["modifiedTime"].replace("Z", "+00:00")
            )
            if data.get("modifiedTime")
            else None,
        )


class Comment(BaseModel):
    """Google Docs comment."""

    id: str
    content: str
    author: User
    created_time: datetime
    modified_time: Optional[datetime] = None
    resolved: bool = False
    replies: list[Reply] = Field(default_factory=list)
    quoted_content: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "Comment":
        """Parse from Drive API comment object."""
        return cls(
            id=data["id"],
            content=data.get("content", ""),
            author=User.from_api_response(data.get("author", {})),
            created_time=datetime.fromisoformat(
                data["createdTime"].replace("Z", "+00:00")
            ),
            modified_time=datetime.fromisoformat(
                data["modifiedTime"].replace("Z", "+00:00")
            )
            if data.get("modifiedTime")
            else None,
            resolved=data.get("resolved", False),
            replies=[Reply.from_api_response(r) for r in data.get("replies", [])],
            quoted_content=data.get("quotedFileContent", {}).get("value"),
        )


class Revision(BaseModel):
    """Document revision metadata."""

    id: str
    modified_time: datetime
    last_modifying_user: Optional[User] = None
    size: Optional[int] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "Revision":
        """Parse from Drive API revision object."""
        return cls(
            id=data["id"],
            modified_time=datetime.fromisoformat(
                data["modifiedTime"].replace("Z", "+00:00")
            ),
            last_modifying_user=User.from_api_response(data["lastModifyingUser"])
            if data.get("lastModifyingUser")
            else None,
            size=data.get("size"),
        )


class DocumentMetadata(BaseModel):
    """Document basic info."""

    document_id: str
    title: str
    revision_id: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "DocumentMetadata":
        """Parse from Docs API document object."""
        return cls(
            document_id=data["documentId"],
            title=data.get("title", "Untitled"),
            revision_id=data.get("revisionId"),
        )
