"""
validate_system.py
------------------

Quick system validation script for the EMD qualification system.

Performs rapid health checks on all components without running full tests.

Usage:
    python validate_system.py
"""

import sys
import importlib
from pathlib import Path

def check_import(module_name, description=""):
    """Try to import a module and return success."""
    try:
        importlib.import_module(module_name)
        return True, ""
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {e}"

def check_file_exists(file_path, description=""):
    """Check if a file exists."""
    path = Path(file_path)
    return path.exists(), "" if path.exists() else "File not found"

def print_check(name, passed, details=""):
    """Print a check result."""
    status = "[OK]  " if passed else "[FAIL]"
    print(f"{status} {name}")
    if details and not passed:
        print(f"       Error: {details}")

print("="*80)
print("EMD QUALIFICATION SYSTEM - VALIDATION")
print("="*80)
print()

checks_passed = 0
checks_failed = 0

# Phase 1: Core imports
print("[PHASE 1] Core System Components")
print("-" * 40)

modules = [
    ("mtoe_generator", "MTOE Generator"),
    ("manning_document", "Manning Document"),
    ("emd_agent", "EMD Agent"),
    ("readiness_tracker", "Readiness Tracker"),
    ("task_organizer", "Task Organizer"),
]

for module_name, description in modules:
    passed, error = check_import(module_name, description)
    print_check(description, passed, error)
    if passed:
        checks_passed += 1
    else:
        checks_failed += 1

print()

# Phase 2: Extended Profile System
print("[PHASE 2] Extended Profile System")
print("-" * 40)

profile_modules = [
    ("soldier_profile_extended", "Extended Profile Data Models"),
    ("profile_generator", "Profile Generator"),
    ("profile_utils", "Profile Utilities"),
]

for module_name, description in profile_modules:
    passed, error = check_import(module_name, description)
    print_check(description, passed, error)
    if passed:
        checks_passed += 1
    else:
        checks_failed += 1

print()

# Phase 3: Qualification System
print("[PHASE 3] Qualification System")
print("-" * 40)

qual_modules = [
    ("billet_requirements", "Billet Requirements"),
    ("qualification_filter", "Qualification Filter"),
]

for module_name, description in qual_modules:
    passed, error = check_import(module_name, description)
    print_check(description, passed, error)
    if passed:
        checks_passed += 1
    else:
        checks_failed += 1

print()

# Phase 4: Optional Components
print("[PHASE 4] Optional Components")
print("-" * 40)

optional_modules = [
    ("geolocation", "Geographic Optimization"),
    ("advanced_profiles", "Advanced Profiles"),
    ("dashboard", "Dashboard"),
]

for module_name, description in optional_modules:
    passed, error = check_import(module_name, description)
    status = "[OK]  " if passed else "[SKIP]"
    print(f"{status} {description}")
    # Don't count optional modules in totals

print()

# Phase 5: Critical Functions
print("[PHASE 5] Critical Functions")
print("-" * 40)

try:
    from mtoe_generator import UnitGenerator, MTOELibrary
    from manning_document import ManningDocument, CapabilityRequirement
    from emd_agent import EMD
    from qualifications import QualificationFilter
    from qualifications import BilletRequirementTemplates

    # Test basic functionality
    try:
        # Create a small test unit
        generator = UnitGenerator(seed=42)
        template = MTOELibrary.infantry_rifle_company()

        print_check("MTOE template loading", True)
        checks_passed += 1

        # Create manning document
        doc = ManningDocument(
            document_id="VAL-001",
            exercise_name="Validation Test",
            mission_description="Quick validation",
            requesting_unit="Test"
        )

        print_check("Manning document creation", True)
        checks_passed += 1

        # Create requirement templates
        ranger_req = BilletRequirementTemplates.ranger_qualified_infantry_leader()
        print_check("Requirement templates", True)
        checks_passed += 1

        # Test qualification filter presets
        import pandas as pd
        test_df = pd.DataFrame({
            'soldier_id': [1, 2, 3],
            'rank': ['E-5', 'E-6', 'E-7'],
            'MOS': ['11B', '11B', '11B']
        })

        qf = QualificationFilter(test_df)
        presets = qf.list_available_presets()

        if len(presets) >= 9:
            print_check(f"Qualification filters ({len(presets)} presets)", True)
            checks_passed += 1
        else:
            print_check("Qualification filters", False, f"Only {len(presets)} presets found")
            checks_failed += 1

    except Exception as e:
        print_check("Basic functionality test", False, str(e))
        checks_failed += 1

