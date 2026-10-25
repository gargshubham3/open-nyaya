"""
open-nyaya: Open-Source AI and Legal Computing Toolkit for Modern Indian Law.
Maps old colonial criminal laws (IPC, CrPC, IEA) to Bharatiya Nyaya Sanhita (BNS),
Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA),
audits procedural violations, and generates district court pleadings.
"""

from nyaya.mapper import LawMapper
from nyaya.auditor import CaseAuditor
from nyaya.parser import FIRParser
from nyaya.drafter import BailDrafter
from nyaya.models import (
    MappingResult,
    FIRDetails,
    AccusedPerson,
    SectionCharge,
    AuditFlag,
    AuditReport,
    BailApplicationDraft,
)

__version__ = "0.1.0"
__all__ = [
    "LawMapper",
    "CaseAuditor",
    "FIRParser",
    "BailDrafter",
    "MappingResult",
    "FIRDetails",
    "AccusedPerson",
    "SectionCharge",
    "AuditFlag",
    "AuditReport",
    "BailApplicationDraft",
]
