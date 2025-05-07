"""Utility script to load sample data into the system."""
import os
import argparse
import logging
from pathlib import Path

from src.services.vector_store_service import VectorStoreService
from src.utils.document_loader import DocumentLoader


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_sample_documents(data_dir: str) -> None:
    """Create sample documents for testing.
    
    Args:
        data_dir: Directory to store sample documents
    """
    os.makedirs(data_dir, exist_ok=True)
    
    # Create sample company policies
    policies = [
        {
            "title": "Remote Work Policy",
            "content": """
# Remote Work Policy

## Overview
This policy outlines guidelines for employees who work remotely, either full-time or part-time.

## Eligibility
All employees who can perform their duties remotely are eligible for remote work, subject to manager approval.

## Equipment
The company will provide necessary equipment including laptop, headset, and software licenses.

## Security
Employees must adhere to all security protocols, including using VPN, securing physical spaces, and following data protection guidelines.

## Working Hours
Standard working hours apply, though flexibility is offered as long as core hours (10 AM - 3 PM) are observed.

## Communication
Remote workers must be available via email, chat, and video conferencing during working hours, with response expected within 2 hours.
"""
        },
        {
            "title": "Employee Benefits Overview",
            "content": """
# Employee Benefits Overview

## Health Insurance
Comprehensive health coverage including medical, dental, and vision. Coverage begins on the first day of employment.

## Retirement Plan
401(k) plan with 5% company match. Employees are eligible after 90 days of employment.

## Paid Time Off
- 15 days vacation annually, accrued monthly
- 10 days sick leave
- 10 paid holidays
- 3 personal days

## Professional Development
$2,000 annual stipend for courses, certifications, and conferences relevant to your role.

## Wellness Program
Monthly wellness stipend of $50 for gym memberships, fitness classes, or mental health apps.
"""
        },
        {
            "title": "Information Security Guidelines",
            "content": """
# Information Security Guidelines

## Password Requirements
- Minimum 12 characters
- Combination of uppercase, lowercase, numbers, and special characters
- Change every 90 days
- No reuse of previous 5 passwords

## Data Classification
1. Public: Information freely available to the public
2. Internal: Information available to all employees
3. Confidential: Sensitive business information
4. Restricted: Highly sensitive information with legal implications

## Incident Reporting
Report all security incidents immediately to security@company.com or call the security hotline at x5555.

## Device Security
- Lock devices when unattended
- Use company-provided antivirus software
- Encrypt sensitive data
- No installation of unauthorized software
"""
        }
    ]
    
    # Write sample documents to files
    for doc in policies:
        file_path = os.path.join(data_dir, f"{doc['title'].replace(' ', '_')}.md")
        with open(file_path, "w") as f:
            f.write(doc["content"])
        logger.info(f"Created sample document: {file_path}")


def main():
    """Main entry point for the sample data loader script."""
    parser = argparse.ArgumentParser(description="Load sample data into the company bot system")
    parser.add_argument("--data-dir", type=str, default="data/sample", help="Directory for sample data")
    parser.add_argument("--create-samples", action="store_true", help="Create sample documents")
    parser.add_argument("--recursive", action="store_true", help="Recursively load from directory")
    args = parser.parse_args()
    
    # Create sample documents if requested
    if args.create_samples:
        create_sample_documents(args.data_dir)
    
    # Initialize services
    vector_store = VectorStoreService()
    document_loader = DocumentLoader(vector_store)
    
    # Load documents from directory
    docs_processed, chunks_stored = document_loader.load_directory(
        args.data_dir,
        recursive=args.recursive
    )
    
    logger.info(f"Processed {docs_processed} documents and stored {chunks_stored} chunks")


if __name__ == "__main__":
    main() 