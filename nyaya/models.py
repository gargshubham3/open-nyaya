from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class MappingTarget(BaseModel):
    act: str
    section: str
    sub_section: Optional[str] = None
    title: str
    chapter: Optional[str] = None

class MappingSource(BaseModel):
    act: str
    section: str
    sub_section: Optional[str] = None
    title: str
    chapter: Optional[str] = None

class MappingResult(BaseModel):
    id: str
    lookup_key: str
    status: str  # Retained, Modified, Repealed, New
    mapping_statement: str
    source: Optional[MappingSource] = None
    target: Optional[MappingTarget] = None
    full_text: Optional[str] = None

class SectionCharge(BaseModel):
    act: str
    section: str
    description: Optional[str] = None
    bailable: Optional[bool] = None
    compoundable: Optional[bool] = None
    max_punishment_years: Optional[float] = None
    cognizable: Optional[bool] = None

class AccusedPerson(BaseModel):
    name: str
    alias: Optional[str] = None
    age: Optional[int] = None
    parentage: Optional[str] = None
    address: Optional[str] = None
    is_arrested: bool = False
    arrest_datetime: Optional[str] = None
    custody_days: Optional[int] = None
    is_first_offender: bool = True

class FIRDetails(BaseModel):
    fir_number: str
    year: int
    police_station: str
    district: str
    state: str = "State"
    date_of_occurrence: Optional[str] = None
    date_of_report: Optional[str] = None
    complainant_name: Optional[str] = None
    accused_list: List[AccusedPerson] = Field(default_factory=list)
    sections_charged: List[SectionCharge] = Field(default_factory=list)
    allegations_summary: Optional[str] = None
    # Procedural metadata
    section_35_notice_issued: Optional[bool] = None  # Old CrPC 41A / BNSS 35
    videography_recorded: Optional[bool] = None      # BNSS 105
    independent_witness_present: Optional[bool] = None # BNSS 36
    magistrate_production_hours: Optional[float] = None # Art 22(2)
    recovery_made: Optional[bool] = None
    medical_examination_done: Optional[bool] = None

class AuditFlag(BaseModel):
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    rule_id: str
    title: str
    violation_detail: str
    statutory_reference: str
    judicial_precedent: str
    suggested_defense_argument: str

class AuditReport(BaseModel):
    fir_number: str
    police_station: str
    accused_name: str
    flags: List[AuditFlag]
    bail_favourability_score: int  # 0 to 100
    summary: str
    cross_examination_questions: List[str]

class BailApplicationDraft(BaseModel):
    court_heading: str
    case_title: str
    accused_name: str
    fir_number: str
    police_station: str
    statutory_provision: str  # e.g., Section 480 of BNSS, 2023
    charges_formatted: str
    grounds: List[str]
    precedent_citations: List[str]
    undertakings: List[str]
    prayer: str
    verification: str
    formatted_document: str
