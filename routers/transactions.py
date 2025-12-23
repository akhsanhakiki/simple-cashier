from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List

from database import get_session
from models import (
    Product,
    Transaction, TransactionCreate, TransactionRead,
    TransactionItem, TransactionItemRead
)

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction_in: TransactionCreate, session: Session = Depends(get_session)):
    """
    Create a new transaction with items.
    Optimized: Loads all products in a single query instead of N queries.
    Uses a single commit instead of two separate commits.
    """
    # Load all products in one query instead of N queries (fixes N+1)
    product_ids = [item.product_id for item in transaction_in.items]
    if not product_ids:
        raise HTTPException(status_code=400, detail="Transaction must have at least one item")
    
    products = session.exec(
        select(Product).where(Product.id.in_(product_ids))
    ).all()
    product_dict = {p.id: p for p in products}
    
    # Validate all products exist
    missing_ids = set(product_ids) - set(product_dict.keys())
    if missing_ids:
        raise HTTPException(
            status_code=404, 
            detail=f"Products not found: {', '.join(map(str, missing_ids))}"
        )
    
    # Validate stock and calculate total
    total_amount = 0.0
    transaction_items = []
    
    for item_in in transaction_in.items:
        product = product_dict[item_in.product_id]
        
        if product.stock < item_in.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough stock for product '{product.name}'. Available: {product.stock}, Requested: {item_in.quantity}"
            )
        
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
    
    # Create Transaction and items in a single commit (optimization)
    db_transaction = Transaction(total_amount=total_amount)
    session.add(db_transaction)
    session.flush()  # Get ID without committing
    
    # Associate items with transaction
    for item in transaction_items:
        item.transaction_id = db_transaction.id
        session.add(item)
    
    # Single commit instead of two separate commits
    session.commit()
    session.refresh(db_transaction)
    
    # Build response using cached product data (no additional queries)
    return_items = []
    for item in db_transaction.items:
        product = product_dict[item.product_id]
        return_items.append(TransactionItemRead(
            id=item.id,
            quantity=item.quantity,
            price=item.price,
            product_id=item.product_id,
            transaction_id=item.transaction_id,
            product_name=product.name  # Use cached product, no N+1 query
        ))
    
    return TransactionRead(
        id=db_transaction.id,
        total_amount=db_transaction.total_amount,
        created_at=db_transaction.created_at,
        items=return_items
    )

@router.get("/", response_model=List[TransactionRead])
def read_transactions(offset: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """
    Get a list of transactions with pagination.
    Optimized: Uses eager loading to prevent N+1 queries.
    """
    # Eager load items and products in one query (fixes N+1)
    statement = (
        select(Transaction)
        .offset(offset)
        .limit(limit)
        .options(
            selectinload(Transaction.items).selectinload(TransactionItem.product)
        )
    )
    transactions = session.exec(statement).all()
    
    # Build response - products are already loaded, no additional queries
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
                product_name=item.product.name  # Already loaded, no N+1 query
            ))
        results.append(TransactionRead(
            id=txn.id,
            total_amount=txn.total_amount,
            created_at=txn.created_at,
            items=items
        ))
    return results

@router.get("/{transaction_id}", response_model=TransactionRead)
def read_transaction(transaction_id: int, session: Session = Depends(get_session)):
    """
    Get a single transaction by ID.
    Optimized: Uses eager loading to prevent N+1 queries.
    """
    # Eager load items and products in one query (fixes N+1)
    statement = (
        select(Transaction)
        .where(Transaction.id == transaction_id)
        .options(
            selectinload(Transaction.items).selectinload(TransactionItem.product)
        )
    )
    txn = session.exec(statement).first()
    
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Build response - products are already loaded, no additional queries
    items = []
    for item in txn.items:
        items.append(TransactionItemRead(
            id=item.id,
            quantity=item.quantity,
            price=item.price,
            product_id=item.product_id,
            transaction_id=item.transaction_id,
            product_name=item.product.name  # Already loaded, no N+1 query
        ))
    
    return TransactionRead(
        id=txn.id,
        total_amount=txn.total_amount,
        created_at=txn.created_at,
        items=items
    )

