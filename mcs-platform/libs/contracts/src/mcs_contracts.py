"""MCS Contracts - Package entry point.

This module re-exports everything from the src package to allow
'from mcs_contracts import ...' imports to work.
"""

# Import everything from the modules in the same directory
# This works both when installed (mcs_contracts.py is in site-packages) 
# and in development mode (mcs_contracts.py is in src/)
import sys
from pathlib import Path

# Determine the src directory location
# When installed as editable: __file__ is a symlink/copy in site-packages, 
# but the actual source is in the original location
_current_file = Path(__file__).resolve()
_src_dir = _current_file.parent

# If installed as editable, find the actual source location
if 'site-packages' in str(_current_file):
    # For editable installs, find the actual source directory
    # The editable install adds the package root to sys.path, so we can find it
    try:
        # Use importlib.metadata instead of deprecated pkg_resources
        try:
            from importlib.metadata import distributions
        except ImportError:
            # Python < 3.8 fallback
            from importlib_metadata import distributions
        
        # For editable installs, check sys.path for the package root
        # The package root (where pyproject.toml is) should be in sys.path
        package_root = None
        for path_str in sys.path:
            path = Path(path_str)
            # Look for the contracts package root (contains pyproject.toml and src/)
            if path.exists() and (path / 'pyproject.toml').exists() and (path / 'src').exists():
                # Check if this is the contracts package
                try:
                    if Path(path / 'pyproject.toml').read_text().find('mcs-contracts') >= 0:
                        package_root = path
                        break
                except Exception:
                    pass
        
        # If found, use src/ subdirectory
        if package_root:
            potential_src = package_root / 'src'
            if potential_src.exists():
                _src_dir = potential_src
    except Exception:
        pass

# Add src directory to path if not already there and it exists
if not _src_dir.exists() or str(_src_dir) not in sys.path:
    # Try to find src directory from package root in sys.path
    found_src = False
    for path_str in sys.path:
        path = Path(path_str)
        if not path.exists():
            continue
        # Check if this is the contracts package root
        pyproject_file = path / 'pyproject.toml'
        if pyproject_file.exists():
            try:
                content = pyproject_file.read_text(encoding='utf-8')
                if 'name = "mcs-contracts"' in content:
                    potential_src = path / 'src'
                    if potential_src.exists() and (potential_src / 'common.py').exists():
                        _src_dir = potential_src
                        found_src = True
                        break
            except Exception:
                pass
        # Or check if this is already the src directory
        elif path.name == 'src' and (path / 'common.py').exists():
            # Verify parent is contracts package
            parent = path.parent
            if (parent / 'pyproject.toml').exists():
                try:
                    content = (parent / 'pyproject.toml').read_text(encoding='utf-8')
                    if 'name = "mcs-contracts"' in content:
                        _src_dir = path
                        found_src = True
                        break
                except Exception:
                    pass
    
    # Add to sys.path if found and not already there
    if found_src and str(_src_dir) not in sys.path:
        sys.path.insert(0, str(_src_dir))
elif _src_dir.exists() and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Import from the src directory modules
from common import ErrorInfo, StatusEnum, now_iso
from email_event import EmailAttachment, EmailEvent
from masterdata import Company, Contact, Customer, MasterData, Product
from orchestrator import (
    ManualReviewCandidateContact,
    ManualReviewCandidateCustomer,
    ManualReviewCandidatePdf,
    ManualReviewCandidates,
    ManualReviewDecision,
    ManualReviewSubmitRequest,
    ManualReviewSubmitResponse,
    OrchestratorRunResult,
)
from results import (
    ContactMatchResult,
    ContractSignalResult,
    CustomerMatchResult,
    DifyContractResult,
    DifyOrderPayloadResult,
    ERPCreateOrderResult,
    FileUploadResult,
)

__version__ = "0.1.0"

__all__ = [
    # Common
    "StatusEnum",
    "ErrorInfo",
    "now_iso",
    # Email
    "EmailEvent",
    "EmailAttachment",
    # Master Data
    "MasterData",
    "Customer",
    "Contact",
    "Company",
    "Product",
    # Results
    "ContactMatchResult",
    "ContractSignalResult",
    "CustomerMatchResult",
    "FileUploadResult",
    "DifyContractResult",
    "DifyOrderPayloadResult",
    "ERPCreateOrderResult",
    # Orchestrator
    "OrchestratorRunResult",
    # Manual Review
    "ManualReviewCandidates",
    "ManualReviewCandidateCustomer",
    "ManualReviewCandidateContact",
    "ManualReviewCandidatePdf",
    "ManualReviewDecision",
    "ManualReviewSubmitRequest",
    "ManualReviewSubmitResponse",
]
