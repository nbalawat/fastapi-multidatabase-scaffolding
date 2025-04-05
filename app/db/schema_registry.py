from typing import Dict, Type, Optional, List, Any
import logging
from importlib import import_module
from pathlib import Path

from app.db.schemas.base import BaseSchema

logger = logging.getLogger(__name__)

class SchemaRegistry:
    """Registry for database schemas.
    
    This class manages the database schemas for all models and provides
    methods for schema validation and database initialization.
    """
    
    def __init__(self):
        """Initialize the schema registry."""
        self._schemas: Dict[str, Dict[str, BaseSchema]] = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize the schema registry by discovering all schemas."""
        if self._initialized:
            return
            
        self._discover_schemas()
        self._initialized = True
    
    def _discover_schemas(self):
        """Discover all schemas in the schemas directory."""
        # Get the base directory for schemas
        schemas_dir = Path(__file__).parent / "schemas"
        
        # First, try to discover schemas organized by model then database type (preferred structure)
        for model_dir in schemas_dir.iterdir():
            if not model_dir.is_dir() or model_dir.name == "__pycache__":
                continue
                
            model_name = model_dir.name
            
            # Discover all database schemas for this model
            for schema_file in model_dir.glob("*.py"):
                if schema_file.name == "__init__.py":
                    continue
                    
                # The database type is the filename without extension
                db_type = schema_file.stem
                
                # Skip if not a valid database type
                if db_type not in ["postgres", "mongodb", "sqlserver"]:
                    continue
                    
                self._load_schema_from_file(model_name, db_type, schema_file)
        
        # Also support the legacy structure (organized by database type then model)
        # This ensures backward compatibility
        for db_type_dir in schemas_dir.iterdir():
            if not db_type_dir.is_dir() or db_type_dir.name == "__pycache__" or db_type_dir.name in ["users", "notes"]:
                continue
                
            db_type = db_type_dir.name
            
            # Discover all model schemas for this database type
            for schema_file in db_type_dir.glob("*.py"):
                if schema_file.name == "__init__.py":
                    continue
                    
                model_name = schema_file.stem
                
                self._load_schema_from_file(model_name, db_type, schema_file)
    
    def _load_schema_from_file(self, model_name: str, db_type: str, schema_file: Path):
        """Load a schema from a file.
        
        Args:
            model_name: The model name
            db_type: The database type
            schema_file: The schema file path
        """
        try:
            # Determine the module path based on the file structure
            if schema_file.parent.name == db_type:
                # Legacy structure: app/db/schemas/postgres/notes.py
                module_path = f"app.db.schemas.{db_type}.{model_name}"
            else:
                # New structure: app/db/schemas/notes/postgres.py
                module_path = f"app.db.schemas.{model_name}.{db_type}"
            
            # Import the schema module
            module = import_module(module_path)
            
            # Find the schema class in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseSchema) and 
                    attr != BaseSchema):
                    
                    # Create an instance of the schema
                    schema = attr()
                    
                    # Add the schema to the registry
                    if model_name not in self._schemas:
                        self._schemas[model_name] = {}
                    
                    self._schemas[model_name][db_type] = schema
                    logger.info(f"Registered schema for {model_name} with {db_type}")
                    
        except Exception as e:
            logger.error(f"Error loading schema for {model_name} with {db_type}: {e}")
    
    def get_schema(self, model_name: str, db_type: str) -> Optional[BaseSchema]:
        """Get the schema for a model and database type.
        
        Args:
            model_name: The model name
            db_type: The database type
            
        Returns:
            The schema or None if not found
        """
        if not self._initialized:
            self.initialize()
            
        return self._schemas.get(model_name, {}).get(db_type)
    
    def get_all_schemas(self) -> Dict[str, Dict[str, BaseSchema]]:
        """Get all schemas.
        
        Returns:
            Dictionary of all schemas
        """
        if not self._initialized:
            self.initialize()
            
        return self._schemas
    
    def get_schemas_for_model(self, model_name: str) -> Dict[str, BaseSchema]:
        """Get all schemas for a model.
        
        Args:
            model_name: The model name
            
        Returns:
            Dictionary of schemas for the model
        """
        if not self._initialized:
            self.initialize()
            
        return self._schemas.get(model_name, {})
    
    def get_schemas_for_db_type(self, db_type: str) -> Dict[str, BaseSchema]:
        """Get all schemas for a database type.
        
        Args:
            db_type: The database type
            
        Returns:
            Dictionary of schemas for the database type
        """
        if not self._initialized:
            self.initialize()
            
        return {
            model_name: schemas.get(db_type)
            for model_name, schemas in self._schemas.items()
            if db_type in schemas
        }
    
    def has_schema(self, model_name: str, db_type: str) -> bool:
        """Check if a schema exists for a model and database type.
        
        Args:
            model_name: The model name
            db_type: The database type
            
        Returns:
            True if the schema exists, False otherwise
        """
        if not self._initialized:
            self.initialize()
            
        return model_name in self._schemas and db_type in self._schemas[model_name]
    
    def get_create_table_statements(self, db_type: str) -> Dict[str, str]:
        """Get all create table statements for a database type.
        
        Args:
            db_type: The database type
            
        Returns:
            Dictionary of create table statements
        """
        if not self._initialized:
            self.initialize()
            
        return {
            model_name: schema.get_create_table_statement()
            for model_name, schema in self.get_schemas_for_db_type(db_type).items()
        }

# Create a singleton instance
schema_registry = SchemaRegistry()

def get_schema_registry() -> SchemaRegistry:
    """Get the schema registry instance."""
    return schema_registry
