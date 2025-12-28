"""
RenderCV Frontend - Main Application

A Streamlit-based CV builder that generates RenderCV-compatible YAML and renders PDFs.

Features:
- Template Mode: Guided CV creation with predefined templates
- Builder Mode: Free-form CV creation from scratch
- YAML Preview: See generated YAML in real-time
- PDF Generation: Render CV using RenderCV CLI
- Design Configuration: Customize theme and appearance
"""

import streamlit as st
import json
import uuid
from datetime import datetime
from models import (
    CV, Design, Locale, Settings, RenderCVDocument,
    ENTRY_DEFINITIONS, TEMPLATE_PRESETS,
    get_entry_type_display_name, validate_entry
)
from yaml_serializer import (
    serialize_to_yaml, create_rendercv_document,
    validate_cv_structure
)
from api_client import RenderCVClient, save_pdf

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="RenderCV Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'mode' not in st.session_state:
    st.session_state.mode = None  # None, 'template', or 'builder'

if 'selected_template' not in st.session_state:
    st.session_state.selected_template = None

if 'cv' not in st.session_state:
    st.session_state.cv = CV().model_dump()

if 'design' not in st.session_state:
    st.session_state.design = Design().model_dump()

if 'locale' not in st.session_state:
    st.session_state.locale = Locale().model_dump()

if 'settings' not in st.session_state:
    st.session_state.settings = Settings().model_dump()

if 'selected_entry_id' not in st.session_state:
    st.session_state.selected_entry_id = None

if 'selected_section_key' not in st.session_state:
    st.session_state.selected_section_key = None

if 'show_yaml_preview' not in st.session_state:
    st.session_state.show_yaml_preview = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_entry_type(entry):
    return entry.get('_type', 'NormalEntry')

def add_entry(section_key, entry_type):
    if section_key not in st.session_state.cv['sections']:
        st.session_state.cv['sections'][section_key] = []
    
    new_entry = {"_ui_id": str(uuid.uuid4()), "_type": entry_type}
    st.session_state.cv['sections'][section_key].append(new_entry)
    
    st.session_state.selected_entry_id = new_entry['_ui_id']
    st.session_state.selected_section_key = section_key
    st.rerun()

def select_entry(section_key, entry):
    st.session_state.selected_entry_id = entry.get('_ui_id')
    st.session_state.selected_section_key = section_key
    st.rerun()

def deselect_entry():
    st.session_state.selected_entry_id = None
    st.session_state.selected_section_key = None
    st.rerun()

def delete_entry(section_key, entry_index):
    entries = st.session_state.cv['sections'][section_key]
    entry = entries[entry_index]
    
    entries.pop(entry_index)
    
    if not entries:
        del st.session_state.cv['sections'][section_key]
    
    if st.session_state.selected_entry_id == entry.get('_ui_id'):
        deselect_entry()
    else:
        st.rerun()

def update_entry_value(entry, key, widget_key):
    entry[key] = st.session_state[widget_key]

def update_entry_list(entry, key, widget_key):
    raw_text = st.session_state[widget_key]
    entry[key] = [x.strip() for x in raw_text.split('\n') if x.strip()]

def add_custom_field_callback():
    new_key = st.session_state.get("new_custom_key_input", "").strip()
    if not new_key:
        return
        
    sec_key = st.session_state.selected_section_key
    ent_id = st.session_state.selected_entry_id
    
    if sec_key and ent_id and sec_key in st.session_state.cv['sections']:
        entries = st.session_state.cv['sections'][sec_key]
        entry = next((e for e in entries if e.get('_ui_id') == ent_id), None)
        
        if entry is not None:
            if new_key not in entry:
                entry[new_key] = ""
                st.toast(f"Field '{new_key}' added!", icon="✅")
                st.session_state.new_custom_key_input = ""
            else:
                st.toast(f"Field '{new_key}' already exists.", icon="⚠️")

def load_template(template_id):
    """Load a template and initialize CV with template defaults"""
    template = TEMPLATE_PRESETS.get(template_id)
    if not template:
        return
    
    st.session_state.selected_template = template_id
    st.session_state.mode = 'template'
    
    # Initialize design from template
    st.session_state.design = template['design'].copy()
    
    # Reset CV
    st.session_state.cv = CV().model_dump()
    
    st.rerun()

def switch_to_builder():
    """Switch to builder mode"""
    st.session_state.mode = 'builder'
    st.session_state.selected_template = None
    st.rerun()

def reset_all():
    """Reset entire application"""
    st.session_state.cv = CV().model_dump()
    st.session_state.design = Design().model_dump()
    st.session_state.locale = Locale().model_dump()
    st.session_state.settings = Settings().model_dump()
    st.session_state.mode = None
    st.session_state.selected_template = None
    deselect_entry()

