"""Script para cargar datos de muestra en el vector store."""
import os
import sys
import uuid
import argparse
import logging
from typing import List, Dict, Any
import json

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.vector_store_service import VectorStoreService
from src.models.class_models import CompanyDocument

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Definir documentos de muestra para cada metodología

ITIL_DOCS = [
    {
        "title": "ITIL Foundation Overview",
        "content": """
ITIL (Information Technology Infrastructure Library) is a framework designed to standardize the selection, planning, delivery, maintenance, and overall lifecycle of IT services within a business. The goal is to improve efficiency and achieve predictable service delivery.

ITIL Framework Core Components:
1. Service Strategy: Defines the perspective, position, plans and patterns that a service provider needs to execute to meet business outcomes.
2. Service Design: Ensures that new and changed services are designed effectively to meet customer expectations.
3. Service Transition: Ensures that new, modified or retired services meet the expectations of the business.
4. Service Operation: Coordinates and carries out activities and processes required to deliver and manage services at agreed levels.
5. Continual Service Improvement: Maintains customer value through better design, introduction, and operation of services.

ITIL 4, the latest version, introduces the Service Value System (SVS) which includes:
- The Service Value Chain
- The Four Dimensions Model
- The Seven Guiding Principles
- Governance
- Continual Improvement

Key ITIL Processes:
- Incident Management
- Problem Management
- Change Management
- Service Level Management
- Availability Management
- Capacity Management
- IT Service Continuity Management
- Information Security Management

ITIL Benefits:
- Improved service delivery and customer satisfaction
- Reduced costs through improved resource utilization
- Greater visibility of IT costs and assets
- Better management of business risk and service disruption
- More stable service environment that supports business change
        """,
        "document_type": "methodology",
        "source": "itil_framework"
    },
    {
        "title": "ITIL Service Management Practices",
        "content": """
ITIL Service Management Practices are organized into three categories:

1. General Management Practices:
   - Architecture Management: Provides a structured approach to designing and maintaining enterprise architecture.
   - Continual Improvement: Aligns organization's practices with changing business needs through improvement of services, processes, or any other element involved in managing services.
   - Information Security Management: Ensures the confidentiality, integrity, and availability of an organization's information, data, and IT services.
   - Knowledge Management: Improves decision-making by ensuring that reliable and secure information is available throughout the service lifecycle.
   - Measurement and Reporting: Supports good decision-making and continual improvement by decreasing uncertainty.
   - Organizational Change Management: Ensures that changes in an organization are implemented smoothly and thoroughly.
   - Portfolio Management: Ensures that an organization's portfolio of services effectively enables its strategy.
   - Project Management: Ensures that all projects are successfully delivered.
   - Relationship Management: Establishes and nurtures links between the organization and its stakeholders.
   - Risk Management: Identifies, assesses, and controls risks.
   - Service Financial Management: Ensures that the organization has an understanding of the costs of providing services.
   - Strategy Management: Formulates the goals of an organization and adopts courses of action to achieve them.
   - Supplier Management: Ensures that suppliers and their performance are managed appropriately to support the provision of seamless services.
   - Workforce and Talent Management: Ensures that the organization has the right people with the appropriate skills and knowledge.

2. Service Management Practices:
   - Availability Management: Ensures that services deliver the agreed levels of availability to meet customers' needs.
   - Business Analysis: Ensures that business requirements are properly identified and understood before changes are implemented.
   - Capacity and Performance Management: Ensures that services can meet agreed capacity and performance needs, both current and future.
   - Change Control: Maximizes the number of successful service and product changes.
   - Incident Management: Minimizes the negative impact of incidents by restoring normal service operation as quickly as possible.
   - IT Asset Management: Plans and manages the full lifecycle of all IT assets.
   - Monitoring and Event Management: Systematically observes services and service components and records and reports selected changes of state.
   - Problem Management: Reduces the likelihood and impact of incidents by identifying actual and potential causes of incidents.
   - Release Management: Makes new and changed services and features available for use.
   - Service Catalogue Management: Provides a single source of consistent information on all services and service offerings.
   - Service Configuration Management: Ensures that accurate and reliable information about the configuration of services is available when and where it is needed.
   - Service Continuity Management: Ensures that services can be delivered at the agreed levels even during a disruption.
   - Service Design: Designs products and services that are fit for purpose, fit for use, and can be delivered by the organization.
   - Service Desk: Captures demand for incident resolution and service requests.
   - Service Level Management: Sets clear business-based targets for service performance and ensures services are delivered according to agreed targets.
   - Service Request Management: Supports the agreed quality of a service by handling all pre-defined, user-initiated service requests.
   - Service Validation and Testing: Ensures that new or changed products and services match their design specifications and meet business requirements.

3. Technical Management Practices:
   - Deployment Management: Moves new or changed hardware, software, documentation, processes, or any other service component to live environments.
   - Infrastructure and Platform Management: Oversees the infrastructure and platforms used by an organization.
   - Software Development and Management: Ensures that applications meet stakeholder needs in terms of functionality, reliability, maintainability, compliance, and auditability.
        """,
        "document_type": "methodology",
        "source": "itil_framework"
    },
    {
        "title": "ITIL Incident Management Process",
        "content": """
ITIL Incident Management Process Overview:

Definition: An Incident is an unplanned interruption to an IT service or reduction in the quality of an IT service. Incident Management is the process for dealing with all incidents, including failures, questions or queries reported by users, technical staff, or automatically detected by monitoring tools.

Objective: The primary objective of Incident Management is to restore normal service operation as quickly as possible and minimize the adverse impact on business operations, thus ensuring that the best possible levels of service quality and availability are maintained.

Key Concepts:
- Incident: Any event that disrupts or could disrupt a service
- Service Restoration: Focus on restoring service rather than finding the underlying cause
- Timescales: Handling incidents based on agreed service level agreements (SLAs)
- Prioritization: Based on impact and urgency

Incident Management Process Steps:
1. Incident Identification: Recognizing that a service disruption has occurred
2. Incident Logging: Creating a formal record of the incident
3. Incident Categorization: Assigning appropriate categories for proper tracking
4. Incident Prioritization: Determining impact and urgency to set priority
5. Initial Diagnosis: First-level investigation by service desk
6. Escalation: Functional or hierarchical if necessary
7. Investigation and Diagnosis: More detailed analysis to determine resolution
8. Resolution and Recovery: Implementing the solution
9. Incident Closure: Confirming resolution and completing documentation

Roles in Incident Management:
- Service Desk: First point of contact for users, logging and initial support
- First-level Support: Basic troubleshooting and resolution
- Second-level Support: More specialized support for complex incidents
- Third-level Support: Expert support often from vendors or specialized teams
- Incident Manager: Oversees the effectiveness of the incident management process

Key Performance Indicators (KPIs):
- Total number of incidents
- Average time to resolve incidents
- Percentage of incidents resolved within SLA
- First-call resolution rate
- Number of major incidents

Major Incident Procedure:
A separate procedure for handling high-impact incidents, typically involving:
- Dedicated resources
- Higher urgency
- Management notification
- Separate reporting
- Post-incident review

Best Practices:
- Self-service options for common incidents
- Knowledge base for quick resolutions
- Clear escalation paths
- Automated incident logging
- Regular review of recurring incidents
- Linking related incidents to problem records
        """,
        "document_type": "methodology",
        "source": "itil_framework"
    }
]

