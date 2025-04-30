#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
phishing_generator.py - Phishing template generator for SpecterX

This module creates customized phishing templates based on target profiles and services.
For educational and security research purposes only.
"""

import os
import json
import random
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import re
import base64
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("logs/phishing_generator.log"), logging.StreamHandler()]
)
logger = logging.getLogger("PhishingGenerator")

# Directory structure
TEMPLATES_DIR = Path("resources/phishing_templates")
OUTPUT_DIR = Path("output/phishing_campaigns")

# Ensure directories exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Common services for phishing templates
COMMON_SERVICES = {
    "email": ["Gmail", "Outlook", "Yahoo", "ProtonMail", "Corporate Email"],
    "social": ["Facebook", "Twitter", "Instagram", "LinkedIn", "TikTok"],
    "financial": ["PayPal", "Bank Account", "Credit Card", "Cryptocurrency Exchange"],
    "cloud": ["Google Drive", "Dropbox", "OneDrive", "iCloud"],
    "streaming": ["Netflix", "Amazon Prime", "Disney+", "Spotify"],
    "corporate": ["VPN Access", "Internal Portal", "HR System", "Project Management"]
}

class PhishingGenerator:
    """
    Generates customized phishing templates based on target profiles and selected services.
    """
    
    def __init__(self):
        """Initialize the PhishingGenerator."""
        self.templates = {}
        self.load_templates()
        logger.info("PhishingGenerator initialized")
        
    def load_templates(self) -> None:
        """Load all available phishing templates from the resources directory."""
        if not TEMPLATES_DIR.exists():
            logger.warning(f"Templates directory not found: {TEMPLATES_DIR}")
            self._create_sample_templates()
            
        for category_dir in TEMPLATES_DIR.iterdir():
            if category_dir.is_dir():
                category = category_dir.name
                self.templates[category] = {}
                
                for template_file in category_dir.glob("*.json"):
                    try:
                        service = template_file.stem
                        with open(template_file, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                            self.templates[category][service] = template_data
                            logger.debug(f"Loaded template: {category}/{service}")
                    except Exception as e:
                        logger.error(f"Failed to load template {template_file}: {str(e)}")
        
        logger.info(f"Loaded {sum(len(services) for services in self.templates.values())} templates")
    
    def _create_sample_templates(self) -> None:
        """Create sample templates if none exist."""
        logger.info("Creating sample templates...")
        
        for category, services in COMMON_SERVICES.items():
            category_dir = TEMPLATES_DIR / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            for service in services:
                service_file = category_dir / f"{service.lower().replace(' ', '_')}.json"
                
                template = {
                    "name": service,
                    "subject_templates": [
                        f"Security alert for your {service} account",
                        f"Action required: {service} account verification",
                        f"Important: Unusual activity detected on your {service}",
                        f"{service} account: Please verify your information"
                    ],
                    "body_templates": [
                        {
                            "title": f"{service} Security Department",
                            "content": f"""Dear {{NAME}},

We have detected unusual activity on your {service} account. To ensure your account security, please verify your information by clicking the link below:

{{PHISHING_LINK}}

This link will expire in 24 hours. If you ignore this message, your account may be temporarily suspended for security reasons.

Thank you,
{service} Security Team"""
                        },
                        {
                            "title": f"{service} Account Services",
                            "content": f"""Hello {{NAME}},

Our system has flagged a potential security issue with your account. We require immediate verification to maintain your access to {service}.

Please update your information at: {{PHISHING_LINK}}

Note: Failure to verify within 48 hours will result in account limitations.

