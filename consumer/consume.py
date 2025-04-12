import asyncio
import json
import logging
import os
from typing import Dict, Any
from aio_pika import connect, connect_robust, Message, IncomingMessage, Exchange, ExchangeType
from models import User, Schedule, ScheduleItem, Slot, Menu, MenuItem, Dish
from db import get_db
from crud import create_user, get_user_by_username, get_user_by_id, get_schedule_by_weekday, get_slot, get_group_head_by_group, get_slot_by_user_id
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host = os.getenv("RABBITMQ_HOST", "rabbitmq")
port = os.getenv("RABBITMQ_PORT", "5672")
RABBITMQ_URL = f"amqp://guest:guest@{host}:{port}/"
EXCHANGE_NAME = "stolovaya_exchange"

async def process_register(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    user_data = message["data"]
    try:
        existing_user = await get_user_by_username(db, user_data["username"])
        if existing_user:
            return {"error": "User with this username already exists"}
        new_user = User(
            username=user_data["username"],
            password=user_data["password"],
            role=user_data.get("role"),
            group=user_data.get("group")
        )
        await create_user(db, new_user)
    finally:
        db.close()
    return {"success": "Пользователь успешно зарегистрирован"}

async def process_login(message: Dict[str, Any]) -> Dict[str, Any]:
    db_gen = get_db()
    db = next(db_gen)
    username = message["data"]["username"]
    try:
        logger.info(f"Processing login request for user: {username}")
        existing_user = await get_user_by_username(db, username)
        if existing_user:
            logger.info(f"User found in database: {existing_user.as_dict()}")
            return existing_user.as_dict()
        else:
            logger.error(f"User not found: {username}")
            return {"error": "Пользователь не найден"} 
    finally:
        db.close()

async def process_student_profile(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    user_id = message["data"]["user_id"]
    try:
        user = await get_user_by_id(db, user_id)
        user = user.as_dict()
        del user["id"]
        del user["password"]

        if user["having_meal"]:
            group_head = await get_group_head_by_group(db, user["group"])
            slot = await get_slot_by_user_id(db, group_head.id)
            
            user["meal_start"] = str(slot.start_time)
            user["meal_end"] = str(slot.end_time)
        return user
    finally:
        db.close()


async def process_confirm_meal(message: Dict[str, Any]):
    db = next(get_db())
    try:
        user_id = message["data"]["user_id"]
        having_meal = message["data"]["having_meal"]
        
        user = await get_user_by_id(db, user_id)
        user.having_meal = having_meal
        db.add(user) 
        db.commit()
        db.refresh(user)
        
        return {"success": f"Meal status updated to {'will have meal' if having_meal else 'will not have meal'}"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

async def process_reserve_slot(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    try:
        slot = await get_slot(db, 
                        message["data"]["weekday"],
                        message["data"]["schedule_item_type"],
                        message["data"]["slot_start_time"])
        user_group = (await get_user_by_id(db, message["data"]["user_id"]))["group"]
        slot.reserved_by = message["data"]["user_id"]
        db.add(slot)
        db.commit()
        db.refresh(slot)

        return {"success": f"Слот для группы {user_group} успешно зарезервирован"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

    

async def process_get_group_choices(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    user_id = message["data"]["user_id"]
    try:
        headman = await get_user_by_id(db, user_id)
        students = db.query(User).filter(User.group == headman.group).all()
        choices = [
            {
                "username": student.username,
                "having_meal": student.having_meal
            }
            for student in students
            if student.id != headman.id
        ]
        return {"choices": choices}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
    return {"success": f"Выборы студентов группы {message['data']['group']} успешно получены"}

async def process_update_menu(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    logging.info({"data": message["data"]})
    logging.info({"menu_items": message["data"]["menu_items"]})
    try:
        menu = Menu(
            menu_items=[MenuItem(
                type=item["type"],
                dishes=[Dish(
                    name=dish["name"],
                    description=dish["description"],
                    price=dish["price"],
                    calories=dish["calories"],
                ) for dish in item["dishes"]]) for item in message["data"]["menu_items"]]
            )
        db.add(menu)
        db.commit()
        db.refresh(menu)
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close() 

async def process_update_schedule(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    try:
        schedule = Schedule(
            weekday=message["data"]["weekday"],
            items=[ScheduleItem(
                start_time=item["start_time"],
                end_time=item["end_time"],
                type=item["type"],
                slots=[Slot(
                    start_time=slot["start_time"],
                    end_time=slot["end_time"],
                ) for slot in item["slots"]]) for item in message["data"]["items"]]
            )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

async def process_get_menu(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    try:
        menu = db.query(Menu).first()
        menu = {
            "menu_items": [
                {
                    "type": item.type,
                    "dishes": [
                        {
                            "name": dish.name,
                            "description": dish.description,
                            "price": dish.price,
                            "calories": dish.calories
                        }
                        for dish in item.dishes
                    ]
                }
                for item in menu.menu_items
            ]}
        return menu
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

async def process_get_schedule(message: Dict[str, Any]):
    db_gen = get_db()
    db = next(db_gen)
    '''
    Schedule(
            weekday=message["data"]["weekday"],
            items=[ScheduleItem(
                start_time=item["start_time"],
                end_time=item["end_time"],
                type=item["type"],
                slots=[Slot(
                    start_time=slot["start_time"],
                    end_time=slot["end_time"],
                ) for slot in item["slots"]]) for item in message["data"]["items"]]
            )
    '''
    try:
        schedule = await get_schedule_by_weekday(db, message["data"])
        schedule =  {
            "weekday": schedule.weekday,
            "items": [
                {
                    "type": item.type,
                    "start_time": str(item.start_time),
                    "end_time": str(item.end_time),
                    "slots": [
                        {
                            "start_time": str(slot.start_time),
                            "end_time": str(slot.end_time),
                            "reserved_by": slot.reserved_by if slot.reserved_by else None
                        }
                        for slot in item.slots
                    ]
                }
                for item in schedule.items
            ]}
        return schedule
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

async def process_get_dashboard_data(message: Dict[str, Any]):
    #получаем данные для дашбоарда
    return {"success": f"Данные для дашбоарда успешно получены"}

async def process_assign_role(message: Dict[str, Any]):
    #назначаем роль пользователю message["data"]["user_email"] новой ролью message["data"]["new_role"]
    return {"success": f"Роль успешно назначена"}

async def process_message(message: IncomingMessage, exchange: Exchange):
    try:
        async with message.process():
            logger.info(f"Received message with correlation_id: {message.correlation_id}")
            request_data = json.loads(message.body.decode())
            action = request_data.get("action")
            response = {}

            # Log the received action and routing key
            logger.info(f"Processing action: {action} with routing key: {message.routing_key}")

            # обработка запросов
            match action:
                case "register_user":
                    logger.info("Processing register request...")
                    response = await process_register(request_data)
                case "get_user_by_username":
                    logger.info("Processing login request...")
                    response = await process_login(request_data)
                case "get_menu":
                    logger.info("Processing menu request...")
                    response = await process_get_menu(request_data)
                case "get_schedule":
                    logger.info("Processing schedule request...")
                    response = await process_get_schedule(request_data)
                case "get_student_profile":
                    logger.info("Processing student profile request...")
                    response = await process_student_profile(request_data)
                case "update_meal_status":
                    logger.info("Processing confirm meal request...")
                    response = await process_confirm_meal(request_data)
                case "reserve_slot":
                    logger.info("Processing reserve slot request...")
                    response = await process_reserve_slot(request_data)
                case "get_group_choices":
                    logger.info("Processing get group choices request...")
                    response = await process_get_group_choices(request_data)
                case "update_menu":
                    logger.info("Processing update menu request...")
                    response = await process_update_menu(request_data)
                case "update_schedule":
                    logger.info("Processing update schedule request...")
                    response = await process_update_schedule(request_data)
                case "get_dashboard_data":
                    logger.info("Processing get dashboard data request...")
                    response = await process_get_dashboard_data(request_data)
                case "assign_role":
                    logger.info("Processing assign role request...")
                    response = await process_assign_role(request_data)
                case _:
                    logger.warning(f"Unknown action received: {action}")
                    response = {"error": f"Unknown action: {action}"}

            # Отправляем ответ обратно в очередь, указанную в reply_to
            if message.reply_to:
                logger.info(f"Sending response to {message.reply_to}")
                response_message = Message(
                    body=json.dumps(response).encode(),
                    correlation_id=message.correlation_id
                )
                await exchange.publish(
                    response_message,
                    routing_key=message.reply_to
                )
                logger.info(f"Response sent for correlation_id: {message.correlation_id}")
            else:
                logger.warning("No reply_to in message, response not sent")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        if not message.processed:
            await message.reject(requeue=False)
        await send_error_response(message, exchange, "Invalid message format")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        if not message.processed:
            await message.reject(requeue=False)
        await send_error_response(message, exchange, str(e))

async def send_error_response(message: IncomingMessage, exchange: Exchange, error_msg: str):
    if message.reply_to:
        error_response = {"error": error_msg}
        error_message = Message(
            body=json.dumps(error_response).encode(),
            correlation_id=message.correlation_id
        )
        try:
            await exchange.publish(
                error_message,
                routing_key=message.reply_to
            )
            logger.error(f"Error response sent for correlation_id: {message.correlation_id}")
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")

async def main():
    # Создаем подключение
    connection = await connect_robust(RABBITMQ_URL)
    async with connection:
        # Создаем канал
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Создаем exchange
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            ExchangeType.DIRECT,
            durable=True
        )

        # Создаем очередь
        queue = await channel.declare_queue(
            "messages",
            durable=True,
            auto_delete=False
        )

        # Привязываем очередь к exchange с разными routing keys
        routing_keys = [
            "user.register",
            "user.login",
            "guest.schedule",
            "guest.menu",
            "admin.dashboard",
            "admin.assign_role",
            "cafe_admin.menu",
            "cafe_admin.schedule",
            "group_head.slot",
            "group_head.choices",
            "student.profile",
            "student.meal_status"
        ]
        
        for key in routing_keys:
            await queue.bind(exchange, routing_key=key)
            logger.info(f"Queue bound to exchange with routing key: {key}")

        # Начинаем обработку сообщений
        async with queue.iterator() as queue_iter:
            message: IncomingMessage
            async for message in queue_iter:
                await process_message(message, exchange)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Consumer error: {e}")
        raise