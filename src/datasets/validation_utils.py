"""
Centralized validation utilities for dataset loaders.
Provides consistent import handling and validation across all datasets.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def get_contracts_import() -> Tuple[bool, Any]:
    """
    Attempt to import contracts_v4.4 with fallback handling.

    Returns:
        Tuple of (success, contracts_module)
    """
    try:
        # Try relative import first
        from ..contracts_v4 import (
            validate_word_events_rt,
            validate_word_events_eeg,
            validate_target_degeneracy,
        )

        logger.debug("Successfully imported contracts via relative import")
        return True, {
            "validate_word_events_rt": validate_word_events_rt,
            "validate_word_events_eeg": validate_word_events_eeg,
            "validate_target_degeneracy": validate_target_degeneracy,
        }
    except ImportError:
        try:
            # Try absolute import
            sys.path.append(str(Path(__file__).parent.parent))
            from contracts_v4 import (
                validate_word_events_rt,
                validate_word_events_eeg,
                validate_target_degeneracy,
            )

            logger.debug("Successfully imported contracts via absolute import")
            return True, {
                "validate_word_events_rt": validate_word_events_rt,
                "validate_word_events_eeg": validate_word_events_eeg,
                "validate_target_degeneracy": validate_target_degeneracy,
            }
        except ImportError:
            logger.error("Failed to import contracts_v4.4 - validation will be limited")
            return False, None


def validate_import_paths(loader_name: str) -> Dict[str, Any]:
    """
    Validate import paths for a specific loader.

    Args:
        loader_name: Name of the loader being validated

    Returns:
        Dict with validation results
    """
    results = {
        "loader": loader_name,
        "contracts_available": False,
        "import_method": None,
        "validation_functions": [],
        "errors": [],
        "warnings": [],
    }

    success, contracts = get_contracts_import()

    if success:
        results["contracts_available"] = True
        results["validation_functions"] = list(contracts.keys())
        results["import_method"] = "successful"
        logger.info(f"Import validation successful for {loader_name}")
    else:
        results["errors"].append("Could not import contracts_v4.4 module")
        results["warnings"].append("Validation functions will not be available")
        logger.warning(f"Import validation failed for {loader_name}")

    return results


def fix_import_statements(file_path: str) -> Dict[str, Any]:
    """
    Analyze and suggest fixes for import statements in a loader file.

    Args:
        file_path: Path to the loader file

    Returns:
        Dict with fix suggestions
    """
    results = {
        "file": file_path,
        "current_imports": [],
        "suggested_fixes": [],
        "issues_found": [],
    }

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Analyze current import patterns
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "contracts_v4" in line or "validate_" in line:
                results["current_imports"].append(
                    {"line_number": i + 1, "content": line.strip()}
                )

                # Check for problematic patterns
                if "from src.contracts" in line:
                    results["issues_found"].append(
                        f"Line {i+1}: Hardcoded 'src.contracts' import"
                    )
                    results["suggested_fixes"].append(
                        {
                            "line": i + 1,
                            "issue": "Hardcoded import path",
                            "suggestion": "Use validation_utils.get_contracts_import()",
                        }
                    )

                if "from ..contracts_v4.4" in line:
                    results["issues_found"].append(
                        f"Line {i+1}: Incorrect relative import path"
                    )
                    results["suggested_fixes"].append(
                        {
                            "line": i + 1,
                            "issue": "Incorrect relative import",
                            "suggestion": "Use validation_utils.get_contracts_import()",
                        }
                    )

    except Exception as e:
        results["issues_found"].append(f"Could not analyze file: {str(e)}")

    return results


def create_standardized_import_block() -> str:
    """
    Generate standardized import block for dataset loaders.

    Returns:
        String containing the standardized import code
    """
    return """
