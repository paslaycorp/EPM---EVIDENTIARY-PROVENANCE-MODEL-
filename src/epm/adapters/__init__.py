"""Reference domain adapters for EPM."""
from .common import AdapterInputError, DomainTransition, build_domain_envelope
from .insurance import InsuranceEvidenceUse, insurance_envelope
from .legal import LegalEvidenceUse, legal_envelope
from .scientific import ScientificEvidenceUse, scientific_envelope

__all__ = [
    "AdapterInputError",
    "DomainTransition",
    "InsuranceEvidenceUse",
    "LegalEvidenceUse",
    "ScientificEvidenceUse",
    "build_domain_envelope",
    "insurance_envelope",
    "legal_envelope",
    "scientific_envelope",
]
