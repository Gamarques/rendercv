"""
RenderCV Frontend - YAML Serializer

This module handles conversion from internal JSON state to RenderCV-compatible YAML.

Key responsibilities:
- Clean internal UI fields (_ui_id, _type)
- Convert Python dicts to YAML with proper formatting
- Preserve multiline strings using YAML block scalars
- Validate structure before serialization
"""

from typing import Dict, Any, List, Tuple, Optional
from ruamel.yaml import YAML
from io import StringIO
import copy


def clean_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove internal UI fields and empty values from an entry.
    
    Internal fields start with underscore (_ui_id, _type, etc.)
    These are used for UI state management but should not appear in YAML.
    
    Also removes empty strings and empty lists to avoid RenderCV validation errors.
    
    Args:
        entry: Entry dictionary with possible internal fields
        
    Returns:
        Cleaned entry without internal fields or empty values
    """
    cleaned = {}
    for k, v in entry.items():
        # Skip internal fields
        if k.startswith('_'):
            continue
        # Skip empty strings (RenderCV doesn't accept empty dates)
        if v == '':
            continue
        # Skip empty lists
        if isinstance(v, list) and len(v) == 0:
            continue
        # Keep the field
        cleaned[k] = v
    return cleaned


def clean_cv_data(cv_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean entire CV data structure, removing internal fields.
    
    Args:
        cv_data: Raw CV data from session state
        
    Returns:
        Cleaned CV data ready for YAML serialization
    """
    cleaned = copy.deepcopy(cv_data)
    
    # Clean sections
    if 'sections' in cleaned:
        for section_key, entries in cleaned['sections'].items():
            if isinstance(entries, list):
                cleaned['sections'][section_key] = [
                    clean_entry(entry) for entry in entries
                ]
    
    # Remove empty optional fields
    fields_to_check = ['headline', 'location', 'email', 'phone', 'website', 'photo']
    for field in fields_to_check:
        if field in cleaned and not cleaned[field]:
            del cleaned[field]
    
    # Remove empty lists
    if 'social_networks' in cleaned and not cleaned['social_networks']:
        del cleaned['social_networks']
    if 'custom_connections' in cleaned and not cleaned['custom_connections']:
        del cleaned['custom_connections']
    
    return cleaned


def serialize_to_yaml(document: Dict[str, Any]) -> str:
    """
    Convert RenderCV document to YAML string.
    
    Uses ruamel.yaml to preserve formatting and use proper YAML features:
    - Block scalars (|, >) for multiline strings
    - Proper list formatting
    - Maintains order
    
    Args:
        document: Complete RenderCV document with cv, design, locale, settings
        
    Returns:
        YAML string ready to send to RenderCV
    """
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.width = 4096  # Prevent line wrapping
    
    # Clean the CV section
    if 'cv' in document:
        document['cv'] = clean_cv_data(document['cv'])
    
    # Remove empty sections
    if 'design' in document:
        # Remove None values from design
        document['design'] = {k: v for k, v in document['design'].items() if v is not None}
        if not document['design'] or document['design'] == {'theme': 'classic'}:
            # Keep minimal design
            document['design'] = {'theme': document['design'].get('theme', 'classic')}
    
    if 'locale' in document:
        document['locale'] = {k: v for k, v in document['locale'].items() if v is not None}
        if not document['locale'] or document['locale'] == {'language': 'english'}:
            document['locale'] = {'language': document['locale'].get('language', 'english')}
    
    if 'settings' in document:
        document['settings'] = {k: v for k, v in document['settings'].items() if v is not None}
        if not document['settings']:
            del document['settings']
    
    # Serialize to YAML
    stream = StringIO()
    yaml.dump(document, stream)
    yaml_str = stream.getvalue()
    
    return yaml_str


def create_rendercv_document(cv_data: Dict[str, Any], 
                             design_data: Optional[Dict[str, Any]] = None,
                             locale_data: Optional[Dict[str, Any]] = None,
                             settings_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a complete RenderCV document from separate components.
    
    Args:
        cv_data: CV data (name, sections, etc.)
        design_data: Design configuration (theme, colors, etc.)
        locale_data: Locale settings (language, date format, etc.)
        settings_data: Rendering settings
        
    Returns:
        Complete RenderCV document structure
    """
    document = {
        'cv': cv_data,
        'design': design_data or {'theme': 'classic'},
        'locale': locale_data or {'language': 'english'},
    }
    
    if settings_data:
        document['settings'] = settings_data
    
    return document


def validate_cv_structure(cv_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate CV structure before serialization.
    
    Checks:
    - Required fields are present
    - Sections are properly formatted
    - Entries have required fields based on type
    
    Args:
        cv_data: CV data to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    if not cv_data.get('name'):
        errors.append("CV name is required")
    
    # Validate sections
    sections = cv_data.get('sections', {})
    if not isinstance(sections, dict):
        errors.append("Sections must be a dictionary")
        return False, errors
    
    for section_key, entries in sections.items():
        if not isinstance(entries, list):
            errors.append(f"Section '{section_key}' must contain a list of entries")
            continue
        
        # Check each entry
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"Entry {i+1} in section '{section_key}' must be a dictionary")
                continue
            
            # Get entry type (if stored internally)
            entry_type = entry.get('_type', 'NormalEntry')
            
            # Import here to avoid circular dependency
            from models import get_required_fields
            
            required_fields = get_required_fields(entry_type)
            for field in required_fields:
                if field not in entry or not entry[field]:
                    errors.append(
                        f"Entry {i+1} in section '{section_key}' is missing required field: {field}"
                    )
    
    is_valid = len(errors) == 0
    return is_valid, errors


def yaml_to_dict(yaml_str: str) -> Dict[str, Any]:
    """
    Parse YAML string to Python dictionary.
    Useful for loading existing CV files.
    
    Args:
        yaml_str: YAML content as string
        
    Returns:
        Parsed dictionary
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    return yaml.load(yaml_str)


# Example usage
if __name__ == "__main__":
    # Test serialization
    test_cv = {
        "name": "John Doe",
        "email": "john@example.com",
        "sections": {
            "experience": [
                {
                    "_ui_id": "123",
                    "_type": "ExperienceEntry",
                    "company": "Tech Corp",
                    "position": "Developer",
                    "start_date": "2020-01",
                    "end_date": "present",
                    "highlights": [
                        "Built awesome features",
                        "Improved performance by 50%"
                    ]
                }
            ]
        }
    }
    
    document = create_rendercv_document(test_cv)
    yaml_output = serialize_to_yaml(document)
    print(yaml_output)
