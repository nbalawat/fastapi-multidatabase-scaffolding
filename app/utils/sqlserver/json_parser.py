import logging
import json
from typing import Any, List

logger = logging.getLogger(__name__)

def parse_json_string(value: Any, field_name: str = "unknown") -> List[Any]:
    """Parse a SQL Server JSON string into a Python list with error handling.
    
    Args:
        value: The JSON string to parse (could be a string, list, or other format)
        field_name: The name of the field being parsed (for logging)
        
    Returns:
        The parsed list or an empty list if parsing fails
    """
    logger.info(f"Parsing SQL Server JSON for {field_name}: {value}")
    
    # If it's already a list, return it
    if isinstance(value, list):
        return value
        
    # If it's None or empty, return an empty list
    if value is None or (isinstance(value, str) and not value.strip()):
        return []
    
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            # Try to parse as JSON first
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    logger.info(f"Successfully parsed {field_name} as JSON list: {parsed}")
                    return parsed
                elif isinstance(parsed, dict):
                    logger.info(f"Parsed {field_name} as JSON object, converting to list: {[parsed]}")
                    return [parsed]
            except json.JSONDecodeError:
                # Not valid JSON, try other parsing methods
                pass
                
            # Try to handle comma-separated strings
            if ',' in value:
                items = [item.strip() for item in value.split(',') if item.strip()]
                logger.info(f"Parsed {field_name} as comma-separated string: {items}")
                return items
            else:
                # Single value, return as a list with one item
                logger.info(f"Treating {field_name} as single value: {value}")
                return [value]
        except Exception as e:
            logger.error(f"Error parsing {field_name}: {e}, raw value: {value}")
    
    # For any other type, try to convert to string and parse
    try:
        str_value = str(value)
        if str_value:
            logger.info(f"Converting {field_name} to string and parsing: {str_value}")
            return [str_value]
    except Exception as e:
        logger.error(f"Error converting {field_name} to string: {e}")
    
    # Return empty list as fallback
    return []
