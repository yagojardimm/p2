from pydantic import BaseModel, Field
from enum import Enum

class OrderStatus(str, Enum):
    PENDENTE = "PENDENTE"

class OrderCreate(BaseModel):
    client_name: str = Field(..., min_length=1, description="Nome do cliente")
    product_name: str = Field(..., min_length=1, description="Nome do produto")
    quantity: int = Field(..., gt=0, description="Quantidade de itens do pedido")

class Order(BaseModel):
    id: str = Field(..., description="Identificador único do pedido")
    client_name: str
    product_name: str
    quantity: int
    status: OrderStatus = OrderStatus.PENDENTE
