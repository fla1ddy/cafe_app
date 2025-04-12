from pydantic import BaseModel, Field
from typing import Optional, List

class SlotModel(BaseModel):
    start_time: str
    end_time: str

class ScheduleItemModel(BaseModel):
    start_time: str
    end_time: str
    type: str # breakfast, lunch, dinner
    slots: Optional[List[SlotModel]] = Field(default_factory=list)

class ScheduleModel(BaseModel):
    weekday: int
    items: List[ScheduleItemModel] = Field(default_factory=list)

class DishModel(BaseModel):
    name: str
    description: str
    price: int
    calories: int

class MenuItemModel(BaseModel):
    type: str # breakfast, lunch, dinner
    dishes: List[DishModel] = Field(default_factory=list)

class MenuModel(BaseModel):
    menu_items: List[MenuItemModel] = Field(default_factory=list)