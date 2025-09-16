#!/usr/bin/env python3
"""
SWOW Multilingual Infrastructure Audit Script

This script performs a comprehensive audit of the SWOW multilingual functionality
and KEC metrics integration pipeline, ensuring all components work correctly
for all supported languages (EN, ES, ZH, NL).

Author: PCS Meta-Repo Audit System
License: MIT
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class SWOWMultilingualAuditor:
    """Comprehensive auditor for SWOW multilingual functionality"""

    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.supported_languages = ["en", "es", "zh", "nl"]
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "audit_version": "1.0.0",
            "languages_tested": self.supported_languages,
            "phases": {},
            "summary": {},
            "issues": [],
            "recommendations": [],
        }

        # Create audit output directory
        self.output_dir = self.repo_root / "reports" / "swow_multilingual_audit"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("🔍 SWOW Multilingual Infrastructure Audit")
        print("=" * 50)
        print(f"Repository: {self.repo_root}")
        print(f"Languages: {', '.join(self.supported_languages)}")
        print(f"Output: {self.output_dir}")
        print()

    def audit_phase_1_core_infrastructure(self) -> Dict[str, Any]:
        """Phase 1: Core Infrastructure Audit"""
        print("📋 Phase 1: Core Infrastructure Audit")
        print("-" * 40)

        phase_results = {
            "phase": "core_infrastructure",
            "status": "in_progress",
            "components": {},
            "issues": [],
            "passed_checks": 0,
            "total_checks": 0,
        }

        # 1.1 SWOW Data Pipeline Verification
        print("🔍 1.1 Auditing SWOW Data Pipeline...")
        swow_pipeline_results = self._audit_swow_pipeline()
        phase_results["components"]["swow_pipeline"] = swow_pipeline_results

        # 1.2 KEC Metrics Computation Audit
        print("🔍 1.2 Auditing KEC Metrics Computation...")
        kec_metrics_results = self._audit_kec_metrics()
        phase_results["components"]["kec_metrics"] = kec_metrics_results

        # 1.3 Integration Pipeline Audit
        print("🔍 1.3 Auditing Integration Pipeline...")
        integration_results = self._audit_integration_pipeline()
        phase_results["components"]["integration_pipeline"] = integration_results

        # 1.4 Missing Files Assessment
        print("🔍 1.4 Assessing Missing Files...")
        missing_files_results = self._audit_missing_files()
        phase_results["components"]["missing_files"] = missing_files_results

        # Calculate phase summary
        for component in phase_results["components"].values():
            phase_results["passed_checks"] += component.get("passed_checks", 0)
            phase_results["total_checks"] += component.get("total_checks", 0)
            phase_results["issues"].extend(component.get("issues", []))

        phase_results["status"] = "completed"
        phase_results["success_rate"] = (
            phase_results["passed_checks"] / phase_results["total_checks"]
            if phase_results["total_checks"] > 0
            else 0
        )

        self.audit_results["phases"]["phase_1"] = phase_results
        return phase_results

    def _audit_swow_pipeline(self) -> Dict[str, Any]:
        """Audit SWOW data loading pipeline"""
        results = {
            "component": "swow_pipeline",
            "status": "testing",
            "language_results": {},
            "issues": [],
            "passed_checks": 0,
            "total_checks": 0,
        }

        # Check core SWOW toolbox
        try:
            from pcs_toolbox.swow import load_swow_graph

            results["pcs_toolbox_swow_available"] = True
            results["passed_checks"] += 1
            print("  ✅ pcs_toolbox.swow module available")
        except ImportError as e:
            results["pcs_toolbox_swow_available"] = False
            results["issues"].append(f"Cannot import pcs_toolbox.swow: {e}")
            print(f"  ❌ pcs_toolbox.swow import failed: {e}")
        results["total_checks"] += 1

        # Check configuration files
        config_files = ["config/swow.yaml", "config/swow_paths.yaml"]

        for config_file in config_files:
            config_path = self.repo_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config_data = yaml.safe_load(f)
                    results[f"{config_file}_valid"] = True
                    results["passed_checks"] += 1
                    print(f"  ✅ {config_file} exists and valid")

                    # Check if languages are properly configured
                    if "languages" in config_data:
                        configured_langs = config_data["languages"]
                        missing_langs = set(self.supported_languages) - set(
                            configured_langs
                        )
                        if missing_langs:
                            results["issues"].append(
                                f"Missing languages in {config_file}: {missing_langs}"
                            )
                        else:
                            print(
                                f"    ✅ All languages configured: {configured_langs}"
                            )

                except Exception as e:
                    results[f"{config_file}_valid"] = False
                    results["issues"].append(f"Error reading {config_file}: {e}")
                    print(f"  ❌ Error reading {config_file}: {e}")
            else:
                results[f"{config_file}_exists"] = False
                results["issues"].append(f"Missing configuration file: {config_file}")
                print(f"  ❌ Missing: {config_file}")
            results["total_checks"] += 1

        # Check data directories for each language
        for lang in self.supported_languages:
            lang_result = self._audit_language_data_structure(lang)
            results["language_results"][lang] = lang_result
            results["passed_checks"] += lang_result["passed_checks"]
            results["total_checks"] += lang_result["total_checks"]
            results["issues"].extend(lang_result["issues"])

        results["status"] = "completed"
        return results

    def _audit_language_data_structure(self, lang: str) -> Dict[str, Any]:
        """Audit data structure for a specific language"""
        results = {
            "language": lang,
            "data_dirs_exist": False,
            "raw_data_available": False,
            "processed_data_available": False,
            "issues": [],
            "passed_checks": 0,
            "total_checks": 0,
        }

        # Check raw data directory
        raw_dir = self.repo_root / "data" / "raw_public" / "swow" / lang
        if raw_dir.exists():
            results["data_dirs_exist"] = True
            results["passed_checks"] += 1
            print(f"    ✅ {lang}: Raw data directory exists")

            # Check for CSV files
            csv_files = list(raw_dir.glob("*.csv"))
            if csv_files:
                results["raw_data_available"] = True
                results["raw_files"] = [f.name for f in csv_files]
                results["passed_checks"] += 1
                print(f"    ✅ {lang}: Raw CSV files found: {len(csv_files)}")
            else:
                results["issues"].append(f"{lang}: No CSV files in raw directory")
                print(f"    ⚠️ {lang}: No CSV files in {raw_dir}")
        else:
            results["issues"].append(f"{lang}: Raw data directory missing: {raw_dir}")
            print(f"    ❌ {lang}: Missing raw directory: {raw_dir}")
        results["total_checks"] += 2

        # Check processed data directory
        processed_dir = self.repo_root / "data" / "L2_derived" / "kec" / lang
        if processed_dir.exists():
            results["processed_data_available"] = True
            results["passed_checks"] += 1
            print(f"    ✅ {lang}: Processed data directory exists")

            # Check for expected KEC files
            expected_files = [
                "entropy.parquet",
                "curvature.parquet",
                "coherence.parquet",
            ]
            found_files = []
            for expected_file in expected_files:
                file_path = processed_dir / expected_file
                if file_path.exists():
                    found_files.append(expected_file)
                    results["passed_checks"] += 1
                else:
                    results["issues"].append(
                        f"{lang}: Missing KEC file: {expected_file}"
                    )
                results["total_checks"] += 1

            results["kec_files_found"] = found_files
            print(f"    📊 {lang}: KEC files found: {found_files}")
        else:
            results["issues"].append(
                f"{lang}: Processed data directory missing: {processed_dir}"
            )
            print(f"    ❌ {lang}: Missing processed directory: {processed_dir}")
        results["total_checks"] += 1

        return results

    def _audit_kec_metrics(self) -> Dict[str, Any]:
        """Audit KEC metrics computation functionality"""
        results = {
            "component": "kec_metrics",
            "status": "testing",
            "metrics_available": {},
            "issues": [],
            "passed_checks": 0,
            "total_checks": 0,
        }

        # Check KEC toolbox availability
        try:
            from pcs_toolbox.kec import (
                compute_kec_metrics,
                transition_entropy,
                ricci_curvature,
                meso_coherence,
            )

            results["pcs_toolbox_kec_available"] = True
            results["passed_checks"] += 1
            print("  ✅ pcs_toolbox.kec module available")

            # Test individual metric functions
            metrics_to_test = [
                ("transition_entropy", transition_entropy),
                ("ricci_curvature", ricci_curvature),
                ("meso_coherence", meso_coherence),
                ("compute_kec_metrics", compute_kec_metrics),
            ]

            for metric_name, metric_func in metrics_to_test:
                try:
                    # Test with a simple synthetic graph
                    import igraph as ig

                    g = ig.Graph(directed=True)
                    g.add_vertices(["a", "b", "c"])
                    g.add_edges([("a", "b"), ("b", "c"), ("c", "a")])
                    g.es["weight"] = [1.0, 1.0, 1.0]

                    if metric_name == "compute_kec_metrics":
                        result_df = metric_func(g)
                        expected_cols = [
                            "name",
                            "entropy",
                            "curvature",
                            "community",
                            "coherence",
                        ]
                        if all(col in result_df.columns for col in expected_cols):
                            results["metrics_available"][metric_name] = True
                            results["passed_checks"] += 1
                            print(f"    ✅ {metric_name} function works correctly")
                        else:
                            results["metrics_available"][metric_name] = False
                            results["issues"].append(
                                f"{metric_name}: Missing expected columns"
                            )
                            print(f"    ❌ {metric_name}: Missing columns in output")
                    else:
                        result_df = metric_func(g)
                        if isinstance(result_df, pd.DataFrame) and len(result_df) > 0:
                            results["metrics_available"][metric_name] = True
                            results["passed_checks"] += 1
                            print(f"    ✅ {metric_name} function works correctly")
                        else:
                            results["metrics_available"][metric_name] = False
                            results["issues"].append(
                                f"{metric_name}: Invalid output format"
                            )
                            print(f"    ❌ {metric_name}: Invalid output")

                except Exception as e:
                    results["metrics_available"][metric_name] = False
                    results["issues"].append(
                        f"{metric_name}: Error during execution: {e}"
                    )
                    print(f"    ❌ {metric_name}: Error: {e}")

                results["total_checks"] += 1

        except ImportError as e:
            results["pcs_toolbox_kec_available"] = False
            results["issues"].append(f"Cannot import pcs_toolbox.kec: {e}")
            print(f"  ❌ pcs_toolbox.kec import failed: {e}")
        results["total_checks"] += 1

        results["status"] = "completed"
        return results

    def _audit_integration_pipeline(self) -> Dict[str, Any]:
        """Audit integration pipeline functionality"""
        results = {
            "component": "integration_pipeline",
            "status": "testing",
            "pipeline_scripts": {},
            "issues": [],
            "passed_checks": 0,
            "total_checks": 0,
        }

        # Check key integration scripts
        integration_scripts = [
            "scripts/swow_zuco_pipeline.py",
            "scripts/multilanguage_swow_analysis.py",
            "scripts/multilingual_comprehensive_analysis.py",
        ]

        for script_path in integration_scripts:
            script_file = self.repo_root / script_path
            script_name = Path(script_path).name

            if script_file.exists():
                results["pipeline_scripts"][script_name] = {
                    "exists": True,
                    "executable": False,
                    "imports_valid": False,
                }
                results["passed_checks"] += 1
                print(f"  ✅ {script_name} exists")

                # Check if script is executable
                try:
                    with open(script_file, "r") as f:
                        content = f.read()

                    # Basic syntax check
                    compile(content, script_file, "exec")
                    results["pipeline_scripts"][script_name]["executable"] = True
                    results["passed_checks"] += 1
                    print(f"    ✅ {script_name} syntax valid")

                    # Check for key imports
                    key_imports = ["pandas", "numpy", "pathlib"]
                    imports_found = []
                    for imp in key_imports:
                        if f"import {imp}" in content or f"from {imp}" in content:
                            imports_found.append(imp)

                    if len(imports_found) >= 2:  # At least 2 key imports
                        results["pipeline_scripts"][script_name]["imports_valid"] = True
                        results["passed_checks"] += 1
                        print(f"    ✅ {script_name} has required imports")
                    else:
                        results["issues"].append(f"{script_name}: Missing key imports")
                        print(
                            f"    ⚠️ {script_name}: Few imports found: {imports_found}"
                        )

                except Exception as e:
                    results["issues"].append(f"{script_name}: Syntax error: {e}")
                    print(f"    ❌ {script_name}: Syntax error: {e}")

                results["total_checks"] += 2
            else:
                results["pipeline_scripts"][script_name] = {
                    "exists": False,
                    "executable": False,
                    "imports_valid": False,
                }
                results["issues"].append(f"Missing integration script: {script_path}")
                print(f"  ❌ Missing: {script_name}")

            results["total_checks"] += 1

        # Check notebooks
        key_notebooks = [
            "notebooks/01_build_swow_graph.ipynb",
            "notebooks/02_compute_kec_metrics.ipynb",
        ]

        for notebook_path in key_notebooks:
            notebook_file = self.repo_root / notebook_path
            notebook_name = Path(notebook_path).name

            if notebook_file.exists():
                results["passed_checks"] += 1
                print(f"  ✅ {notebook_name} exists")
            else:
                results["issues"].append(f"Missing notebook: {notebook_path}")
                print(f"  ❌ Missing: {notebook_name}")
            results["total_checks"] += 1

        results["status"] = "completed"
        return results

    def _audit_missing_files(self) -> Dict[str, Any]:
        """Audit and identify missing files"""
        results = {
            "component": "missing_files",
            "status": "testing",
            "missing_modules": [],
            "missing_scripts": [],
            "missing_configs": [],
            "issues": [],
            "passed_checks": 0,
            "total_checks": 0,
        }

        # Expected src/swow modules (based on VSCode tabs)
        expected_swow_modules = [
            "src/swow/__init__.py",
            "src/swow/api.py",
            "src/swow/align.py",
            "src/swow/clean_en.py",
            "src/swow/clean_es.py",
            "src/swow/clean_nl.py",
            "src/swow/clean_zh.py",
            "src/swow/graph.py",
            "src/swow/io.py",
            "src/swow/metrics_kec.py",
            "src/swow/zh_preproc.py",
        ]

        print("  🔍 Checking expected SWOW modules...")
        for module_path in expected_swow_modules:
            module_file = self.repo_root / module_path
            if module_file.exists():
                results["passed_checks"] += 1
                print(f"    ✅ {module_path}")
            else:
                results["missing_modules"].append(module_path)
                results["issues"].append(f"Missing SWOW module: {module_path}")
                print(f"    ❌ Missing: {module_path}")
            results["total_checks"] += 1

        # Check for language-specific processing completeness
        for lang in self.supported_languages:
            lang_specific_files = [
                f"src/swow/clean_{lang}.py",
                f"data/raw_public/swow/{lang}/.gitkeep",
                f"data/L2_derived/kec/{lang}/.gitkeep",
            ]

            for file_path in lang_specific_files:
                file_obj = self.repo_root / file_path
                if not file_obj.exists():
                    results["missing_scripts"].append(file_path)
                    results["issues"].append(f"Missing {lang} file: {file_path}")
                else:
                    results["passed_checks"] += 1
                results["total_checks"] += 1

        results["status"] = "completed"
        return results

    def generate_audit_report(self) -> None:
        """Generate comprehensive audit report"""
        print("\n📊 Generating Audit Report...")

        # Calculate overall summary
        total_passed = 0
        total_checks = 0
        all_issues = []

        for phase_name, phase_data in self.audit_results["phases"].items():
            total_passed += phase_data.get("passed_checks", 0)
            total_checks += phase_data.get("total_checks", 0)
            all_issues.extend(phase_data.get("issues", []))

        self.audit_results["summary"] = {
            "total_checks": total_checks,
            "passed_checks": total_passed,
            "failed_checks": total_checks - total_passed,
            "success_rate": total_passed / total_checks if total_checks > 0 else 0,
            "total_issues": len(all_issues),
            "critical_issues": len(
                [i for i in all_issues if "Missing" in i or "Error" in i]
            ),
        }

        self.audit_results["issues"] = all_issues

        # Generate recommendations
        self._generate_recommendations()

        # Save JSON report
        json_report_path = self.output_dir / "swow_multilingual_audit_report.json"
        with open(json_report_path, "w") as f:
            json.dump(self.audit_results, f, indent=2)

        # Generate markdown report
        self._generate_markdown_report()

        print(f"📄 Audit report saved to: {self.output_dir}")
        print(f"📊 Success Rate: {self.audit_results['summary']['success_rate']:.1%}")
        print(f"🔍 Total Issues: {self.audit_results['summary']['total_issues']}")

    def _generate_recommendations(self) -> None:
        """Generate recommendations based on audit results"""
        recommendations = []

        # Check for missing core modules
        if self.audit_results["phases"]["phase_1"]["components"]["missing_files"][
            "missing_modules"
        ]:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Missing Files",
                    "description": "Create missing src/swow/ modules to complete the SWOW processing pipeline",
                    "action": "Implement all missing modules in src/swow/ directory",
                }
            )

        # Check for language support issues
        phase1_results = self.audit_results["phases"]["phase_1"]
        swow_results = phase1_results["components"]["swow_pipeline"]["language_results"]

        incomplete_languages = []
        for lang, lang_data in swow_results.items():
            if not lang_data.get("processed_data_available", False):
                incomplete_languages.append(lang)

        if incomplete_languages:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Language Support",
                    "description": f"Complete KEC processing for languages: {', '.join(incomplete_languages)}",
                    "action": "Run KEC metrics computation for missing languages",
                }
            )

        # Check for integration issues
        integration_results = phase1_results["components"]["integration_pipeline"]
        broken_scripts = [
            name
            for name, data in integration_results["pipeline_scripts"].items()
            if not data.get("executable", False)
        ]

        if broken_scripts:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "Integration Pipeline",
                    "description": f"Fix broken integration scripts: {', '.join(broken_scripts)}",
                    "action": "Debug and repair script syntax and import issues",
                }
            )

        # Language standardization recommendation
        recommendations.append(
            {
                "priority": "HIGH",
                "category": "Language Standardization",
                "description": "Convert all Portuguese text to English throughout the codebase",
                "action": "Systematically translate all comments, docstrings, and documentation to English",
            }
        )

        self.audit_results["recommendations"] = recommendations

    def _generate_markdown_report(self) -> None:
        """Generate markdown audit report"""
        report_path = self.output_dir / "swow_multilingual_audit_report.md"

        with open(report_path, "w") as f:
            f.write("# SWOW Multilingual Infrastructure Audit Report\n\n")
            f.write(f"**Generated:** {self.audit_results['timestamp']}\n")
            f.write(f"**Audit Version:** {self.audit_results['audit_version']}\n")
            f.write(
                f"**Languages Tested:** {', '.join(self.audit_results['languages_tested'])}\n\n"
            )

            # Executive Summary
            summary = self.audit_results["summary"]
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Checks:** {summary['total_checks']}\n")
            f.write(f"- **Passed:** {summary['passed_checks']}\n")
            f.write(f"- **Failed:** {summary['failed_checks']}\n")
            f.write(f"- **Success Rate:** {summary['success_rate']:.1%}\n")
            f.write(f"- **Total Issues:** {summary['total_issues']}\n")
            f.write(f"- **Critical Issues:** {summary['critical_issues']}\n\n")

            # Phase Results
            f.write("## Phase 1: Core Infrastructure Audit\n\n")
            phase1 = self.audit_results["phases"]["phase_1"]
            f.write(f"**Status:** {phase1['status']}\n")
            f.write(f"**Success Rate:** {phase1['success_rate']:.1%}\n\n")

            # Component Details
            for comp_name, comp_data in phase1["components"].items():
                f.write(f"### {comp_name.replace('_', ' ').title()}\n\n")
                f.write(
                    f"- **Passed:** {comp_data['passed_checks']}/{comp_data['total_checks']}\n"
                )
                if comp_data["issues"]:
                    f.write("- **Issues:**\n")
                    for issue in comp_data["issues"]:
                        f.write(f"  - {issue}\n")
                f.write("\n")

            # Recommendations
            f.write("## Recommendations\n\n")
            for i, rec in enumerate(self.audit_results["recommendations"], 1):
                f.write(f"### {i}. {rec['category']} ({rec['priority']} Priority)\n\n")
                f.write(f"**Description:** {rec['description']}\n\n")
                f.write(f"**Action:** {rec['action']}\n\n")

            # All Issues
            f.write("## All Issues Identified\n\n")
            for i, issue in enumerate(self.audit_results["issues"], 1):
                f.write(f"{i}. {issue}\n")

    def run_complete_audit(self) -> Dict[str, Any]:
        """Run the complete multilingual audit"""
        try:
            # Phase 1: Core Infrastructure
            self.audit_phase_1_core_infrastructure()

            # Generate comprehensive report
            self.generate_audit_report()

            print("\n🎉 SWOW Multilingual Audit Completed!")
            print(
                f"📊 Overall Success Rate: {self.audit_results['summary']['success_rate']:.1%}"
            )

            return self.audit_results

        except Exception as e:
            print(f"\n❌ Audit failed with error: {e}")
            traceback.print_exc()
            return {"error": str(e), "traceback": traceback.format_exc()}


def main():
    """Main execution function"""
    print("🚀 Starting SWOW Multilingual Infrastructure Audit")
    print("=" * 60)

    auditor = SWOWMultilingualAuditor()
    results = auditor.run_complete_audit()

    if "error" not in results:
        print("\n✅ Audit completed successfully!")
        print(f"📁 Reports available in: {auditor.output_dir}")
    else:
        print("\n❌ Audit failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
