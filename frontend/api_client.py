"""
RenderCV Frontend - API Client

This module handles communication with RenderCV for PDF generation.

Two modes supported:
1. Local mode: Uses RenderCV CLI via subprocess
2. API mode: Sends requests to a RenderCV API endpoint

The local mode is the default and most reliable option.
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, Tuple
import requests
from datetime import datetime


class RenderCVClient:
    """
    Client for interacting with RenderCV.
    
    Supports both local CLI execution and remote API calls.
    """
    
    def __init__(self, mode: str = "local", api_url: Optional[str] = None):
        """
        Initialize RenderCV client.
        
        Args:
            mode: "local" to use RenderCV CLI, "api" to use remote API
            api_url: URL of RenderCV API (required if mode="api")
        """
        self.mode = mode
        self.api_url = api_url
        
        if mode == "api" and not api_url:
            raise ValueError("api_url is required when mode='api'")
    
    def render_cv_local(self, yaml_content: str, output_dir: Optional[str] = None) -> Tuple[bool, str, Optional[bytes]]:
        """
        Render CV using local RenderCV CLI.
        
        This is the most reliable method as it uses the official RenderCV tool.
        
        Args:
            yaml_content: YAML content to render
            output_dir: Directory to save output (uses temp dir if None)
            
        Returns:
            Tuple of (success, message, pdf_bytes)
        """
        # Create temporary directory for rendering
        if output_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="rendercv_")
        else:
            temp_dir = output_dir
            os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Write YAML to temp file
            yaml_path = os.path.join(temp_dir, "cv.yaml")
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            # Run RenderCV CLI
            # Use 'python -m rendercv' to work with user installations
            # Set encoding to utf-8 and handle errors to avoid Windows console issues
            result = subprocess.run(
                ['python', '-m', 'rendercv', 'render', yaml_path],
                cwd=temp_dir,
                capture_output=True,
                encoding='utf-8',
                errors='replace',  # Replace unencodable characters instead of failing
                timeout=60  # 60 second timeout
            )
            
            # Note: On Windows, RenderCV might fail with encoding errors in stdout/stderr
            # even when the PDF is generated successfully. So we check for PDF existence
            # instead of relying solely on return code.
            
            # Find generated PDF
            # RenderCV creates: rendercv_output/NAME_CV.pdf
            output_folder = os.path.join(temp_dir, "rendercv_output")
            
            if not os.path.exists(output_folder):
                # If no output folder, it really failed
                error_msg = f"RenderCV failed - no output folder created"
                if result.stderr:
                    error_msg += f"\n\nError:\n{result.stderr}"
                if result.stdout:
                    error_msg += f"\n\nOutput:\n{result.stdout}"
                return False, error_msg, None
            
            # Find PDF file
            pdf_files = list(Path(output_folder).glob("*.pdf"))
            
            if not pdf_files:
                # Output folder exists but no PDF
                error_msg = f"RenderCV failed - no PDF file generated"
                if result.stderr:
                    error_msg += f"\n\nError:\n{result.stderr}"
                return False, error_msg, None
            
            # Success! PDF was generated
            # Read PDF bytes
            pdf_path = pdf_files[0]
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            success_msg = f"CV rendered successfully: {pdf_path.name}"
            return True, success_msg, pdf_bytes
            
        except subprocess.TimeoutExpired:
            return False, "RenderCV timed out (>60s)", None
        except FileNotFoundError:
            return False, "RenderCV CLI not found. Please install: pip install rendercv", None
        except Exception as e:
            return False, f"Error rendering CV: {str(e)}", None
    
    def render_cv_api(self, yaml_content: str) -> Tuple[bool, str, Optional[bytes]]:
        """
        Render CV using remote API.
        
        Args:
            yaml_content: YAML content to render
            
        Returns:
            Tuple of (success, message, pdf_bytes)
        """
        try:
            # Send POST request to API
            response = requests.post(
                f"{self.api_url}/render",
                json={"yaml": yaml_content},
                timeout=30
            )
            
            if response.status_code == 200:
                # Check if response is PDF
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/pdf' in content_type:
                    return True, "CV rendered successfully", response.content
                else:
                    # Might be JSON with URL
                    data = response.json()
                    if 'pdf_url' in data:
                        # Download PDF from URL
                        pdf_response = requests.get(data['pdf_url'], timeout=30)
                        if pdf_response.status_code == 200:
                            return True, "CV rendered successfully", pdf_response.content
                        else:
                            return False, f"Failed to download PDF: {pdf_response.status_code}", None
                    else:
                        return False, "Unexpected API response format", None
            else:
                error_msg = f"API error ({response.status_code}): {response.text}"
                return False, error_msg, None
                
        except requests.exceptions.Timeout:
            return False, "API request timed out", None
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to API at {self.api_url}", None
        except Exception as e:
            return False, f"API error: {str(e)}", None
    
    def render_cv(self, yaml_content: str, output_dir: Optional[str] = None) -> Tuple[bool, str, Optional[bytes]]:
        """
        Render CV using configured mode (local or API).
        
        Args:
            yaml_content: YAML content to render
            output_dir: Output directory (only used in local mode)
            
        Returns:
            Tuple of (success, message, pdf_bytes)
        """
        if self.mode == "local":
            return self.render_cv_local(yaml_content, output_dir)
        elif self.mode == "api":
            return self.render_cv_api(yaml_content)
        else:
            return False, f"Unknown mode: {self.mode}", None
    
    def health_check(self) -> bool:
        """
        Check if RenderCV is available.
        
        Returns:
            True if RenderCV is accessible, False otherwise
        """
        if self.mode == "local":
            try:
                result = subprocess.run(
                    ['python', '-m', 'rendercv', '--version'],
                    capture_output=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=5
                )
                return result.returncode == 0
            except:
                return False
        elif self.mode == "api":
            try:
                response = requests.get(f"{self.api_url}/health", timeout=5)
                return response.status_code == 200
            except:
                return False
        return False


def save_pdf(pdf_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    Save PDF bytes to file.
    
    Args:
        pdf_bytes: PDF content as bytes
        filename: Output filename (auto-generated if None)
        
    Returns:
        Path to saved file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cv_{timestamp}.pdf"
    
    with open(filename, 'wb') as f:
        f.write(pdf_bytes)
    
    return filename


# Example usage
if __name__ == "__main__":
    # Test local rendering
    client = RenderCVClient(mode="local")
    
    test_yaml = """
cv:
  name: Test User
  email: test@example.com
  sections:
    experience:
      - company: Test Corp
        position: Developer
        start_date: 2020-01
        end_date: present
design:
  theme: classic
locale:
  language: english
"""
    
    success, message, pdf_bytes = client.render_cv(test_yaml)
    print(f"Success: {success}")
    print(f"Message: {message}")
    
    if success and pdf_bytes:
        output_path = save_pdf(pdf_bytes, "test_cv.pdf")
        print(f"PDF saved to: {output_path}")
