import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="E-commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "E-commerce API is running"}

@app.get("/schema")
def get_schema_info():
    # Expose information that the database viewer can read
    return {
        "collections": [
            "user", "product", "order"
        ]
    }

@app.get("/api/products", response_model=List[Product])
def list_products(category: Optional[str] = None):
    filter_dict = {"category": category} if category else {}
    try:
        products = get_documents("product", filter_dict)
        # Convert ObjectId to string for any fields if needed
        for p in products:
            p.pop("_id", None)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class NewProduct(Product):
    pass

@app.post("/api/products", status_code=201)
def add_product(product: NewProduct):
    try:
        inserted_id = create_document("product", product)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders", status_code=201)
def create_order(order: Order):
    try:
        order_id = create_document("order", order)
        return {"id": order_id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["database_url"] = "✅ Set"
                response["database_name"] = db.name
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