COBIT_DOCS = [
    {
        "title": "COBIT Framework Overview",
        "content": """
COBIT (Control Objectives for Information and Related Technologies) is a framework created by ISACA for information technology (IT) governance and management. It provides a comprehensive framework that assists enterprises in achieving their objectives for the governance and management of enterprise IT.

COBIT 2019 Core Components:

1. Governance System and Components:
   - Governance Objectives
   - Governance Components
   - Design Factors
   - Focus Areas

2. Core Principles:
   - Principle 1: Provide Stakeholder Value
   - Principle 2: Holistic Approach
   - Principle 3: Dynamic Governance System
   - Principle 4: Governance vs. Management
   - Principle 5: Tailored to Enterprise Needs
   - Principle 6: End-to-End Governance System

3. Governance and Management Objectives:
   Organized into domains:
   - Evaluate, Direct and Monitor (EDM)
   - Align, Plan and Organize (APO)
   - Build, Acquire and Implement (BAI)
   - Deliver, Service and Support (DSS)
   - Monitor, Evaluate and Assess (MEA)

4. Governance Components:
   - Processes
   - Organizational Structures
   - Information Flows
   - People, Skills and Competencies
   - Policies and Procedures
   - Culture and Behavior
   - Services, Infrastructure and Applications

5. Design Factors:
   - Enterprise Strategy
   - Enterprise Goals
   - Risk Profile
   - I&T-Related Issues
   - Threat Landscape
   - Compliance Requirements
   - Role of IT
   - Sourcing Model
   - IT Implementation Methods
   - Technology Adoption Strategy
   - Enterprise Size

Benefits of COBIT:
- Better alignment between business goals and IT
- A more holistic view on IT governance
- Increased business user satisfaction with IT services
- Improved adherence to regulatory requirements
- Enhanced processes for IT investment decisions
- Higher quality IT services and reduced costs
- More effective management of IT-related risks
        """,
        "document_type": "methodology",
        "source": "cobit_framework"
    },
    {
        "title": "COBIT Governance and Management Objectives",
        "content": """
COBIT Governance and Management Objectives in Detail:

Evaluate, Direct and Monitor (EDM) Domain - Governance:
- EDM01: Ensured Governance Framework Setting and Maintenance
  Ensures a consistent approach integrated and aligned with the enterprise governance approach.

- EDM02: Ensured Benefits Delivery
  Secures optimal value from IT-enabled initiatives, services, and assets.

- EDM03: Ensured Risk Optimization
  Ensures risk appetite and tolerance are understood, and risk to enterprise value is identified and managed.

- EDM04: Ensured Resource Optimization
  Ensures adequate and sufficient enterprise resources (people, process, and technology).

- EDM05: Ensured Stakeholder Transparency
  Ensures enterprise IT performance and conformance reporting is transparent, with stakeholders approving goals and metrics.

Align, Plan and Organize (APO) Domain - Management:
- APO01: Managed I&T Management Framework
- APO02: Managed Strategy
- APO03: Managed Enterprise Architecture
- APO04: Managed Innovation
- APO05: Managed Portfolio
- APO06: Managed Budget and Costs
- APO07: Managed Human Resources
- APO08: Managed Relationships
- APO09: Managed Service Agreements
- APO10: Managed Vendors
- APO11: Managed Quality
- APO12: Managed Risk
- APO13: Managed Security
- APO14: Managed Data

Build, Acquire and Implement (BAI) Domain - Management:
- BAI01: Managed Programs
- BAI02: Managed Requirements Definition
- BAI03: Managed Solutions Identification and Build
- BAI04: Managed Availability and Capacity
- BAI05: Managed Organizational Change
- BAI06: Managed IT Changes
- BAI07: Managed IT Change Acceptance and Transitioning
- BAI08: Managed Knowledge
- BAI09: Managed Assets
- BAI10: Managed Configuration
- BAI11: Managed Projects

Deliver, Service and Support (DSS) Domain - Management:
- DSS01: Managed Operations
- DSS02: Managed Service Requests and Incidents
- DSS03: Managed Problems
- DSS04: Managed Continuity
- DSS05: Managed Security Services
- DSS06: Managed Business Process Controls

Monitor, Evaluate and Assess (MEA) Domain - Management:
- MEA01: Managed Performance and Conformance Monitoring
- MEA02: Managed System of Internal Control
- MEA03: Managed Compliance With External Requirements
- MEA04: Managed Assurance

Each objective includes:
- Description and purpose
- Related IT process goals
- Process inputs and outputs
- RACI chart (Responsible, Accountable, Consulted, Informed)
- Control objectives
- Management guidelines
- Maturity model

Capability Levels for Processes:
0 - Incomplete Process
1 - Performed Process
2 - Managed Process
3 - Established Process
4 - Predictable Process
5 - Optimizing Process

Implementing COBIT involves:
1. Understanding the enterprise context and strategy
2. Determining the initial scope
3. Refining the scope based on design factors
4. Planning the implementation program
5. Executing the implementation
6. Realizing benefits
7. Reviewing effectiveness
        """,
        "document_type": "methodology",
        "source": "cobit_framework"
    },
    {
        "title": "COBIT Implementation and IT Risk Management",
        "content": """
COBIT Implementation and IT Risk Management:

Implementation Phases:

Phase 1: What Are the Drivers?
- Identify change drivers and current compliance requirements
- Obtain executive management commitment
- Create desire to change

Phase 2: Where Are We Now?
- Define problems and opportunities
- Assess current process capability
- Define scope using COBIT mapping of enterprise goals to IT-related goals to processes

Phase 3: Where Do We Want to Be?
- Define target capability
- Perform gap analysis
- Identify and analyze potential improvements
- Prioritize improvement opportunities

Phase 4: What Needs to Be Done?
- Define projects
- Build a detailed implementation roadmap
- Develop business cases

Phase 5: How Do We Get There?
- Implement proposed solution
- Enable operation of the improvements
- Provide for business and IT operations
- Monitor improvement achievement

Phase 6: Did We Get There?
- Check transition to normal operations
- Assess achievement of benefits
- Review effectiveness of process metrics
- Identify additional requirements for governance or management of enterprise IT

Phase 7: How Do We Keep the Momentum Going?
- Promote a continual improvement culture
- Review overall governance and management effectiveness
- Identify other improvement opportunities

IT Risk Management through COBIT:

COBIT addresses IT risk management through several specific domains and objectives:

1. EDM03 (Ensure Risk Optimization):
   - Ensures IT-related risks do not exceed risk appetite
   - Risk is identified, managed, and reported
   - IT compliance is established
   - Controls are set effectively and efficiently

2. APO12 (Manage Risk):
   - IT risk is identified, assessed, and reduced
   - Integrates with Enterprise Risk Management (ERM)
   - Implements risk analysis for decision making
   - Process Activities:
     - Collect data
     - Analyze risk
     - Maintain a risk profile
     - Articulate risk
     - Define a risk management action portfolio
     - Respond to risk

3. APO13 (Manage Security):
   - Defines, operates, and monitors information security management system
   - Establishes information security policy and standards
   - Implements security controls
   - Monitors security performance and compliance

Risk Assessment Approach:
1. Risk Scenario Identification
2. Risk Analysis
3. Risk Response
4. Risk and Control Activities
5. Information on Risk
6. Risk Monitoring

Key Risk Management Controls and Practices:
- Risk governance oversight
- Risk appetite and tolerance establishment
- Risk awareness and communication
- Risk assessment methods and tools
- Risk response strategies
- Risk reporting and disclosure
- Risk culture development
- Risk skill development
- Assurance over risk management

Common IT Risk Scenarios Addressed:
- Unauthorized access to information systems
- System or software failure
- Project failure or cost overruns
- Data corruption or loss
- Regulatory compliance violations
- Service interruptions
- Emerging technology risks
- Third-party vendor risks
- IT skill shortages
        """,
        "document_type": "methodology",
        "source": "cobit_framework"
    }
]

