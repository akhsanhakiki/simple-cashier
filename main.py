from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from database import create_db_and_tables, get_session
from models import (
    Product, ProductCreate, ProductRead, ProductUpdate,
    Transaction, TransactionCreate, TransactionRead,
    TransactionItem, TransactionItemCreate, TransactionItemRead
)

app = FastAPI(title="Simple Cashier API")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Product Endpoints

@app.post("/products/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    db_product = Product.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[ProductRead])
def read_products(offset: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    products = session.exec(select(Product).offset(offset).limit(limit)).all()
    return products

@app.get("/products/{product_id}", response_model=ProductRead)
def read_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, product: ProductUpdate, session: Session = Depends(get_session)):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = product.model_dump(exclude_unset=True)
    for key, value in product_data.items():
        setattr(db_product, key, value)
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"ok": True}

# Transaction Endpoints

@app.post("/transactions/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction_in: TransactionCreate, session: Session = Depends(get_session)):
    # 1. Validate items and calculate total
    total_amount = 0.0
    transaction_items = []
    
    for item_in in transaction_in.items:
        product = session.get(Product, item_in.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with id {item_in.product_id} not found")
        
        if product.stock < item_in.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for product '{product.name}'")
        
        # Deduct stock
        product.stock -= item_in.quantity
        session.add(product)
        
        # Calculate item price total and add to transaction total
        item_total = product.price * item_in.quantity
        total_amount += item_total
        
        # Create TransactionItem (not saved yet)
        db_item = TransactionItem(
            product_id=product.id,
            quantity=item_in.quantity,
            price=product.price
        )
        transaction_items.append(db_item)
    
    # 2. Create Transaction
    db_transaction = Transaction(total_amount=total_amount)
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    
    # 3. Associate items with transaction and save them
    for item in transaction_items:
        item.transaction_id = db_transaction.id
        session.add(item)
    
    session.commit()
    session.refresh(db_transaction)
    
    # Prepare response (fetching product names for read model)
    # We reload items to ensure relationships are populated if needed, 
    # though session.refresh should handle the immediate fields.
    # For the response model, we need to construct TransactionRead manually or ensure relationships work.
    
    return_items = []
    for item in db_transaction.items:
        # We assume product is loaded or lazy loaded
        return_items.append(TransactionItemRead(
            id=item.id,
            quantity=item.quantity,
            price=item.price,
            product_id=item.product_id,
            transaction_id=item.transaction_id,
            product_name=item.product.name # This triggers a fetch if not loaded
        ))

    return TransactionRead(
        id=db_transaction.id,
        total_amount=db_transaction.total_amount,
        created_at=db_transaction.created_at,
        items=return_items
    )

@app.get("/transactions/", response_model=List[TransactionRead])
def read_transactions(offset: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    transactions = session.exec(select(Transaction).offset(offset).limit(limit)).all()
    
    # Convert to Read model to include nested details
    results = []
    for txn in transactions:
        items = []
        for item in txn.items:
            items.append(TransactionItemRead(
                id=item.id,
                quantity=item.quantity,
                price=item.price,
                product_id=item.product_id,
                transaction_id=item.transaction_id,
                product_name=item.product.name
            ))
        results.append(TransactionRead(
            id=txn.id,
            total_amount=txn.total_amount,
            created_at=txn.created_at,
            items=items
        ))
    return results

@app.get("/transactions/{transaction_id}", response_model=TransactionRead)
def read_transaction(transaction_id: int, session: Session = Depends(get_session)):
    txn = session.get(Transaction, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    items = []
    for item in txn.items:
        items.append(TransactionItemRead(
            id=item.id,
            quantity=item.quantity,
            price=item.price,
            product_id=item.product_id,
            transaction_id=item.transaction_id,
            product_name=item.product.name
        ))
    return TransactionRead(
        id=txn.id,
        total_amount=txn.total_amount,
        created_at=txn.created_at,
        items=items
    )
