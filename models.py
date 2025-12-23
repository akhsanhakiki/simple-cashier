from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

# Product Models
class ProductBase(SQLModel):
    name: str = Field(index=True)
    price: float
    description: Optional[str] = None
    stock: int = 0

class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_items: List["TransactionItem"] = Relationship(back_populates="product")

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int

class ProductUpdate(SQLModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    stock: Optional[int] = None

# Transaction Item Models
class TransactionItemBase(SQLModel):
    quantity: int
    price: float
    product_id: int = Field(foreign_key="product.id")

class TransactionItem(TransactionItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id")
    
    product: Product = Relationship(back_populates="transaction_items")
    transaction: Optional["Transaction"] = Relationship(back_populates="items")

class TransactionItemCreate(SQLModel):
    product_id: int
    quantity: int

class TransactionItemRead(TransactionItemBase):
    id: int
    product_name: str

# Transaction Models
class TransactionBase(SQLModel):
    total_amount: float

class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    items: List[TransactionItem] = Relationship(back_populates="transaction")

class TransactionCreate(SQLModel):
    items: List[TransactionItemCreate]
    created_at: Optional[datetime] = None

class TransactionRead(TransactionBase):
    id: int
    created_at: datetime
    items: List[TransactionItemRead]

