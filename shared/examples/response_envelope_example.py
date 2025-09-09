from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

# Import the shared response envelope components
from shared.utils.response_envelope import ResponseEnvelope
from shared.utils.response_wrapper import envelope_response, create_error_response
from shared.middleware.exception_handlers import register_exception_handlers

# Create a FastAPI app
app = FastAPI(title="Response Envelope Example")

# Register the exception handlers
register_exception_handlers(app)

# Example models
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

# Mock database
items_db = [
    Item(id=1, name="Item 1", description="Description for Item 1", price=10.5),
    Item(id=2, name="Item 2", price=20.0),
    Item(id=3, name="Item 3", description="Description for Item 3", price=30.75),
]

# Example routes
@app.get("/items", response_model=ResponseEnvelope[List[Item]])
@envelope_response
async def get_items():
    """Get all items using the envelope_response decorator.
    
    The decorator automatically wraps the return value in a ResponseEnvelope.
    """
    return items_db

@app.get("/items/{item_id}", response_model=ResponseEnvelope[Item])
@envelope_response
async def get_item(item_id: int):
    """Get a specific item by ID using the envelope_response decorator.
    
    The decorator automatically wraps the return value in a ResponseEnvelope.
    If the item is not found, an HTTPException is raised, which will be caught
    by the registered exception handler and converted to an error response.
    """
    for item in items_db:
        if item.id == item_id:
            return item
    
    # This will be caught by the http_exception_handler
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Item with ID {item_id} not found"
    )

@app.post("/items", response_model=ResponseEnvelope[Item], status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    """Create a new item with manual response envelope creation.
    
    This example shows how to manually create a ResponseEnvelope without using the decorator.
    """
    # Check if item with this ID already exists
    for existing_item in items_db:
        if existing_item.id == item.id:
            # Using the create_error_response helper function
            return create_error_response(
                code="DUPLICATE_ITEM",
                message=f"Item with ID {item.id} already exists",
                status_code=status.HTTP_409_CONFLICT,
                details={"existing_item": existing_item.dict()}
            )
    
    # Add the item to the database
    items_db.append(item)
    
    # Manually create a success response
    return ResponseEnvelope.success_response(data=item)

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item by ID with manual response envelope creation.
    
    This example shows how to manually create different types of ResponseEnvelopes.
    """
    for i, item in enumerate(items_db):
        if item.id == item_id:
            deleted_item = items_db.pop(i)
            # Return a success response with the deleted item
            return ResponseEnvelope.success_response(
                data={"message": f"Item {item_id} deleted", "item": deleted_item}
            )
    
    # Return an error response for item not found
    return ResponseEnvelope.error_response(
        code="ITEM_NOT_FOUND",
        message=f"Item with ID {item_id} not found",
        details={"available_ids": [item.id for item in items_db]}
    )

# Example of a route that will trigger a validation error
@app.get("/validation-error-example")
async def validation_error_example():
    """This route will trigger a validation error.
    
    The error will be caught by the validation_exception_handler and converted
    to an error response.
    """
    # This will cause a validation error when Pydantic tries to parse it
    return Item(id="not-an-integer", name=123, price="not-a-float")

# Example of a route that will trigger an unhandled exception
@app.get("/unhandled-error-example")
async def unhandled_error_example():
    """This route will trigger an unhandled exception.
    
    The error will be caught by the unhandled_exception_handler and converted
    to an error response.
    """
    # This will cause a division by zero error
    return 1 / 0

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)