# ============================================================================
# CSS STYLING
# ============================================================================

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton button {
        text-align: left;
    }
    .template-card {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .template-card:hover {
        border-color: #4CAF50;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .yaml-preview {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 12px;
        max-height: 600px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN APP LOGIC
# ============================================================================

# Sidebar - Always visible
with st.sidebar:
    st.title("🎨 RenderCV Builder")
    
    st.divider()
    
    # Mode selector
    if st.session_state.mode is None:
        st.info("Choose a mode to get started")
    else:
        current_mode = "Template Mode" if st.session_state.mode == 'template' else "Builder Mode"
        st.success(f"**Mode:** {current_mode}")
        
        if st.button("🔄 Change Mode", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
    
    st.divider()
    
    # Design Configuration
    with st.expander("🎨 Design", expanded=False):
        st.session_state.design['theme'] = st.selectbox(
            "Theme",
            options=["classic", "moderncv", "sb2nov", "engineeringresumes"],
            index=["classic", "moderncv", "sb2nov", "engineeringresumes"].index(
                st.session_state.design.get('theme', 'classic')
            )
        )
        
        st.session_state.design['color'] = st.selectbox(
            "Color",
            options=[None, "blue", "green", "red", "purple", "orange"],
            index=0
        )
    
    # Locale Configuration
    with st.expander("🌍 Locale", expanded=False):
        st.session_state.locale['language'] = st.selectbox(
            "Language",
            options=["english", "spanish", "french", "german", "portuguese"],
            index=0
        )
    
    st.divider()
    
    # Actions
    st.subheader("Actions")
    
    # YAML Preview Toggle
    if st.button("👁️ Toggle YAML Preview", use_container_width=True):
        st.session_state.show_yaml_preview = not st.session_state.show_yaml_preview
        st.rerun()
    
    # Download YAML
    if st.session_state.cv.get('name'):
        document = create_rendercv_document(
            st.session_state.cv,
            st.session_state.design,
            st.session_state.locale,
            st.session_state.settings
        )
        yaml_str = serialize_to_yaml(document)
        
        st.download_button(
            label="📥 Download YAML",
            data=yaml_str,
            file_name=f"{st.session_state.cv['name'].replace(' ', '_')}_CV.yaml",
            mime="text/yaml",
            use_container_width=True
        )
    
    # Render PDF
    if st.button("🎯 Render PDF", use_container_width=True, type="primary"):
        with st.spinner("Rendering CV..."):
            # Validate first
            is_valid, errors = validate_cv_structure(st.session_state.cv)
            
            if not is_valid:
                st.error("**Validation Errors:**")
                for error in errors:
                    st.error(f"• {error}")
            else:
                # Create document
                document = create_rendercv_document(
                    st.session_state.cv,
                    st.session_state.design,
                    st.session_state.locale,
                    st.session_state.settings
                )
                yaml_str = serialize_to_yaml(document)
                
                # Render using RenderCV
                client = RenderCVClient(mode="local")
                success, message, pdf_bytes = client.render_cv(yaml_str)
                
                if success:
                    st.success(message)
                    # Offer download
                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_bytes,
                        file_name=f"{st.session_state.cv['name'].replace(' ', '_')}_CV.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error(f"**Render Failed:**\n{message}")
    
    st.divider()
    
    if st.button("🗑️ Reset All", use_container_width=True):
        reset_all()

# ============================================================================
# MODE SELECTION SCREEN
# ============================================================================

if st.session_state.mode is None:
    st.title("Welcome to RenderCV Builder")
    st.markdown("### Choose how you want to create your CV")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Template Mode")
        st.markdown("**Guided creation with predefined templates**")
        st.markdown("- Select a professional template")
        st.markdown("- Fill in structured forms")
        st.markdown("- Quick and easy")
        
        if st.button("Start with Template", use_container_width=True, type="primary"):
            st.session_state.mode = 'template'
            st.rerun()
    
    with col2:
        st.markdown("#### 🛠️ Builder Mode")
        st.markdown("**Free-form creation from scratch**")
        st.markdown("- Complete control over structure")
        st.markdown("- Add custom fields")
        st.markdown("- Maximum flexibility")
        
        if st.button("Start Building", use_container_width=True):
            switch_to_builder()

# ============================================================================
# TEMPLATE MODE
# ============================================================================

elif st.session_state.mode == 'template':
    if st.session_state.selected_template is None:
        # Template selection
        st.title("Select a Template")
        
        for template_id, template in TEMPLATE_PRESETS.items():
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {template['name']}")
                    st.markdown(template['description'])
                    st.markdown(f"**Theme:** `{template['design']['theme']}`")
                    st.markdown(f"**Recommended sections:** {', '.join(template['recommended_sections'])}")
                
                with col2:
                    if st.button(f"Use {template['name']}", key=f"select_{template_id}"):
                        load_template(template_id)
                
                st.divider()
    
    else:
        # Template-guided form
        template = TEMPLATE_PRESETS[st.session_state.selected_template]
        
        st.title(f"📋 {template['name']}")
        st.markdown(f"*{template['description']}*")
        
        st.divider()
        
        # Guided fields
        st.subheader("Basic Information")
        
        for field in template['guided_fields']:
            key = field['key']
            label = field['label']
            field_type = field.get('type', 'text')
            required = field.get('required', False)
            
            label_display = f"{label} {'*' if required else ''}"
            
            if field_type == 'email':
                st.session_state.cv[key] = st.text_input(
                    label_display,
                    value=st.session_state.cv.get(key, ''),
                    placeholder="example@email.com"
                )
            elif field_type == 'url':
                st.session_state.cv[key] = st.text_input(
                    label_display,
                    value=st.session_state.cv.get(key, ''),
                    placeholder="https://example.com"
                )
            else:
                st.session_state.cv[key] = st.text_input(
                    label_display,
                    value=st.session_state.cv.get(key, '')
                )
        
        st.divider()
        
        # Sections
        st.subheader("Sections")
        st.info("Add sections recommended for this template. You can switch to Builder Mode for more control.")
        
        for section_name in template['recommended_sections']:
            with st.expander(f"📂 {section_name.title()}", expanded=False):
                entries = st.session_state.cv['sections'].get(section_name, [])
                
                if not entries:
                    st.info(f"No {section_name} entries yet. Add one below.")
                else:
                    for i, entry in enumerate(entries):
                        st.markdown(f"**Entry {i+1}**")
                        entry_type = get_entry_type(entry)
                        schema = ENTRY_DEFINITIONS.get(entry_type, {})
                        
                        # Show ALL schema fields, not just existing ones
                        for key, meta in schema.items():
                            label = meta['label']
                            widget_key = f"template_{section_name}_{i}_{key}"
                            
                            # Get current value or default
                            if key not in entry:
                                # Initialize field with default value
                                entry[key] = [] if meta.get('type') == 'list' else ''
                            
                            current_value = entry[key]
                            
                            if meta.get('type') == 'list':
                                val_str = '\n'.join(current_value) if isinstance(current_value, list) else str(current_value or '')
                                st.text_area(label, value=val_str, key=widget_key, on_change=update_entry_list, args=(entry, key, widget_key))
                            elif meta.get('type') == 'textarea':
                                st.text_area(label, value=current_value or '', key=widget_key, on_change=update_entry_value, args=(entry, key, widget_key))
                            else:
                                st.text_input(label, value=current_value or '', key=widget_key, on_change=update_entry_value, args=(entry, key, widget_key))
                        
                        if st.button(f"🗑️ Delete Entry {i+1}", key=f"del_template_{section_name}_{i}"):
                            delete_entry(section_name, i)
                        
                        st.divider()
                
                # Add entry button
                entry_type_for_section = "ExperienceEntry" if "experience" in section_name else "EducationEntry" if "education" in section_name else "OneLineEntry" if "skill" in section_name else "NormalEntry"
                
                if st.button(f"➕ Add {section_name.title()} Entry", key=f"add_{section_name}"):
                    add_entry(section_name, entry_type_for_section)

# ============================================================================
# BUILDER MODE
# ============================================================================

elif st.session_state.mode == 'builder':
    col_canvas, col_palette = st.columns([3, 1])
    
    # Canvas (Left)
    with col_canvas:
        st.markdown("### 📄 Resume")
        
        # Header
        with st.container(border=True):
            col1, col2 = st.columns(2)
            st.session_state.cv['name'] = col1.text_input("Full Name", value=st.session_state.cv.get('name', ''))
            st.session_state.cv['headline'] = col2.text_input("Headline", value=st.session_state.cv.get('headline', ''))
            
            col3, col4 = st.columns(2)
            st.session_state.cv['email'] = col3.text_input("Email", value=st.session_state.cv.get('email', ''))
            st.session_state.cv['phone'] = col4.text_input("Phone", value=st.session_state.cv.get('phone', ''))
            
            col5, col6 = st.columns(2)
            st.session_state.cv['location'] = col5.text_input("Location", value=st.session_state.cv.get('location', ''))
            st.session_state.cv['website'] = col6.text_input("Website", value=st.session_state.cv.get('website', ''))
        
        # Sections
        sections = st.session_state.cv.get('sections', {})
        
        if not sections:
            st.info("👈 Start by clicking a section type on the right to add content!")
        
        for section_key, entries in sections.items():
            st.markdown(f"#### {section_key.replace('_', ' ').title()}")
            
            for i, entry in enumerate(entries):
                if '_ui_id' not in entry:
                    entry['_ui_id'] = str(uuid.uuid4())
                
                is_selected = st.session_state.selected_entry_id == entry['_ui_id']
                
                # Controls
                c1, c2 = st.columns([0.9, 0.1])
                display_text = (entry.get('company') or entry.get('institution') or 
                              entry.get('name') or entry.get('title') or f"Entry {i+1}")
                
                sel_label = f"{'🟢' if is_selected else '📍'} {display_text}"
                if c1.button(sel_label, key=f"sel_{entry['_ui_id']}"):
                    select_entry(section_key, entry)
                
                if c2.button("✖", key=f"del_{entry['_ui_id']}"):
                    delete_entry(section_key, i)
                
                # Fields
                curr_type = get_entry_type(entry)
                schema = ENTRY_DEFINITIONS.get(curr_type, {})
                all_keys = list(schema.keys()) + [k for k in entry.keys() if k not in schema and not k.startswith('_')]
                
                for k in all_keys:
                    if k in entry:
                        val = entry[k]
                        label = schema.get(k, {}).get('label', k.title())
                        widget_key = f"in_{entry['_ui_id']}_{k}"
                        help_text = schema.get(k, {}).get('help')
                        
                        # Create columns for field and delete button
                        col_field, col_delete = st.columns([0.9, 0.1])
                        
                        with col_field:
                            if schema.get(k, {}).get('type') == 'textarea':
                                st.text_area(label, value=val or "", key=widget_key, help=help_text,
                                           on_change=update_entry_value, args=(entry, k, widget_key))
                            elif schema.get(k, {}).get('type') == 'list':
                                v_str = "\n".join(val) if isinstance(val, list) else str(val or "")
                                st.text_area(label, value=v_str, key=widget_key, help=help_text,
                                           on_change=update_entry_list, args=(entry, k, widget_key))
                            else:
                                st.text_input(label, value=val or "", key=widget_key, help=help_text,
                                            on_change=update_entry_value, args=(entry, k, widget_key))
                        
                        with col_delete:
                            # Only allow deleting non-required fields and custom fields
                            is_required = schema.get(k, {}).get('required', False)
                            is_custom = k not in schema
                            
                            if not is_required or is_custom:
                                st.write("")  # Spacer to align with input
                                if st.button("🗑️", key=f"del_field_{entry['_ui_id']}_{k}", help=f"Delete {label}"):
                                    del entry[k]
                                    st.rerun()
                
                st.divider()
    
    # Palette (Right)
    with col_palette:
        if st.session_state.selected_entry_id is None:
            st.header("Sections")
            st.info("Select a section to add.")
            
            for type_name in ENTRY_DEFINITIONS.keys():
                clean_name = get_entry_type_display_name(type_name)
                if st.button(f"➕ {clean_name}", use_container_width=True):
                    section_key = clean_name.lower()
                    add_entry(section_key, type_name)
        
        else:
            # Detail Mode
            section_key = st.session_state.selected_section_key
            entries = st.session_state.cv['sections'].get(section_key, [])
            entry = next((e for e in entries if e.get('_ui_id') == st.session_state.selected_entry_id), None)
            
            if not entry:
                deselect_entry()
            else:
                entry_type = get_entry_type(entry)
                clean_name = get_entry_type_display_name(entry_type)
                
                st.header(f"{clean_name}")
                if st.button("← Back", use_container_width=True):
                    deselect_entry()
                
                st.divider()
                st.markdown("**Add Field**")
                
                schema = ENTRY_DEFINITIONS.get(entry_type, {})
                for field_key, field_meta in schema.items():
                    label = field_meta['label']
                    is_present = field_key in entry
                    btn_label = f"{'✓' if is_present else '+'} {label}"
                    
                    if st.button(btn_label, key=f"add_field_{field_key}", use_container_width=True, disabled=is_present):
                        if not is_present:
                            default = [] if field_meta.get('type') == 'list' else ""
                            entry[field_key] = default
                            st.rerun()
                
                st.divider()
                st.markdown("**Custom Field**")
                st.text_input(
                    "Field name",
                    key="new_custom_key_input",
                    placeholder="e.g., revenue"
                )
                st.button("Add Custom Field", on_click=add_custom_field_callback, use_container_width=True)

# ============================================================================
# YAML PREVIEW (Bottom Panel)
# ============================================================================

if st.session_state.show_yaml_preview and st.session_state.mode is not None:
    st.divider()
    st.subheader("📝 YAML Preview")
    
    try:
        document = create_rendercv_document(
            st.session_state.cv,
            st.session_state.design,
            st.session_state.locale,
            st.session_state.settings
        )
        yaml_str = serialize_to_yaml(document)
        
        st.code(yaml_str, language='yaml')
    except Exception as e:
        st.error(f"Error generating YAML: {str(e)}")
