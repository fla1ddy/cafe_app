from sqlalchemy.orm import Session
from models import User, Schedule

async def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)

async def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

async def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

async def get_schedule_by_weekday(db: Session, weekday: int):
    return db.query(Schedule).filter(Schedule.weekday == weekday).first()


