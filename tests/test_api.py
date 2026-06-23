import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def mock_external_services():
    # mocka as conexoes pra nao precisar subir mongo/rabbit/kafka nos testes
    with patch("app.main.connect_services_with_retry", AsyncMock()), \
         patch("app.main.close_mongo_connection", AsyncMock()), \
         patch("app.main.rabbitmq_publisher", AsyncMock()) as mock_rmq, \
         patch("app.main.kafka_publisher", AsyncMock()) as mock_kafka, \
         patch("app.main.get_collection") as mock_get_coll:

        mock_collection = AsyncMock()
        mock_get_coll.return_value = mock_collection

        yield {
            "rabbitmq": mock_rmq,
            "kafka": mock_kafka,
            "collection": mock_collection
        }


@pytest.mark.asyncio
async def test_criar_pedido(mock_external_services):
    from app.main import app

    mock_coll = mock_external_services["collection"]
    mock_coll.insert_one = AsyncMock()

    payload = {
        "client_name": "Maria Silva",
        "product_name": "Celular",
        "quantity": 1
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/pedidos", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["client_name"] == "Maria Silva"
    assert data["product_name"] == "Celular"
    assert data["quantity"] == 1
    assert data["status"] == "PENDENTE"
    assert "id" in data

    # checa se salvou no mongo
    mock_coll.insert_one.assert_called_once()

    # checa se publicou no rabbitmq
    mock_rmq = mock_external_services["rabbitmq"]
    mock_rmq.publish_order_created.assert_called_once_with(data["id"])

    # checa se publicou no kafka
    mock_kafka = mock_external_services["kafka"]
    mock_kafka.publish_order_event.assert_called_once_with("pedido_criado", data)


@pytest.mark.asyncio
async def test_listar_pedidos(mock_external_services):
    from app.main import app

    mock_docs = [
        {
            "_id": "order-1",
            "client_name": "Maria",
            "product_name": "Celular",
            "quantity": 1,
            "status": "PENDENTE"
        },
        {
            "_id": "order-2",
            "client_name": "João",
            "product_name": "Teclado",
            "quantity": 2,
            "status": "PENDENTE"
        }
    ]

    # simula o cursor async do motor
    class AsyncIterator:
        def __init__(self, items):
            self.items = items

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)

    mock_coll = mock_external_services["collection"]
    mock_coll.find = MagicMock(return_value=AsyncIterator(mock_docs))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/pedidos")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "order-1"
    assert data[0]["client_name"] == "Maria"
    assert data[1]["id"] == "order-2"
    assert data[1]["client_name"] == "João"