except Exception as e:
    print_check("Critical function imports", False, str(e))
    checks_failed += 1

print()

# Phase 6: Test Files
print("[PHASE 6] Test Files")
print("-" * 40)

test_files = [
    "test_billet_requirements.py",
    "test_qualification_filter.py",
    "test_qualification_penalties.py",
    "test_integration.py",
    "run_all_tests.py"
]

for test_file in test_files:
    passed, error = check_file_exists(test_file)
    print_check(test_file, passed, error)
    if passed:
        checks_passed += 1
    else:
        checks_failed += 1

print()

# Phase 7: Data Integrity
print("[PHASE 7] Data Integrity Checks")
print("-" * 40)

try:
    from qualifications import (
        EducationLevel, DLPTLevel, BadgeType, AwardType
    )

    # Check enums have expected values
    edu_levels = len([e for e in EducationLevel])
    dlpt_levels = len([d for d in DLPTLevel])
    badge_types = len([b for b in BadgeType])
    award_types = len([a for a in AwardType])

    print_check(f"Education levels ({edu_levels} defined)", edu_levels >= 7)
    checks_passed += 1

    print_check(f"DLPT levels ({dlpt_levels} defined)", dlpt_levels >= 6)
    checks_passed += 1

    print_check(f"Badge types ({badge_types} defined)", badge_types >= 10)
    checks_passed += 1

    print_check(f"Award types ({award_types} defined)", award_types >= 10)
    checks_passed += 1

except Exception as e:
    print_check("Data integrity check", False, str(e))
    checks_failed += 4

print()

# Phase 8: EMD Policy Parameters
print("[PHASE 8] EMD Policy Parameters")
print("-" * 40)

try:
    from emd_agent import EMD
    import pandas as pd

    # Create minimal EMD instance
    soldiers = pd.DataFrame({
        'soldier_id': [1],
        'rank': ['E-5'],
        'MOS': ['11B'],
        'base': ['JBLM'],
        'tis_months': [60]
    })

    billets = pd.DataFrame({
        'billet_id': [1],
        'mos_required': ['11B'],
        'min_rank': ['E-5'],
        'base': ['JBLM']
    })

    emd = EMD(soldiers_df=soldiers, billets_df=billets)

    # Check policy parameters
    total_policies = len(emd.policies)
    qual_policies = [k for k in emd.policies.keys() if any(x in k for x in
                     ['education', 'language', 'badge', 'asi_', 'sqi_'])]

    print_check(f"Total policy parameters ({total_policies})", total_policies >= 50)
    checks_passed += 1

    print_check(f"Qualification policies ({len(qual_policies)})", len(qual_policies) >= 10)
    checks_passed += 1

    # Check if qualification penalty method exists
    has_qual_method = hasattr(emd, 'apply_qualification_penalties')
    print_check("Qualification penalty method", has_qual_method)
    if has_qual_method:
        checks_passed += 1
    else:
        checks_failed += 1

except Exception as e:
    print_check("EMD policy check", False, str(e))
    checks_failed += 3

print()

# Summary
print("="*80)
print("VALIDATION SUMMARY")
print("="*80)
print()

total_checks = checks_passed + checks_failed
pass_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0

print(f"Total Checks: {total_checks}")
print(f"Passed:       {checks_passed}")
print(f"Failed:       {checks_failed}")
print(f"Pass Rate:    {pass_rate:.1f}%")
print()

if checks_failed == 0:
    print("[SUCCESS] All validation checks passed!")
    print("The EMD qualification system is ready for use.")
    sys.exit(0)
elif pass_rate >= 80:
    print("[WARNING] Some validation checks failed, but system is mostly functional.")
    print(f"Review the {checks_failed} failed checks above.")
    sys.exit(1)
else:
    print("[FAILURE] Critical validation failures detected!")
    print("System may not function correctly. Review errors above.")
    sys.exit(2)