Best regards,
{service} Support"""
                        }
                    ],
                    "logos": [f"{service.lower().replace(' ', '_')}_logo.png"],
                    "footer": f"© {datetime.now().year} {service}. All rights reserved."
                }
                
                with open(service_file, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=4)
                
                logger.debug(f"Created sample template: {category}/{service}")
        
        logger.info("Sample templates created successfully")
    
    def list_available_services(self) -> Dict[str, List[str]]:
        """
        List all available services that have phishing templates
        
        Returns:
            Dict[str, List[str]]: Dictionary of categories and their available services
        """
        available_services = {}
        
        for category, services in self.templates.items():
            available_services[category] = list(services.keys())
            
        return available_services
    
    def _personalize_template(self, template_content: str, target_info: Dict) -> str:
        """
        Replace placeholders in template with personalized information
        
        Args:
            template_content: The template string with placeholders
            target_info: Dictionary containing target's personal information
            
        Returns:
            str: Personalized template content
        """
        # Common replacements
        replacements = {
            "{{NAME}}": target_info.get("name", "Valued Customer"),
            "{{FIRST_NAME}}": target_info.get("name", "User").split()[0] if target_info.get("name") else "User",
            "{{EMAIL}}": target_info.get("email", ""),
            "{{COMPANY}}": target_info.get("company", "your company"),
            "{{PHISHING_LINK}}": self._generate_phishing_link(target_info),
            "{{CURRENT_YEAR}}": str(datetime.now().year),
            "{{CURRENT_DATE}}": datetime.now().strftime("%B %d, %Y"),
        }
        
        # Replace all placeholders
        content = template_content
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
            
        return content
    
    def _generate_phishing_link(self, target_info: Dict) -> str:
        """
        Generate a convincing phishing link based on the target service
        
        Args:
            target_info: Dictionary containing target's information
            
        Returns:
            str: A fake phishing URL
        """
        service = target_info.get("service", "").lower()
        company = target_info.get("company", "").lower()
        id_string = base64.urlsafe_b64encode(os.urandom(8)).decode().rstrip('=')
        
        # Create domain variations
        domain_variations = [
            f"{service}-account-security.com",
            f"{service}-verify-login.net",
            f"{service}.account-verify.com",
            f"{service}-id{random.randint(100, 999)}.com",
            f"secure-{service}.com"
        ]
        
        # For corporate targets, create more convincing company-related domains
        if company:
            company_slug = re.sub(r'[^a-z0-9]', '', company.lower())
            domain_variations.extend([
                f"{company_slug}-{service}.com",
                f"{service}.{company_slug}-portal.com",
                f"{company_slug}-access.{service}.com".replace(".com.com", ".com")
            ])
        
        domain = random.choice(domain_variations)
        paths = [
            "account/verify",
            "login/secure",
            "auth/session",
            "security/checkpoint",
            f"user/{id_string}/verify"
        ]
        
        path = random.choice(paths)
        protocol = "https"
        
        return f"{protocol}://{domain}/{path}?token={id_string}&src=email"
    
    def generate_phishing_template(self, 
                                  category: str,
                                  service: str,
                                  target_info: Dict,
                                  output_format: str = "html") -> Union[str, Dict]:
        """
        Generate a personalized phishing template based on target information
        
        Args:
            category: The category of the service (email, social, financial, etc.)
            service: The specific service to target (Gmail, Facebook, etc.)
            target_info: Dictionary containing target's personal information
            output_format: Format of the output ("html", "json", or "text")
            
        Returns:
            Union[str, Dict]: The generated phishing template in the specified format
        """
        if category not in self.templates:
            logger.error(f"Category '{category}' not found")
            return None
            
        if service not in self.templates[category]:
            logger.error(f"Service '{service}' not found in category '{category}'")
            return None
        
        try:
            # Get template data
            template_data = self.templates[category][service]
            
            # Select random subject and body templates
            subject = random.choice(template_data["subject_templates"])
            body_template = random.choice(template_data["body_templates"])
            
            # Personalize content
            personalized_subject = self._personalize_template(subject, target_info)
            personalized_content = self._personalize_template(body_template["content"], target_info)
            
            # Generate output in requested format
            if output_format == "html":
                html_template = self._generate_html_template(
                    template_data["name"],
                    body_template["title"],
                    personalized_content,
                    template_data.get("logos", [])[0] if template_data.get("logos") else None,
                    template_data.get("footer", "")
                )
                return html_template
                
            elif output_format == "text":
                return f"Subject: {personalized_subject}\n\n{personalized_content}"
                
            elif output_format == "json":
                return {
                    "service": template_data["name"],
                    "subject": personalized_subject,
                    "title": body_template["title"],
                    "content": personalized_content,
                    "logo": template_data.get("logos", [])[0] if template_data.get("logos") else None,
                    "footer": template_data.get("footer", ""),
                    "generated_time": datetime.now().isoformat(),
                    "phishing_link": self._generate_phishing_link(target_info)
                }
                
            else:
                logger.error(f"Invalid output format: {output_format}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating phishing template: {str(e)}")
            return None
    
    def _generate_html_template(self, 
                               service_name: str, 
                               title: str, 
                               content: str, 
                               logo_path: Optional[str] = None,
                               footer: str = "") -> str:
        """
        Generate an HTML phishing template
        
        Args:
            service_name: Name of the service
            title: Title of the email
            content: Main content of the email
            logo_path: Path to the logo image
            footer: Footer text
            
        Returns:
            str: HTML template content
        """
        # Logo section
        logo_html = ""
        if logo_path:
            logo_html = f"""
            <div class="logo">
                <img src="cid:{logo_path}" alt="{service_name} Logo" style="max-height: 60px; max-width: 200px;">
            </div>
            """
        
        # Convert newlines to HTML breaks
        content_html = content.replace("\n", "<br>")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{service_name} - {title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .logo {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header {{
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .content {{
                    margin-bottom: 30px;
                }}
                .footer {{
                    border-top: 1px solid #ddd;
                    padding-top: 10px;
                    font-size: 12px;
                    color: #777;
                    text-align: center;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #0066cc;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            {logo_html}
            <div class="header">
                <h2>{title}</h2>
            </div>
            <div class="content">
                {content_html}
            </div>
            <div class="footer">
                {footer}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def save_phishing_template(self, 
                              category: str,
                              service: str,
                              target_info: Dict,
                              campaign_name: Optional[str] = None) -> Dict:
        """
        Generate and save phishing templates to the output directory
        
        Args:
            category: The category of the service
            service: The specific service to target
            target_info: Dictionary containing target's personal information
            campaign_name: Optional name for the campaign
            
        Returns:
            Dict: Information about the saved templates
        """
        timestamp = int(time.time())
        campaign_id = campaign_name or f"campaign_{timestamp}"
        campaign_dir = OUTPUT_DIR / campaign_id
        campaign_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Generate templates in different formats
            html_content = self.generate_phishing_template(category, service, target_info, "html")
            text_content = self.generate_phishing_template(category, service, target_info, "text")
            json_content = self.generate_phishing_template(category, service, target_info, "json")
            
            if not html_content or not text_content or not json_content:
                logger.error("Failed to generate one or more template formats")
                return {"status": "error", "message": "Template generation failed"}
            
            # Save the templates
            service_slug = service.lower().replace(' ', '_')
            target_name = re.sub(r'[^a-z0-9]', '_', target_info.get("name", "target").lower())
            base_filename = f"{service_slug}_{target_name}_{timestamp}"
            
            html_path = campaign_dir / f"{base_filename}.html"
            text_path = campaign_dir / f"{base_filename}.txt"
            json_path = campaign_dir / f"{base_filename}.json"
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
                
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=4)
            
            # Generate campaign info
            campaign_info = {
                "campaign_id": campaign_id,
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "category": category,
                "service": service,
                "target": {k: v for k, v in target_info.items() if k != "password"},  # Don't save any passwords
                "files": {
                    "html": str(html_path),
                    "text": str(text_path),
                    "json": str(json_path)
                }
            }
            
            # Save campaign info
            with open(campaign_dir / "campaign_info.json", 'w', encoding='utf-8') as f:
                json.dump(campaign_info, f, indent=4)
                
            logger.info(f"Phishing templates saved to {campaign_dir}")
            
            return {
                "status": "success", 
                "campaign_id": campaign_id,
                "output_dir": str(campaign_dir),
                "files": campaign_info["files"]
            }
            
        except Exception as e:
            logger.error(f"Error saving phishing templates: {str(e)}")
            return {"status": "error", "message": str(e)}

    def analyze_effectiveness(self, template_content: str) -> Dict:
        """
        Analyze the potential effectiveness of a phishing template
        
        Args:
            template_content: The phishing template content to analyze
            
        Returns:
            Dict: Analysis results with effectiveness score and suggestions
        """
        # Calculate basic metrics
        word_count = len(template_content.split())
        avg_word_length = sum(len(word) for word in template_content.split()) / max(1, word_count)
        
        # Check for common urgency indicators
        urgency_phrases = ["urgent", "immediate", "alert", "warning", "action required", 
                          "limited time", "expires", "suspension", "now"]
        
        urgency_count = sum(1 for phrase in urgency_phrases 
                           if phrase in template_content.lower())
        
        # Check for security-related terminology
        security_phrases = ["security", "verify", "confirm", "update", "password", 
                           "credential", "login", "account", "unauthorized", "suspicious"]
        
        security_count = sum(1 for phrase in security_phrases 
                            if phrase in template_content.lower())
        
        # Calculate readability (simplified)
        sentence_count = max(1, len(re.split(r'[.!?]', template_content)) - 1)
        readability_score = 100 - (avg_word_length * 10) - (word_count / sentence_count)
        readability_score = max(0, min(100, readability_score))
        
        # Calculate effectiveness score (0-100)
        effectiveness = min(100, (
            (urgency_count * 5) + 
            (security_count * 4) + 
            (readability_score * 0.5) +
            (min(50, word_count) * 0.5)
        ))
        
        # Generate suggestions
        suggestions = []
        if urgency_count < 2:
            suggestions.append("Add more urgency to the message")
        if security_count < 3:
            suggestions.append("Include more security-related terminology")
        if word_count < 50:
            suggestions.append("Consider making the message more detailed")
        if word_count > 300:
            suggestions.append("The message may be too long; consider shortening it")
        if readability_score < 60:
            suggestions.append("Improve readability by using shorter sentences and simpler words")
        
        # Categorize effectiveness
        if effectiveness >= 80:
            effectiveness_category = "High"
        elif effectiveness >= 60:
            effectiveness_category = "Medium"
        else:
            effectiveness_category = "Low"
            
        return {
            "effectiveness": round(effectiveness, 1),
            "effectiveness_category": effectiveness_category,
            "metrics": {
                "word_count": word_count,
                "avg_word_length": round(avg_word_length, 1),
                "sentence_count": sentence_count,
                "urgency_indicators": urgency_count,
                "security_terminology": security_count,
                "readability_score": round(readability_score, 1)
            },
            "suggestions": suggestions
        }

def main():
    """Test function to demonstrate the PhishingGenerator capabilities."""
    generator = PhishingGenerator()
    
    # List available services
    available_services = generator.list_available_services()
    print("Available phishing templates:")
    for category, services in available_services.items():
        print(f"  {category.capitalize()}:")
        for service in services:
            print(f"    - {service}")
    
    # Example target info
    target_info = {
        "name": "John Smith",
        "email": "john.smith@example.com",
        "company": "Acme Corp",
        "service": "Gmail"
    }
    
    # Generate a sample template
    if "email" in available_services and "gmail" in available_services.get("email", []):
        template = generator.generate_phishing_template("email", "gmail", target_info, "text")
        print("\nSample Phishing Template:")
        print(template)
        
        # Analyze effectiveness
        analysis = generator.analyze_effectiveness(template)
        print("\nTemplate Analysis:")
        print(f"Effectiveness: {analysis['effectiveness']} ({analysis['effectiveness_category']})")
        print("Suggestions:")
        for suggestion in analysis["suggestions"]:
            print(f"  - {suggestion}")
    else:
        print("Sample template not available. Please run the script to create templates first.")
    
if __name__ == "__main__":
    main()