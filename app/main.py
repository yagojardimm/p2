import asyncio
import logging
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from typing import List

from app.models import OrderCreate, Order, OrderStatus
from app.database import connect_to_mongo, close_mongo_connection, get_collection
from app.queue_publisher import rabbitmq_publisher
from app.kafka_publisher import kafka_publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def connect_services_with_retry():
    max_retries = 10
    retry_delay = 3

    for i in range(max_retries):
        try:
            logger.info("Conectando ao MongoDB...")
            await connect_to_mongo()
            logger.info("MongoDB conectado.")
            break
        except Exception as e:
            logger.warning(f"Falha MongoDB (tentativa {i+1}/{max_retries}): {e}")
            if i == max_retries - 1:
                raise e
            await asyncio.sleep(retry_delay)

    for i in range(max_retries):
        try:
            logger.info("Conectando ao RabbitMQ...")
            await rabbitmq_publisher.connect()
            logger.info("RabbitMQ conectado.")
            break
        except Exception as e:
            logger.warning(f"Falha RabbitMQ (tentativa {i+1}/{max_retries}): {e}")
            if i == max_retries - 1:
                raise e
            await asyncio.sleep(retry_delay)

    for i in range(max_retries):
        try:
            logger.info("Conectando ao Kafka...")
            await kafka_publisher.connect()
            logger.info("Kafka conectado.")
            break
        except Exception as e:
            logger.warning(f"Falha Kafka (tentativa {i+1}/{max_retries}): {e}")
            if i == max_retries - 1:
                raise e
            await asyncio.sleep(retry_delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_services_with_retry()
    yield
    logger.info("Encerrando conexoes...")
    await close_mongo_connection()
    await rabbitmq_publisher.close()
    await kafka_publisher.close()
    logger.info("Conexoes encerradas.")


app = FastAPI(
    title="API de Gerenciamento de Pedidos",
    description="API para cadastro e consulta de pedidos, com MongoDB, RabbitMQ e Kafka.",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


@app.post("/pedidos", response_model=Order, status_code=status.HTTP_201_CREATED)
async def criar_pedido(order_in: OrderCreate):
    order_id = str(uuid4())

    order_doc = {
        "_id": order_id,
        "client_name": order_in.client_name,
        "product_name": order_in.product_name,
        "quantity": order_in.quantity,
        "status": OrderStatus.PENDENTE.value
    }

    try:
        collection = get_collection()
        await collection.insert_one(order_doc)

        # publica no rabbit e no kafka
        await rabbitmq_publisher.publish_order_created(
            order_id=order_id,
            client_name=order_in.client_name,
            product_name=order_in.product_name
        )

        order_data = {
            "id": order_id,
            "client_name": order_in.client_name,
            "product_name": order_in.product_name,
            "quantity": order_in.quantity,
            "status": OrderStatus.PENDENTE.value
        }
        await kafka_publisher.publish_order_event("pedido_criado", order_data)

        return Order(
            id=order_id,
            client_name=order_in.client_name,
            product_name=order_in.product_name,
            quantity=order_in.quantity,
            status=OrderStatus.PENDENTE
        )
    except Exception as e:
        logger.error(f"Erro ao cadastrar pedido: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar pedido: {str(e)}"
        )


@app.get("/pedidos", response_model=List[Order])
async def listar_pedidos():
    try:
        collection = get_collection()
        cursor = collection.find()
        orders = []
        async for doc in cursor:
            orders.append(
                Order(
                    id=doc["_id"],
                    client_name=doc["client_name"],
                    product_name=doc["product_name"],
                    quantity=doc["quantity"],
                    status=OrderStatus(doc["status"])
                )
            )
        return orders
    except Exception as e:
        logger.error(f"Erro ao listar pedidos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar pedidos: {str(e)}"
        )
