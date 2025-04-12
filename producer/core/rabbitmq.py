import aio_pika
import json
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import Request

EXCHANGE_NAME = "stolovaya_exchange"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RabbitMQManager:
    def __init__(self, url: str = "amqp://guest:guest@localhost/"):
        self.url = url
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.callback_queue: Optional[aio_pika.Queue] = None
        self.futures: Dict[str, asyncio.Future] = {}

    async def connect(self):
        try:
            logger.info("Connecting to RabbitMQ...")
            self.connection = await aio_pika.connect_robust(self.url)
            self.channel = await self.connection.channel()
            
            # Создаем exchange
            logger.info(f"Declaring exchange {EXCHANGE_NAME}...")
            self.exchange = await self.channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Создаем callback очередь
            logger.info("Creating callback queue...")
            self.callback_queue = await self.channel.declare_queue(
                exclusive=True,
                auto_delete=True,
                durable=False
            )
            
            # Привязываем callback очередь к exchange
            await self.callback_queue.bind(self.exchange, routing_key=self.callback_queue.name)
            
            # Начинаем слушать callback очередь
            await self.callback_queue.consume(self.on_response)
            logger.info("RabbitMQ connection established successfully")
            return self
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            raise

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")

    async def on_response(self, message: aio_pika.Message):
        try:
            async with message.process():
                if message.correlation_id in self.futures:
                    logger.info(f"Received response for correlation_id: {message.correlation_id}")
                    future = self.futures.pop(message.correlation_id)
                    future.set_result(json.loads(message.body.decode()))
                else:
                    logger.warning(f"Received response for unknown correlation_id: {message.correlation_id}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in response: {e}")
            if not message.processed:
                await message.reject(requeue=False)
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            if not message.processed:
                await message.reject(requeue=False)

    async def publish_message(
        self,
        routing_key: str,
        message: dict,
        exchange_name: str = EXCHANGE_NAME
    ) -> dict:
        if not self.connection or not self.channel or not self.exchange:
            raise RuntimeError("RabbitMQ connection not established")

        correlation_id = str(uuid.uuid4())
        future = asyncio.Future()
        self.futures[correlation_id] = future

        body = json.dumps(message).encode()
        
        logger.info(f"Publishing message to {routing_key} with correlation_id: {correlation_id}")
        await self.exchange.publish(
            aio_pika.Message(
                body=body,
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name
            ),
            routing_key=routing_key
        )

        try:
            # Увеличиваем таймаут до 60 секунд
            response = await asyncio.wait_for(future, timeout=60.0)
            logger.info(f"Received response for correlation_id: {correlation_id}")
            return response
        except asyncio.TimeoutError:
            if correlation_id in self.futures:
                self.futures.pop(correlation_id)
            logger.error(f"Timeout waiting for response for correlation_id: {correlation_id}")
            raise RuntimeError("Timeout waiting for response from consumer")
        except Exception as e:
            if correlation_id in self.futures:
                self.futures.pop(correlation_id)
            logger.error(f"Error processing response for correlation_id {correlation_id}: {e}")
            raise RuntimeError(f"Error processing response: {str(e)}")

# Global instance
rabbitmq_manager = RabbitMQManager()