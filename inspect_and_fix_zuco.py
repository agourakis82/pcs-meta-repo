#!/usr/bin/env python3
"""
Execute ZuCo structure inspection and create targeted fix
Research-grade analysis of ZuCo data format
"""

import os
import subprocess
import sys
from pathlib import Path


def run_inspection_and_fix():
    """Run ZuCo inspection and create targeted fix"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    os.chdir(repo_path)

    print("🔍 EXECUTING ZuCo Structure Inspection & Fix")
    print("=" * 60)

    # Step 1: Run the inspection
    print("Step 1: Inspecting ZuCo .mat file structure...")

    try:
        result = subprocess.run(
            [sys.executable, "inspect_zuco_structure.py"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=30,
        )

        print("Inspection Output:")
        print(result.stdout)

        if result.stderr:
            print("Inspection Errors:")
            print(result.stderr)

        # Store the inspection output for analysis
        inspection_output = result.stdout

    except subprocess.TimeoutExpired:
        print("❌ Inspection timed out")
        return False
    except Exception as e:
        print(f"❌ Inspection failed: {e}")
        return False

    # Step 2: Analyze inspection results and suggest fixes
    print("\n" + "=" * 50)
    print("Step 2: Analyzing inspection results...")

    # Look for key indicators in the output
    has_main_data = "Main data key:" in inspection_output
    has_attributes = "attributes:" in inspection_output.lower()
    has_fields = "fields:" in inspection_output.lower()
    has_sentence_data = "sentence" in inspection_output.lower()
    has_word_data = "word" in inspection_output.lower()
    has_rt_measures = any(
        rt in inspection_output for rt in ["FFD", "GD", "TRT", "nFixations"]
    )

    print(f"Analysis results:")
    print(f"  Has main data structure: {has_main_data}")
    print(f"  Has object attributes: {has_attributes}")
    print(f"  Has struct fields: {has_fields}")
    print(f"  Has sentence data: {has_sentence_data}")
    print(f"  Has word data: {has_word_data}")
    print(f"  Has RT measures: {has_rt_measures}")

    # Step 3: Create a more targeted ZuCo inspection
    print("\n" + "=" * 50)
    print("Step 3: Creating detailed ZuCo structure probe...")

    detailed_probe_code = '''
import scipy.io
import numpy as np
from pathlib import Path

def detailed_zuco_probe():
    """Detailed probe of ZuCo structure"""
    
    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    zuco_path = repo_path / "scripts/data/raw_public/zuco/v1/osfstorage/answers"
    
    # Find NR files
    nr_files = list(zuco_path.glob("Fullresults_NR_*.mat"))
    if not nr_files:
        print("No NR files found")
        return
    
    test_file = nr_files[0]
    print(f"Detailed probe of: {test_file.name}")
    
    try:
        # Load with different options
        print("\\nTrying different loading options...")
        
        # Option 1: Default
        mat_data = scipy.io.loadmat(str(test_file))
        print(f"Default load keys: {[k for k in mat_data.keys() if not k.startswith('__')]}")
        
        # Option 2: With squeeze_me and struct_as_record=False
        mat_data2 = scipy.io.loadmat(str(test_file), squeeze_me=True, struct_as_record=False)
        print(f"Structured load keys: {[k for k in mat_data2.keys() if not k.startswith('__')]}")
        
        # Option 3: With struct_as_record=True (default)
        mat_data3 = scipy.io.loadmat(str(test_file), squeeze_me=True, struct_as_record=True)
        print(f"Record load keys: {[k for k in mat_data3.keys() if not k.startswith('__')]}")
        
        # Explore the main data structure in detail
        for i, (load_type, data) in enumerate([
            ("default", mat_data), 
            ("structured", mat_data2), 
            ("record", mat_data3)
        ]):
            print(f"\\n--- {load_type.upper()} LOADING ---")
            
            data_keys = [k for k in data.keys() if not k.startswith('__')]
            if data_keys:
                main_key = data_keys[0]
                main_data = data[main_key]
                
                print(f"Main key: {main_key}")
                print(f"Main data type: {type(main_data)}")
                print(f"Main data shape: {getattr(main_data, 'shape', 'no shape')}")
                print(f"Main data dtype: {getattr(main_data, 'dtype', 'no dtype')}")
                
                # If it's a numpy array with structured dtype
                if hasattr(main_data, 'dtype') and main_data.dtype.names:
                    print(f"Structured array field names: {main_data.dtype.names}")
                    
                    # Show first element
                    if len(main_data) > 0:
                        first_elem = main_data[0]
                        print(f"First element type: {type(first_elem)}")
                        print(f"First element: {first_elem}")
                        
                        # If it's a tuple/record, show fields
                        if hasattr(first_elem, '_fields') or isinstance(first_elem, tuple):
                            print(f"First element fields: {getattr(first_elem, '_fields', 'tuple')}")
                
                # If it's an object array
                elif hasattr(main_data, '__len__') and len(main_data) > 0:
                    first_item = main_data[0] if hasattr(main_data, '__getitem__') else main_data
                    print(f"First item type: {type(first_item)}")
                    
                    if hasattr(first_item, '__dict__'):
                        attrs = [attr for attr in dir(first_item) if not attr.startswith('_')]
                        print(f"First item attributes: {attrs[:10]}...")  # Limit output
                    
                    # Check for common ZuCo patterns
                    for attr in ['sentence', 'sentenceData', 'content', 'rawData']:
                        if hasattr(first_item, attr):
                            attr_data = getattr(first_item, attr)
                            print(f"Found {attr}: {type(attr_data)}, shape: {getattr(attr_data, 'shape', 'no shape')}")
                
                if i == 1:  # Focus on structured loading for word-level analysis
                    print("\\n--- WORD-LEVEL ANALYSIS ---")
                    try:
                        # Try to navigate to word level
                        test_paths = [
                            lambda d: d,  # Direct
                            lambda d: d[0] if hasattr(d, '__getitem__') and len(d) > 0 else None,
                            lambda d: getattr(d, 'sentence', None),
                            lambda d: getattr(d[0], 'sentence', None) if hasattr(d, '__getitem__') and len(d) > 0 else None,
                        ]
                        
                        for path_idx, path_func in enumerate(test_paths):
                            try:
                                candidate = path_func(main_data)
                                if candidate is not None:
                                    print(f"Path {path_idx}: {type(candidate)}")
                                    
                                    # Look for sentence/word structure
                                    if hasattr(candidate, '__len__') and len(candidate) > 0:
                                        first_sent = candidate[0] if hasattr(candidate, '__getitem__') else candidate
                                        print(f"  First sentence type: {type(first_sent)}")
                                        
                                        if hasattr(first_sent, 'word'):
                                            words = first_sent.word
                                            print(f"  Words type: {type(words)}, len: {len(words) if hasattr(words, '__len__') else 'no len'}")
                                            
                                            if hasattr(words, '__len__') and len(words) > 0:
                                                first_word = words[0] if hasattr(words, '__getitem__') else words
                                                print(f"  First word type: {type(first_word)}")
                                                
                                                # Check for RT fields
                                                rt_fields = ['FFD', 'GD', 'TRT', 'nFixations', 'content']
                                                for field in rt_fields:
                                                    if hasattr(first_word, field):
                                                        value = getattr(first_word, field)
                                                        print(f"    {field}: {value} (type: {type(value)})")
                            except Exception as e:
                                print(f"Path {path_idx} failed: {e}")
                    
                    except Exception as e:
                        print(f"Word-level analysis failed: {e}")
                
    except Exception as e:
        print(f"Detailed probe failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    detailed_zuco_probe()
'''

    # Write and execute the detailed probe
    detailed_probe_file = repo_path / "detailed_zuco_probe.py"
    with open(detailed_probe_file, "w") as f:
        f.write(detailed_probe_code)

    print("Created detailed_zuco_probe.py")

    # Run the detailed probe
    try:
        result = subprocess.run(
            [sys.executable, "detailed_zuco_probe.py"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=45,
        )

        print("Detailed Probe Output:")
        print(result.stdout)

        if result.stderr:
            print("Detailed Probe Errors:")
            print(result.stderr)

        # Store detailed output
        detailed_output = result.stdout

    except Exception as e:
        print(f"Detailed probe failed: {e}")
        detailed_output = ""

    # Step 4: Based on findings, suggest next steps
    print("\n" + "=" * 50)
    print("Step 4: Next Steps Based on Findings")

    if "Found" in detailed_output and any(
        field in detailed_output for field in ["FFD", "GD", "TRT"]
    ):
        print("✅ RT measures found! Need to update loader with correct structure.")
        print("📋 Action: Update zuco_real_loader.py with discovered structure")
    elif "sentence" in detailed_output.lower() and "word" in detailed_output.lower():
        print("✅ Word-level structure found! Need to adjust field access.")
        print("📋 Action: Update field extraction logic")
    elif "Structured array" in detailed_output:
        print("✅ Structured array format detected!")
        print("📋 Action: Use numpy structured array access")
    else:
        print("⚠️  Complex structure - need manual analysis")
        print("📋 Action: Review detailed output and create custom loader")

    print(f"\n📊 Files created:")
    print(f"  - detailed_zuco_probe.py (detailed structure analysis)")
    print(f"\n🚀 Next: Based on findings, update the ZuCo loader")


if __name__ == "__main__":
    run_inspection_and_fix()
