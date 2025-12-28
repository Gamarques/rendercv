"""
RenderCV Frontend - Data Models

This module defines all data structures for the RenderCV frontend application.
It follows the official RenderCV schema: https://github.com/rendercv/rendercv/blob/main/schema.json

Key concepts:
- CV: Main curriculum vitae data
- Design: Theme and template configuration
- Locale: Language and date formatting
- Settings: Rendering options
- Entry Types: Different types of CV entries (Education, Experience, etc.)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# CORE DATA MODELS
# ============================================================================

class CV(BaseModel):
    """
    Main CV data structure following RenderCV schema.
    Supports all standard fields plus arbitrary custom fields.
    """
    name: str = ""
    headline: Optional[str] = ""
    location: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    website: Optional[str] = ""
    photo: Optional[str] = ""
    social_networks: List[Dict[str, str]] = Field(default_factory=list)
    custom_connections: List[Dict[str, str]] = Field(default_factory=list)
    sections: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)


class Design(BaseModel):
    """
    Design configuration for CV rendering.
    Controls theme, colors, fonts, and layout.
    
    Note: page_size is NOT supported in RenderCV v2.6
    """
    theme: str = "classic"
    # Templates define custom Typst code for each entry type
    # Example: {"TextEntry": "custom typst code"}
    templates: Optional[Dict[str, str]] = None
    # Additional design options
    color: Optional[str] = None
    disable_page_numbering: Optional[bool] = None
    

class Locale(BaseModel):
    """
    Localization settings for CV rendering.
    Controls language, date formats, and text translations.
    """
    language: str = "english"
    date_style: Optional[str] = None
    # Custom translations for section headers, etc.
    translations: Optional[Dict[str, str]] = None


class Settings(BaseModel):
    """
    Rendering settings and output options.
    """
    current_date: Optional[str] = None
    bold_keywords: List[str] = Field(default_factory=list)
    # Output paths (usually handled by RenderCV, but can be customized)
    render_command: Optional[Dict[str, Any]] = None


class RenderCVDocument(BaseModel):
    """
    Complete RenderCV document structure.
    This is the root object that gets serialized to YAML.
    """
    cv: CV
    design: Design = Field(default_factory=Design)
    locale: Locale = Field(default_factory=Locale)
    settings: Settings = Field(default_factory=Settings)


# ============================================================================
# ENTRY TYPE DEFINITIONS
# ============================================================================
# These definitions drive the form generator in the UI.
# Each entry type has a schema defining its fields, labels, types, and requirements.

ENTRY_DEFINITIONS = {
    "EducationEntry": {
        "institution": {"label": "Institution", "required": True, "type": "text"},
        "area": {"label": "Area of Study", "required": True, "type": "text"},
        "degree": {"label": "Degree", "required": False, "type": "text"},
        "date": {"label": "Date", "required": False, "type": "text", "help": "Use this OR start_date/end_date"},
        "start_date": {"label": "Start Date", "required": False, "type": "text", "help": "YYYY-MM format"},
        "end_date": {"label": "End Date", "required": False, "type": "text", "help": "YYYY-MM or 'present'"},
        "location": {"label": "Location", "required": False, "type": "text"},
        "summary": {"label": "Summary", "required": False, "type": "textarea"},
        "highlights": {"label": "Highlights", "required": False, "type": "list", "help": "One per line"},
    },
    
    "ExperienceEntry": {
        "company": {"label": "Company", "required": True, "type": "text"},
        "position": {"label": "Position", "required": True, "type": "text"},
        "date": {"label": "Date", "required": False, "type": "text", "help": "Use this OR start_date/end_date"},
        "start_date": {"label": "Start Date", "required": False, "type": "text", "help": "YYYY-MM format"},
        "end_date": {"label": "End Date", "required": False, "type": "text", "help": "YYYY-MM or 'present'"},
        "location": {"label": "Location", "required": False, "type": "text"},
        "summary": {"label": "Summary", "required": False, "type": "textarea"},
        "highlights": {"label": "Highlights", "required": False, "type": "list", "help": "One per line"},
    },
    
    "NormalEntry": {
        "name": {"label": "Name", "required": True, "type": "text"},
        "date": {"label": "Date", "required": False, "type": "text"},
        "start_date": {"label": "Start Date", "required": False, "type": "text"},
        "end_date": {"label": "End Date", "required": False, "type": "text"},
        "location": {"label": "Location", "required": False, "type": "text"},
        "summary": {"label": "Summary", "required": False, "type": "textarea"},
        "highlights": {"label": "Highlights", "required": False, "type": "list"},
    },
    
    "PublicationEntry": {
        "title": {"label": "Title", "required": True, "type": "text"},
        "authors": {"label": "Authors", "required": True, "type": "list", "help": "One author per line"},
        "doi": {"label": "DOI", "required": False, "type": "text"},
        "url": {"label": "URL", "required": False, "type": "text"},
        "journal": {"label": "Journal/Venue", "required": False, "type": "text"},
        "date": {"label": "Date", "required": False, "type": "text"},
    },
    
    "OneLineEntry": {
        "label": {"label": "Label", "required": True, "type": "text"},
        "details": {"label": "Details", "required": True, "type": "text"},
    },
    
    "BulletEntry": {
        "bullet": {"label": "Bullet Point", "required": True, "type": "textarea"},
    },
    
    "TextEntry": {
        "text": {"label": "Text", "required": True, "type": "textarea"},
    },
}


# ============================================================================
# TEMPLATE PRESETS
# ============================================================================
# Predefined templates for "Guided Mode"

TEMPLATE_PRESETS = {
    "classic": {
        "id": "classic",
        "name": "Classic Theme",
        "description": "Traditional timeline-based CV with clean typography",
        "preview_image": None,  # TODO: Add preview images
        "design": {
            "theme": "classic",
            "color": "blue"
        },
        "recommended_sections": ["education", "experience", "skills", "projects"],
        "guided_fields": [
            {"key": "name", "label": "Full Name", "type": "text", "required": True},
            {"key": "headline", "label": "Professional Headline", "type": "text", "required": False},
            {"key": "location", "label": "Location", "type": "text", "required": False},
            {"key": "email", "label": "Email", "type": "email", "required": True},
            {"key": "phone", "label": "Phone", "type": "text", "required": False},
            {"key": "website", "label": "Website", "type": "url", "required": False},
        ]
    },
    "moderncv": {
        "id": "moderncv",
        "name": "Modern CV",
        "description": "Contemporary design with accent colors",
        "preview_image": None,
        "design": {
            "theme": "moderncv",
            "color": "purple"
        },
        "recommended_sections": ["summary", "experience", "education", "skills"],
        "guided_fields": [
            {"key": "name", "label": "Full Name", "type": "text", "required": True},
            {"key": "headline", "label": "Professional Title", "type": "text", "required": False},
            {"key": "email", "label": "Email", "type": "email", "required": True},
        ]
    },
    "sb2nov": {
        "id": "sb2nov",
        "name": "SB2Nov",
        "description": "Compact, information-dense layout",
        "preview_image": None,
        "design": {
            "theme": "sb2nov"
        },
        "recommended_sections": ["education", "experience", "projects", "skills"],
        "guided_fields": [
            {"key": "name", "label": "Full Name", "type": "text", "required": True},
            {"key": "email", "label": "Email", "type": "email", "required": True},
            {"key": "phone", "label": "Phone", "type": "text", "required": False},
        ]
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_entry_type_display_name(entry_type: str) -> str:
    """Convert entry type to display name (e.g., 'ExperienceEntry' -> 'Experience')"""
    return entry_type.replace("Entry", "")


def get_required_fields(entry_type: str) -> List[str]:
    """Get list of required field names for an entry type"""
    schema = ENTRY_DEFINITIONS.get(entry_type, {})
    return [key for key, meta in schema.items() if meta.get("required", False)]


def validate_entry(entry: Dict[str, Any], entry_type: str) -> List[str]:
    """
    Validate an entry against its schema.
    Returns list of missing required fields.
    """
    required_fields = get_required_fields(entry_type)
    missing = []
    
    for field in required_fields:
        value = entry.get(field)
        # Check if field is missing or empty
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            missing.append(field)
    
    return missing
