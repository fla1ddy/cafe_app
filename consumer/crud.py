from sqlalchemy.orm import Session
from models import User, Schedule, ScheduleItem, Slot

async def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)

async def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

async def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first().as_dict()

async def get_schedule_by_weekday(db: Session, weekday: int):
    return db.query(Schedule).filter(Schedule.weekday == weekday).first()


async def get_schedule_item_by_type(db: Session, weekday: int, schedule_item_type: str):
    schedule = await get_schedule_by_weekday(db, weekday)
    if not schedule:
        return None
    return db.query(ScheduleItem).filter(
        ScheduleItem.type == schedule_item_type,
        ScheduleItem.schedule_weekday == schedule.weekday
    ).first()


async def get_slot(db: Session, weekday: int, schedule_item_type: str, slot_start_time: str):
    schedule_item = await get_schedule_item_by_type(db, weekday, schedule_item_type)
    if not schedule_item:
        return None

    return db.query(Slot).filter(
        Slot.start_time == slot_start_time,
        Slot.item_id == schedule_item.id
    ).first()