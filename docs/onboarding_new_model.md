# Onboarding a New Model

This guide outlines the step-by-step process for adding a new model to the application. Following these steps will ensure that your model integrates properly with the existing architecture and follows the established design patterns.

## Prerequisites

Before starting, ensure you have:

- A clear understanding of the model's purpose and requirements
- Familiarity with FastAPI and Pydantic
- Knowledge of the application's database structure

## Step 1: Define the Model

Create a new directory for your model under `app/models/`. For example, if you're creating a "Product" model:

```bash
mkdir -p app/models/products
touch app/models/products/__init__.py
touch app/models/products/model.py
touch app/models/products/controller.py
touch app/models/products/router.py
```

In `model.py`, define your Pydantic models:

```python
"""Models for products."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from uuid import UUID

class ProductCategory(str, Enum):
    """Product categories."""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    OTHER = "other"

class ProductBase(BaseModel):
    """Base model for products with common fields."""
    name: str
    description: str
    price: float
    category: ProductCategory = ProductCategory.OTHER
    tags: List[str] = Field(default_factory=list)
    
class ProductCreate(ProductBase):
    """Model for creating a new product."""
    user_id: Optional[str] = None
    
class ProductUpdate(BaseModel):
    """Model for updating an existing product."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[ProductCategory] = None
    tags: Optional[List[str]] = None
    
class ProductInDB(ProductBase):
    """Model for product as stored in the database."""
    id: str
    user_id: Union[str, UUID]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }
        
class Product(ProductInDB):
    """Model for product as returned by the API."""
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "5f8d0d55b54764421b7056f0",
                "name": "Sample Product",
                "description": "This is a sample product",
                "price": 29.99,
                "category": "electronics",
                "tags": ["sample", "product"],
                "user_id": "5f8d0d55b54764421b7056f1",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00"
            }
        }
    }
```

## Step 2: Create the Controller

In `controller.py`, implement the controller for your model:

```python
"""Controller for products."""
from typing import Dict, List, Any, Optional
from app.utils.generic.base_controller import BaseController
from app.models.products.model import ProductCreate, ProductUpdate, Product, ProductInDB
from app.models.users.model import User

class ProductsController(BaseController[ProductCreate, ProductUpdate, Product]):
    """Controller for products."""
    
    def __init__(self, db_adapter):
        """Initialize the controller with a database adapter."""
        super().__init__(db_adapter)
        self.collection = "products"  # Set the collection name
    
    # Override base methods for model-specific logic if needed
    def _preprocess_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess data before creating a record."""
        # Ensure tags is a list
        if "tags" not in data or data["tags"] is None:
            data["tags"] = []
        return data
    
    # Add custom methods specific to this model
    async def create_with_user(self, data: ProductCreate, user: User) -> Dict[str, Any]:
        """Create a new product with the current user's ID."""
        # Convert Pydantic model to dict if needed
        if hasattr(data, "model_dump"):
            # Pydantic v2
            data_dict = data.model_dump()
        elif hasattr(data, "dict"):
            # Pydantic v1
            data_dict = data.dict()
        else:
            # Already a dict
            data_dict = dict(data)
            
        # Set the user_id from the authenticated user
        # We now have the user ID from the token, but ensure it's a string
        data_dict["user_id"] = str(user.id) if hasattr(user.id, 'hex') else user.id
        
        # Use the existing create method with the updated data
        return await self.create(data_dict)
    
    async def search_by_name(self, query: str) -> List[Dict[str, Any]]:
        """Search products by name."""
        all_products = await self.list(0, 1000)
        return [product for product in all_products 
                if query.lower() in product.get("name", "").lower()]
    
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products by category."""
        return await self.list(0, 1000, {"category": category})
```

## Step 3: Implement the Router

In `router.py`, create the API endpoints for your model:

```python
"""Router for products."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from app.models.products.model import ProductCreate, ProductUpdate, Product
from app.models.products.controller import ProductsController
from app.api.dependencies.db import get_db_adapter
from app.api.dependencies import get_current_active_user
from app.models.users.model import User
from app.utils.generic.router_utils import create_standard_routes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])

# Option 1: Use create_standard_routes for standard CRUD operations
create_standard_routes(
    router=router,
    controller_class=ProductsController,
    create_model=ProductCreate,
    update_model=ProductUpdate,
    response_model=Product,
    get_db_adapter=get_db_adapter
)

# Option 2: Create custom routes with authentication
# Uncomment and use this approach if you need custom behavior

# @router.post("/", response_model=Product)
# async def create_product(
#     product: ProductCreate,
#     db_adapter=Depends(get_db_adapter),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """Create a new product with the current user's ID."""
#     controller = ProductsController(db_adapter)
#     result = await controller.create_with_user(product, current_user)
#     return result

# Add custom routes
@router.get("/search/{query}", response_model=List[Product])
async def search_products(
    query: str,
    db_adapter=Depends(get_db_adapter)
):
    """Search products by name."""
    controller = ProductsController(db_adapter)
    result = await controller.search_by_name(query)
    return result

@router.get("/by-category/{category}", response_model=List[Product])
async def get_products_by_category(
    category: str,
    skip: int = 0,
    limit: int = 100,
    db_adapter=Depends(get_db_adapter)
):
    """Get products by category."""
    controller = ProductsController(db_adapter)
    result = await controller.get_by_category(category)
    return result
```