TOGAF_DOCS = [
    {
        "title": "TOGAF Architecture Framework Overview",
        "content": """
TOGAF (The Open Group Architecture Framework) is a framework for enterprise architecture that provides an approach for designing, planning, implementing, and governing an enterprise information technology architecture. TOGAF is a high-level framework and methodology that can be used in conjunction with other, more detailed methods and frameworks.

TOGAF Core Components:

1. Architecture Development Method (ADM):
   The ADM is the core of TOGAF and provides a step-by-step approach to develop an enterprise architecture. It consists of several phases:
   - Preliminary Phase: Prepares an organization for successful architecture projects
   - Phase A: Architecture Vision
   - Phase B: Business Architecture
   - Phase C: Information Systems Architectures (Data and Application)
   - Phase D: Technology Architecture
   - Phase E: Opportunities and Solutions
   - Phase F: Migration Planning
   - Phase G: Implementation Governance
   - Phase H: Architecture Change Management
   - Requirements Management (central to the ADM)

2. Enterprise Continuum:
   A "virtual repository" of architecture assets that provides methods for classifying architecture and solution artifacts. It includes:
   - Architecture Continuum
   - Solutions Continuum
   - Enterprise Repository

3. Architecture Content Framework:
   Provides a structural model for architectural content, including:
   - Deliverables (formal work products)
   - Artifacts (architecture descriptions)
   - Building Blocks (components of enterprises)

4. ADM Guidelines and Techniques:
   Additional guidance for applying the ADM, including:
   - Adapting the ADM
   - Architecture Principles
   - Stakeholder Management
   - Architecture Patterns
   - Business Scenarios
   - Gap Analysis
   - Migration Planning
   - Interoperability Requirements
   - Business Transformation Readiness Assessment
   - Risk Management
   - Capability-Based Planning

5. TOGAF Reference Models:
   - Technical Reference Model (TRM)
   - Integrated Information Infrastructure Reference Model (III-RM)

6. Architecture Capability Framework:
   Provides the organizational structures, skills, roles, responsibilities, and processes for establishing and operating an architecture function.

Benefits of TOGAF:
- Proven and repeatable approach to developing architectures
- Common vocabulary and standardized methods
- Resource savings through asset reuse and reduced vendor lock-in
- Greater transparency in IT-related decision-making
- Reduced risk for future architecture projects
- More effective collaboration across the organization
- Alignment between business goals and IT systems
        """,
        "document_type": "methodology",
        "source": "togaf_framework"
    },
    {
        "title": "TOGAF Architecture Development Method (ADM)",
        "content": """
TOGAF Architecture Development Method (ADM) in Detail:

The Architecture Development Method (ADM) is the core of TOGAF, providing a tested and repeatable process for developing architectures. The ADM includes established phases for developing and managing the lifecycle of the Enterprise Architecture.

Preliminary Phase: Framework and Principles
- Define "where, what, why, who, and how" of architecture
- Establish Architecture Capability
- Define Architecture Principles
- Identify Architecture Framework
- Implement Architecture Tools

Phase A: Architecture Vision
- Develop high-level vision of capabilities and business value
- Obtain approval for statement of architecture work
- Define scope, constraints, and expectations
- Create Architecture Vision
- Identify stakeholders, concerns, and business requirements
- Confirm and elaborate business goals, drivers, and constraints

Phase B: Business Architecture
- Develop Baseline and Target Business Architectures
- Analyze gaps between them
- Define candidate roadmap components
- Define business constraints for technology
- Validate and revise business architecture principles
- Describe baseline and target business landscapes

Phase C: Information Systems Architecture
This phase addresses both the data and application systems architectures:

Data Architecture:
- Develop Baseline and Target Data Architectures
- Analyze gaps between them
- Define candidate roadmap components
- Identify data entities, data components, and their relationships
- Develop data management policies
- Map data to business services
- Establish data ownership and stewardship

Application Architecture:
- Develop Baseline and Target Application Architectures
- Analyze gaps between them
- Define candidate roadmap components
- Define major types of applications
- Create application inventory
- Map applications to business services and processes

Phase D: Technology Architecture
- Develop Baseline and Target Technology Architectures
- Analyze gaps between them
- Define candidate roadmap components
- Define technology platform services
- Create technology portfolio
- Consider platform decomposition diagrams
- Map technology to applications and data entities

Phase E: Opportunities and Solutions
- Generate the initial Architecture Roadmap
- Consolidate gap analysis results from phases B-D
- Review and consolidate requirements
- Conduct initial implementation planning
- Identify major work packages or projects
- Define Transition Architectures
- Create Architecture Implementation and Migration Plan

Phase F: Migration Planning
- Prioritize projects and develop detailed Implementation and Migration Plan
- Assess dependencies, costs, and benefits
- Generate Implementation Roadmap
- Document Migration Plan
- Finalize Architecture Roadmap and Implementation and Migration Plan
- Ensure alignment with enterprise change management approach

Phase G: Implementation Governance
- Ensure conformance of implementation projects to the architecture
- Define architecture contracts
- Implement governance processes
- Manage architecture changes during implementation
- Monitor and track compliance
- Provide implementation oversight

Phase H: Architecture Change Management
- Provide continuous monitoring and change management process
- Monitor technology changes and trends
- Monitor business changes
- Make recommendations for changes to current architecture framework
- Manage governance framework
- Activate change process for new architecture development

Requirements Management (Central to All Phases):
- Process for managing architecture requirements
- Store requirements and changes
- Assess impact on current and ongoing phases
- Implement requirements traceability
- Ensure relevant requirements are addressed

Key ADM Characteristics:
- Iterative across the whole process
- Iterative between phases
- Adaptable to different use-cases
- Scalable to different levels of architecture planning
- Centered around business requirements
- Focused on deliverables validation at each phase
- Aligned with governance processes
        """,
        "document_type": "methodology",
        "source": "togaf_framework"
    },
    {
        "title": "TOGAF Enterprise Architecture Artifacts and Deliverables",
        "content": """
TOGAF Enterprise Architecture Artifacts and Deliverables:

TOGAF Content Framework Components:

1. Deliverables: Contractually specified, formal work products; outputs of projects that are reviewed, agreed, and signed off by stakeholders. Examples include:
   - Architecture Definition Document
   - Architecture Requirements Specification
   - Architecture Roadmap
   - Transition Architecture
   - Implementation and Migration Plan
   - Architecture Contract
   - Architecture Vision
   - Statement of Architecture Work
   - Architecture Compliance Statement

2. Artifacts: Describes a single aspect of the architecture; can include diagrams, catalog entries, matrices. Examples include:
   
   Catalogs (lists of items):
   - Actor Catalog
   - Role Catalog
   - Business Service/Function Catalog
   - Application Portfolio Catalog
   - Data Entity Catalog
   - Technology Portfolio Catalog
   - Principles Catalog
   
   Matrices (show relationships between items):
   - Business Interaction Matrix
   - Actor/Role Matrix
   - Business Function/Organization Matrix
   - Organization/Application Matrix
   - Process/Application Matrix
   - Application/Data Matrix
   - Application/Technology Matrix
   - Data/Application Matrix
   
   Diagrams (graphical representations):
   - Business Ecosystem Diagram
   - Organization Chart
   - Process Flow Diagram
   - Business Footprint Diagram
   - System Context Diagram
   - Information Exchange Diagram
   - Application Communication Diagram
   - Solution Concept Diagram
   - Platform Decomposition Diagram
   - Networked Computing/Hardware Diagram

3. Building Blocks: Components (potentially reusable) that can be combined with other building blocks to deliver architectures and solutions. Two types:
   - Architecture Building Blocks (ABBs)
   - Solution Building Blocks (SBBs)

Viewpoints and Views in TOGAF:

1. Viewpoints: A way of looking at a system from a particular perspective or standpoint. Types include:
   - Business Architecture Viewpoints
   - Data Architecture Viewpoints
   - Application Architecture Viewpoints
   - Technology Architecture Viewpoints
   - Enterprise Security Viewpoints
   - Enterprise Manageability Viewpoints
   - Enterprise Quality of Service Viewpoints
   - Enterprise Mobility Viewpoints

2. Views: What stakeholders actually see; a representation of a system from a particular viewpoint. Common views include:
   - Strategic/Executive View
   - Operational/Management View
   - Architect View
   - Designer View
   - Builder View
   - Subcontractor View

TOGAF Deliverables by ADM Phase:

Preliminary Phase:
- Architecture Principles
- Organization Model for Enterprise Architecture
- Architecture Compliance Statement
- Architecture Capability Maturity Assessment

Phase A: Architecture Vision
- Architecture Vision
- Statement of Architecture Work
- Communications Plan
- Stakeholder Map Matrix
- Value Chain Diagram

Phase B: Business Architecture
- Organization Structure Diagram
- Business Service/Function Catalog
- Business Interaction Matrix
- Actor/Role Matrix
- Business Footprint Diagram
- Process Flow Diagram

Phase C: Information Systems Architecture
- Data Entity Catalog
- Data Entity/Business Function Matrix
- Application Portfolio Catalog
- Interface Catalog
- Application/Organization Matrix
- System/Data Matrix

Phase D: Technology Architecture
- Technology Portfolio Catalog
- Technology Standards Catalog
- Environments and Locations Diagram
- Platform Decomposition Diagram
- Network Computing Diagram

Phase E: Opportunities and Solutions
- Project Context Diagram
- Benefits Diagram
- Solution Concept Diagram
- Capability Assessment
- Implementation Factor Assessment and Deduction Matrix

Phase F: Migration Planning
- Implementation and Migration Plan
- Architecture Roadmap
- Transition Architecture
- Implementation Governance Model

Phase G: Implementation Governance
- Architecture Contract
- Compliance Assessment
- Implementation Governance Reference

Phase H: Architecture Change Management
- Change Request
- Architecture Compliance Assessment
- Architecture Requirements Impact Assessment
        """,
        "document_type": "methodology",
        "source": "togaf_framework"
    }
]

