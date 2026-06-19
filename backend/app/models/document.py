from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    file_name: str
    storage_path: str


class DocumentResponse(DocumentBase):
    document_id: str
    user_id: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