## Step 4: Register the Router

Add your router to the API in `app/api/api.py`:

```python
from fastapi import APIRouter
from app.models.users.router import router as users_router
from app.models.notes.router import router as notes_router
from app.models.products.router import router as products_router  # Add this line

api_router = APIRouter()

api_router.include_router(users_router, prefix="/users")
api_router.include_router(notes_router, prefix="/notes")
api_router.include_router(products_router, prefix="/products")  # Add this line
```

## Step 5: Create Database Schema (Optional)

If your model requires specific database schema handling, create schema files in the appropriate database-specific directories:

For PostgreSQL (`app/schemas/postgres/products.py`):

```python
from app.schemas.base import BaseSchema

class ProductsSchema(BaseSchema):
    """Schema for products in PostgreSQL."""
    
    def to_db_model(self, data):
        """Convert API model to database model."""
        # Handle any PostgreSQL-specific conversions
        if "tags" in data and isinstance(data["tags"], list):
            # Convert Python list to PostgreSQL array
            data["tags"] = data["tags"]  # No conversion needed for PostgreSQL arrays
        return data
    
    def from_db_model(self, data):
        """Convert database model to API model."""
        # Handle any PostgreSQL-specific conversions
        return data
```

## Step 6: Register the Schema

Register your schema in `app/db/schema_registry.py`:

```python
# Import your schema
from app.schemas.postgres.products import ProductsSchema

# In the SchemaRegistry class, add to the _register_schemas method:
def _register_schemas(self):
    # Existing schemas...
    
    # Register products schema
    self.register_schema("products", "postgres", ProductsSchema())
    self.register_schema("products", "sqlserver", ProductsSchema())  # If using SQL Server
    # Add other database types as needed
```

## Step 7: Add Tests

Create tests for your model in `app/scripts/tests/`:

```python
# test_crud_postgres.py
import pytest
from app.models.products.controller import ProductsController
from app.models.products.model import ProductCreate

@pytest.mark.asyncio
async def test_create_product(postgres_db):
    """Test creating a product."""
    controller = ProductsController(postgres_db)
    
    # Create test data
    product_data = ProductCreate(
        name="Test Product",
        description="A test product",
        price=19.99,
        category="electronics",
        tags=["test", "product"]
    )
    
    # Create the product
    result = await controller.create(product_data)
    
    # Verify the result
    assert result is not None
    assert result["name"] == "Test Product"
    assert result["price"] == 19.99
    assert "id" in result
```

## Step 8: Update API Documentation

Update the Swagger documentation by adding appropriate descriptions to your models and endpoints.

## Step 9: Test Your API

Start the application and test your new endpoints using the Swagger UI or a tool like curl or Postman.

## Best Practices

1. **Follow Naming Conventions**: Use consistent naming for your models (e.g., `ProductCreate`, `ProductUpdate`, `Product`)
2. **Type Safety**: Always use proper type annotations
3. **Documentation**: Include docstrings for all classes and methods
4. **Validation**: Use Pydantic validators for complex validation logic
5. **UUID Handling**: Remember that the system automatically converts UUIDs to strings in responses
6. **Error Handling**: Implement appropriate error handling in your controller methods
7. **Testing**: Write comprehensive tests for all CRUD operations and custom methods

## Troubleshooting

### Common Issues

1. **Model Not Found**: Ensure your router is properly registered in `app/api/api.py`
2. **Database Errors**: Check that your schema is correctly registered and handles any database-specific conversions
3. **Validation Errors**: Verify that your Pydantic models have the correct field types and constraints
4. **UUID Conversion Issues**: Make sure your model properly handles UUID fields with `Union[str, UUID]`

### Debugging Tips

- Use logging to track the flow of data through your controller
- Check the API response for detailed validation errors
- Verify database queries using database tools or logging

## Conclusion

By following these steps, you'll have successfully onboarded a new model into the application. This approach ensures that your model integrates properly with the existing architecture and follows the established design patterns.

Remember that the application's architecture is designed to be flexible, so you can customize any part of this process to meet your specific requirements.
