import json
import aio_pika
from app.config import settings

class RabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        # Garante que a fila existe
        await self.channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True)

    async def publish_order_created(self, order_id: str, client_name: str, product_name: str):
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized")
        
        message_data = {
            "id": order_id,
            "client_name": client_name,
            "product_name": product_name,
            "status": "PENDENTE"
        }
        
        message_body = json.dumps(message_data).encode("utf-8")
        
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=settings.RABBITMQ_QUEUE
        )

    async def close(self):
        if self.connection:
            await self.connection.close()

rabbitmq_publisher = RabbitMQPublisher()