def create_sample_documents() -> List[Dict[str, Any]]:
    """Create sample documents for testing.
    
    Returns:
        List of document dictionaries
    """
    # Combine all sample docs
    all_docs = []
    all_docs.extend(ITIL_DOCS)
    all_docs.extend(COBIT_DOCS)
    all_docs.extend(TOGAF_DOCS)
    
    # Add IDs and clean up
    for i, doc in enumerate(all_docs):
        doc["id"] = f"sample_doc_{str(uuid.uuid4())[:8]}"
        # Trim whitespace in content
        doc["content"] = doc["content"].strip()
        
    return all_docs

def load_documents(vector_store: VectorStoreService, documents: List[Dict[str, Any]]) -> None:
    """Load documents into the vector store.
    
    Args:
        vector_store: Vector store service
        documents: List of document dictionaries
    """
    # Convert dictionaries to CompanyDocument objects
    company_docs = []
    for doc in documents:
        company_doc = CompanyDocument(
            id=doc["id"],
            title=doc["title"],
            content=doc["content"],
            document_type=doc["document_type"],
            source=doc["source"],
            metadata={"sample": True}
        )
        company_docs.append(company_doc)
    
    # Add documents to vector store
    doc_ids = vector_store.add_documents(company_docs)
    logger.info(f"Added {len(doc_ids)} documents to vector store")

def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Load sample data into the vector store")
    parser.add_argument("--clear", action="store_true", help="Clear existing documents before loading")
    parser.add_argument("--output", help="Output sample documents to a JSON file")
    args = parser.parse_args()
    
    # Create vector store service
    vector_store = VectorStoreService()
    
    # Clear existing documents if requested
    if args.clear:
        logger.info("Clearing existing documents")
        vector_store.clear_all_documents()
    
    # Create sample documents
    logger.info("Creating sample documents")
    sample_docs = create_sample_documents()
    
    # Output sample documents to a JSON file if requested
    if args.output:
        logger.info(f"Writing sample documents to {args.output}")
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(sample_docs, f, ensure_ascii=False, indent=2)
    
    # Load documents into vector store
    logger.info("Loading documents into vector store")
    load_documents(vector_store, sample_docs)
    
    logger.info("Done")

if __name__ == "__main__":
    main() 