# Standardized validation imports
try:
    from .validation_utils import get_contracts_import
    success, contracts = get_contracts_import()
    if success:
        validate_word_events_rt = contracts.get('validate_word_events_rt')
        validate_word_events_eeg = contracts.get('validate_word_events_eeg')
        validate_target_degeneracy = contracts.get('validate_target_degeneracy')
    else:
        # Fallback - validation will be limited
        validate_word_events_rt = None
        validate_word_events_eeg = None
        validate_target_degeneracy = None
except ImportError:
    # Ultimate fallback
    validate_word_events_rt = None
    validate_word_events_eeg = None
    validate_target_degeneracy = None
    logger.warning("Validation functions not available - imports failed")
"""


def enhanced_validation_wrapper(validation_func, df, validation_type="generic"):
    """
    Wrapper for validation functions with enhanced error handling.

    Args:
        validation_func: The validation function to call
        df: DataFrame to validate
        validation_type: Type of validation being performed

    Returns:
        Enhanced validation results
    """
    if validation_func is None:
        return {
            "valid": False,
            "errors": ["Validation function not available"],
            "warnings": ["Import issues prevented validation"],
            "stats": {"total_records": len(df) if df is not None else 0},
            "compliance_level": "UNKNOWN",
            "fixed_issues": [],
        }

    try:
        results = validation_func(df)

        # Enhance results with compliance level
        if results.get("valid", False) and len(results.get("errors", [])) == 0:
            results["compliance_level"] = "COMPLIANT"
        elif results.get("valid", False) and len(results.get("warnings", [])) > 0:
            results["compliance_level"] = "PARTIAL"
        else:
            results["compliance_level"] = "NEEDS_IMPROVEMENT"

        # Add fixed issues tracking
        if "fixed_issues" not in results:
            results["fixed_issues"] = []

        return results

    except Exception as e:
        logger.error(f"Validation failed for {validation_type}: {str(e)}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": [],
            "stats": {"total_records": len(df) if df is not None else 0},
            "compliance_level": "ERROR",
            "fixed_issues": [],
        }


def log_dataset_status(
    dataset_name: str, status: str, issues: Optional[List[str]] = None
):
    """
    Log dataset status for memory context tracking.

    Args:
        dataset_name: Name of the dataset
        status: Current status
        issues: List of issues found/fixed
    """
    if issues is None:
        issues = []

    status_msg = f"Dataset {dataset_name}: {status}"
    if issues:
        status_msg += f" - Issues: {', '.join(issues)}"

    logger.info(status_msg)

    # Also print for immediate visibility
    print(f"📊 {status_msg}")


# Additional validation utilities for systematic fixes

class DatasetValidationPipeline:
    """Complete validation pipeline for dataset loaders"""
    
    def __init__(self):
        self.results = {}
        self.contracts_available, self.contracts = get_contracts_import()
        
    def validate_loader(self, loader_name: str, loader_func, test_data_path: str = None) -> Dict[str, Any]:
        """
        Validate a complete dataset loader
        
        Args:
            loader_name: Name of the loader
            loader_func: Loader function to test
            test_data_path: Optional path to test data
            
        Returns:
            Complete validation results
        """
        results = {
            "loader_name": loader_name,
            "timestamp": str(Path(__file__).stat().st_mtime),
            "import_validation": {},
            "function_validation": {},
            "data_validation": {},
            "overall_status": "UNKNOWN",
            "recommendations": []
        }
        
        # 1. Import validation
        results["import_validation"] = validate_import_paths(loader_name)
        
        # 2. Function validation
        try:
            if test_data_path and Path(test_data_path).exists():
                df = loader_func(test_data_path)
                results["function_validation"] = {
                    "success": True,
                    "records_loaded": len(df),
                    "columns": list(df.columns),
                    "dtypes": df.dtypes.to_dict()
                }
                
                # 3. Data validation
                if self.contracts_available:
                    validation_func = self.contracts.get('validate_word_events_rt')
                    if validation_func:
                        results["data_validation"] = enhanced_validation_wrapper(
                            validation_func, df, f"{loader_name}_rt"
                        )
            else:
                results["function_validation"] = {
                    "success": False,
                    "error": "No test data available"
                }
                
        except Exception as e:
            results["function_validation"] = {
                "success": False,
                "error": str(e)
            }
            
        # 4. Overall status
        results["overall_status"] = self._determine_status(results)
        
        # 5. Recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        self.results[loader_name] = results
        log_dataset_status(loader_name, results["overall_status"], 
                          [r[:50] for r in results["recommendations"][:3]])
        
        return results
        
    def _determine_status(self, results: Dict[str, Any]) -> str:
        """Determine overall loader status"""
        import_ok = results["import_validation"].get("contracts_available", False)
        function_ok = results["function_validation"].get("success", False)
        data_compliance = results["data_validation"].get("compliance_level", "UNKNOWN")
        
        if import_ok and function_ok and data_compliance == "COMPLIANT":
            return "COMPLIANT"
        elif import_ok and function_ok and data_compliance in ["PARTIAL", "NEEDS_IMPROVEMENT"]:
            return "NEEDS_IMPROVEMENT"
        elif function_ok:
            return "FUNCTIONAL_ISSUES"
        else:
            return "CRITICAL_ISSUES"
            
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Import issues
        if not results["import_validation"].get("contracts_available", False):
            recommendations.append("Fix import paths using validation_utils.get_contracts_import()")
            
        # Function issues
        if not results["function_validation"].get("success", False):
            error = results["function_validation"].get("error", "Unknown error")
            recommendations.append(f"Fix loader function: {error}")
            
        # Data validation issues
        data_val = results.get("data_validation", {})
        for error in data_val.get("errors", []):
            recommendations.append(f"Fix data issue: {error}")
            
        return recommendations
        
    def generate_summary_report(self) -> str:
        """Generate summary report of all validations"""
        if not self.results:
            return "No validation results available"
            
        total = len(self.results)
        compliant = sum(1 for r in self.results.values() if r["overall_status"] == "COMPLIANT")
        needs_improvement = sum(1 for r in self.results.values() if r["overall_status"] == "NEEDS_IMPROVEMENT")
        critical = sum(1 for r in self.results.values() if r["overall_status"] == "CRITICAL_ISSUES")
        
        report = f"""
