# API de Gerenciamento de Pedidos

Projeto desenvolvido para modernização arquitetural utilizando comunicação assíncrona orientada a eventos e persistência NoSQL.

## Tecnologias Utilizadas
- **Linguagem**: Python 3.10+
- **Framework Web**: FastAPI
- **Banco de Dados**: MongoDB (Motor assíncrono)
- **Mensageria**: RabbitMQ (aio-pika) e Kafka (aiokafka)
- **Testes**: Pytest e Pytest-Asyncio
- **Orquestração**: Docker Compose

## Estrutura do Projeto
- `app/models.py`: Esquemas de dados (Pydantic).
- `app/database.py`: Gerenciamento da conexão com MongoDB.
- `app/queue_publisher.py`: Publicação de mensagens no RabbitMQ.
- `app/kafka_publisher.py`: Publicação de eventos no Kafka.
- `app/main.py`: Endpoints (`/pedidos`) e lógica principal.
- `tests/test_api.py`: Testes automatizados com mocks.

## Como Executar

Certifique-se de ter o Docker e Docker Compose instalados na sua máquina.

1. Na raiz do projeto, suba todos os serviços:
```bash
docker compose up --build
```

2. Acesse a documentação iterativa da API no navegador:
```
http://localhost:8000/docs
```

## Testes Automatizados

O projeto possui testes unitários mockados, garantindo que a regra de negócios possa ser testada rapidamente sem subir contêineres:

```bash
# Crie e ative um ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Execute os testes
pytest
```

---
**Desenvolvido por Yago**
