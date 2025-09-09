import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from shared.utils.response_envelope import ResponseEnvelope, ErrorDetail
from shared.utils.response_wrapper import envelope_response, create_error_response
from shared.middleware.exception_handlers import register_exception_handlers


class TestResponseEnvelope:
    """Tests for the ResponseEnvelope class."""
    
    def test_success_response(self):
        """Test creating a success response."""
        data = {"key": "value"}
        response = ResponseEnvelope.success_response(data=data)
        
        assert response.success is True
        assert response.data == data
        assert response.error is None
    
    def test_error_response(self):
        """Test creating an error response."""
        code = "TEST_ERROR"
        message = "Test error message"
        details = {"field": "value"}
        
        response = ResponseEnvelope.error_response(
            code=code,
            message=message,
            details=details
        )
        
        assert response.success is False
        assert response.data is None
        assert response.error is not None
        assert response.error.code == code
        assert response.error.message == message
        assert response.error.details == details
    
    def test_error_response_without_details(self):
        """Test creating an error response without details."""
        code = "TEST_ERROR"
        message = "Test error message"
        
        response = ResponseEnvelope.error_response(
            code=code,
            message=message
        )
        
        assert response.success is False
        assert response.data is None
        assert response.error is not None
        assert response.error.code == code
        assert response.error.message == message
        assert response.error.details is None


class TestExceptionHandlers:
    """Tests for the exception handlers."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app with exception handlers registered."""
        app = FastAPI()
        register_exception_handlers(app)
        
        @app.get("/http-exception")
        async def http_exception():
            raise HTTPException(status_code=404, detail="Not found")
        
        @app.get("/validation-error")
        async def validation_error():
            class Model(BaseModel):
                value: int
            
            # This will raise a validation error
            return Model(value="not an int")
        
        @app.get("/unhandled-exception")
        async def unhandled_exception():
            # This will raise a division by zero error
            return 1 / 0
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client for the app."""
        return TestClient(app)
    
    def test_http_exception_handler(self, client):
        """Test the HTTP exception handler."""
        response = client.get("/http-exception")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == "HTTP_ERROR_404"
        assert data["error"]["message"] == "Not found"
    
    def test_validation_exception_handler(self, client):
        """Test the validation exception handler."""
        response = client.get("/validation-error")
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "errors" in data["error"]["details"]
    
    def test_unhandled_exception_handler(self, client):
        """Test the unhandled exception handler."""
        response = client.get("/unhandled-exception")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == "SERVER_ERROR"
        assert data["error"]["message"] == "An unexpected error occurred"
        assert data["error"]["details"]["type"] == "ZeroDivisionError"


class TestResponseWrapper:
    """Tests for the response wrapper decorator."""
    
    @pytest.fixture
    def app(self):
        """Create a FastAPI app with test routes."""
        app = FastAPI()
        
        @app.get("/wrapped")
        @envelope_response
        async def wrapped_route():
            return {"message": "Hello, World!"}
        
        @app.get("/error")
        async def error_route():
            return create_error_response(
                code="TEST_ERROR",
                message="Test error message",
                status_code=400,
                details={"field": "value"}
            )
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client for the app."""
        return TestClient(app)
    
    def test_envelope_response_decorator(self, client):
        """Test the envelope_response decorator."""
        response = client.get("/wrapped")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["message"] == "Hello, World!"
        assert data["error"] is None
    
    def test_create_error_response(self, client):
        """Test the create_error_response function."""
        response = client.get("/error")
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["error"]["message"] == "Test error message"
        assert data["error"]["details"]["field"] == "value"