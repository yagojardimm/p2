import json
from aiokafka import AIOKafkaProducer
from app.config import settings

class KafkaPublisher:
    def __init__(self):
        self.producer = None

    async def connect(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await self.producer.start()

    async def publish_order_event(self, event_type: str, order_data: dict):
        if not self.producer:
            raise RuntimeError("Kafka producer is not initialized")
        
        event_payload = {
            "event": event_type,
            "data": order_data
        }
        
        await self.producer.send_and_wait(settings.KAFKA_TOPIC, event_payload)

    async def close(self):
        if self.producer:
            await self.producer.stop()

kafka_publisher = KafkaPublisher()
