from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from database import get_session
from models import (
    Product, ProductCreate, ProductRead, ProductUpdate
)

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    """Create a new product."""
    db_product = Product.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@router.get("/", response_model=List[ProductRead])
def read_products(offset: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """Get a list of products with pagination."""
    products = session.exec(select(Product).offset(offset).limit(limit)).all()
    return products

@router.get("/{product_id}", response_model=ProductRead)
def read_product(product_id: int, session: Session = Depends(get_session)):
    """Get a single product by ID."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, product: ProductUpdate, session: Session = Depends(get_session)):
    """Update a product by ID."""
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

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: Session = Depends(get_session)):
    """Delete a product by ID."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return None