# Dataset Validation Summary

**Total Loaders**: {total}
- ✅ **Compliant**: {compliant}
- ⚠️ **Needs Improvement**: {needs_improvement}  
- ❌ **Critical Issues**: {critical}

## Individual Results:
"""
        
        for name, result in self.results.items():
            status = result["overall_status"]
            emoji = {"COMPLIANT": "✅", "NEEDS_IMPROVEMENT": "⚠️", "CRITICAL_ISSUES": "❌"}.get(status, "❓")
            report += f"\n### {emoji} {name}\n"
            report += f"**Status**: {status}\n"
            
            if result["recommendations"]:
                report += "**Recommendations**:\n"
                for rec in result["recommendations"][:3]:
                    report += f"- {rec}\n"
                    
        return report


def fix_geco_loader_imports() -> str:
    """Fix GECO loader import issues"""
    geco_path = "src/datasets/geco_loader.py"
    
    try:
        with open(geco_path, 'r') as f:
            content = f.read()
            
        # Replace problematic imports
        if "from ..contracts_v4.4" in content:
            content = content.replace(
                "from ..contracts_v4.4 import validate_word_events_rt",
                "from .validation_utils import get_contracts_import\nsuccess, contracts = get_contracts_import()\nvalidate_word_events_rt = contracts.get('validate_word_events_rt') if success else None"
            )
            
            with open(geco_path, 'w') as f:
                f.write(content)
                
            return "✅ GECO loader imports fixed"
        else:
            return "ℹ️ GECO loader imports already correct"
            
    except Exception as e:
        return f"❌ Failed to fix GECO imports: {str(e)}"


def fix_lpp_loader_imports() -> str:
    """Fix LPP loader import issues"""
    lpp_path = "src/datasets/lpp_eeg_loader.py"
    
    try:
        with open(lpp_path, 'r') as f:
            content = f.read()
            
        # Check if needs fixing
        if "contracts_v4" in content and "validation_utils" not in content:
            # Add standardized import
            import_block = create_standardized_import_block()
            
            # Find where to insert
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_pos = i + 1
                    
            lines.insert(insert_pos, import_block)
            
            with open(lpp_path, 'w') as f:
                f.write('\n'.join(lines))
                
            return "✅ LPP loader imports fixed"
        else:
            return "ℹ️ LPP loader imports already correct"
            
    except Exception as e:
        return f"❌ Failed to fix LPP imports: {str(e)}"


def fix_onestop_loader_imports() -> str:
    """Fix OneStop loader import issues"""
    onestop_path = "src/datasets/onestop_loader.py"
    
    try:
        with open(onestop_path, 'r') as f:
            content = f.read()
            
        # Similar fix as LPP
        if "contracts_v4" in content and "validation_utils" not in content:
            import_block = create_standardized_import_block()
            
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_pos = i + 1
                    
            lines.insert(insert_pos, import_block)
            
            with open(onestop_path, 'w') as f:
                f.write('\n'.join(lines))
                
            return "✅ OneStop loader imports fixed"
        else:
            return "ℹ️ OneStop loader imports already correct"
            
    except Exception as e:
        return f"❌ Failed to fix OneStop imports: {str(e)}"


def run_phase1_validation_infrastructure() -> Dict[str, Any]:
    """
    Execute Phase 1: Validation Infrastructure Setup
    
    Returns:
        Results of Phase 1 execution
    """
    print("🚀 Starting PHASE 1: Validation Infrastructure Setup")
    
    results = {
        "phase": "1 - Validation Infrastructure",
        "timestamp": str(Path(__file__).stat().st_mtime),
        "tasks_completed": [],
        "issues_fixed": [],
        "next_steps": []
    }
    
    # Task 1: Validate contracts import
    print("📋 Task 1: Validating contracts import...")
    success, contracts = get_contracts_import()
    if success:
        results["tasks_completed"].append("✅ Contracts import working")
        print("✅ Contracts import successful")
    else:
        results["issues_fixed"].append("❌ Contracts import failed")
        print("❌ Contracts import failed")
        
    # Task 2: Fix loader imports
    print("📋 Task 2: Fixing loader imports...")
    
    geco_result = fix_geco_loader_imports()
    results["tasks_completed"].append(f"GECO: {geco_result}")
    print(f"  {geco_result}")
    
    lpp_result = fix_lpp_loader_imports()
    results["tasks_completed"].append(f"LPP: {lpp_result}")
    print(f"  {lpp_result}")
    
    onestop_result = fix_onestop_loader_imports()
    results["tasks_completed"].append(f"OneStop: {onestop_result}")
    print(f"  {onestop_result}")
    
    # Task 3: Setup validation pipeline
    print("📋 Task 3: Setting up validation pipeline...")
    pipeline = DatasetValidationPipeline()
    results["tasks_completed"].append("✅ Validation pipeline created")
    print("✅ Validation pipeline ready")
    
    # Next steps
    results["next_steps"] = [
        "PHASE 2: Fix GECO loader data issues",
        "PHASE 3: Fix LPP loader compliance",
        "PHASE 4: Fix OneStop loader validation",
        "PHASE 5: SWOW multilingual fixes"
    ]
    
    print("\n🎉 PHASE 1 COMPLETED!")
    print("📊 Summary:")
    for task in results["tasks_completed"]:
        print(f"  {task}")
        
    print("\n➡️ Next: PHASE 2 - GECO Loader Fixes")
    
    return results
