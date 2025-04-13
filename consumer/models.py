from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, Identity
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")
    group = Column(String, nullable=True)
    having_meal = Column(Boolean, nullable=True, default=False)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class Schedule(Base):
    __tablename__ = "schedule"

    weekday = Column(Integer, primary_key=True)
    items = relationship("ScheduleItem", back_populates="schedule", cascade="all, delete-orphan")
    

class ScheduleItem(Base):
    __tablename__ = "schedule_items"

    id = Column(Integer, primary_key=True)
    start_time = Column(Time)
    end_time = Column(Time)
    type = Column(String)  # breakfast, dinner, lunch

    schedule_weekday = Column(Integer, ForeignKey("schedule.weekday", ondelete="CASCADE"))

    schedule = relationship("Schedule", back_populates="items")
    slots = relationship("Slot", back_populates="item", cascade="all, delete-orphan")

class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, Identity(start=1, increment=1), primary_key=True)
    start_time = Column(Time)
    end_time = Column(Time)

    item_id = Column(Integer, ForeignKey("schedule_items.id", ondelete="CASCADE"))
    reserved_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    item = relationship("ScheduleItem", back_populates="slots")

class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True)
    menu_items = relationship("MenuItem", back_populates="menu", cascade="all, delete-orphan")

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, Identity(start=1, increment=1), primary_key=True)
    menu_id = Column(Integer, ForeignKey("menu.id", ondelete="CASCADE"))
    type = Column(String) # breakfast, dinner, lunch
    menu = relationship("Menu", back_populates="menu_items")
    dishes = relationship("Dish", back_populates="menu_item", cascade="all, delete-orphan")
     
class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, Identity(start=1, increment=1), primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    calories = Column(Integer)
    
    menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"))
    menu_item = relationship("MenuItem", back_populates="dishes")

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    object_name = Column(String, unique=True, index=True)
    