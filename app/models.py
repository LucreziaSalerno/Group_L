from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ModelConfigParams(BaseModel):
    model: str
    prompt: str
    temperature: float = 0.1

class ImageryConfig(BaseModel):
    width: int
    height: int
    bbox_half_size_degrees_base: float = 0.8

class AppConfig(BaseModel):
    image_analysis: ModelConfigParams
    risk_analysis: ModelConfigParams
    imagery: ImageryConfig

class ImageRecord(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    latitude: float
    longitude: float
    zoom: int
    image_path: str
    image_description: str
    image_prompt: str
    image_model: str
    text_description: str
    text_prompt: str
    text_model: str
    danger: str
