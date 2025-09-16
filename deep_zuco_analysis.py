#!/usr/bin/env python3
"""
Deep ZuCo .mat file structure analyzer
Research-grade investigation of actual data structure
"""

import logging
from pathlib import Path

import numpy as np
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def deep_zuco_analysis():
    """Perform deep analysis of ZuCo .mat file structure"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    zuco_path = repo_path / "scripts/data/raw_public/zuco/v1/osfstorage/answers"

    print("🔬 DEEP ZUCO STRUCTURE ANALYSIS")
    print("=" * 60)

    # Get one NR file for deep analysis
    nr_files = list(zuco_path.glob("Fullresults_NR_*.mat"))
    if not nr_files:
        print("❌ No NR files found")
        return

    test_file = nr_files[0]
    print(f"Analyzing: {test_file.name}")

    try:
        # Load with different methods
        print(f"\n1. LOADING WITH DIFFERENT METHODS")
        print("-" * 40)

        # Method 1: Default loading
        print("Method 1: Default loading")
        mat_default = scipy.io.loadmat(str(test_file))
        print(f"  Keys: {[k for k in mat_default.keys() if not k.startswith('__')]}")

        # Method 2: Structured loading
        print("Method 2: Structured loading (struct_as_record=False)")
        mat_struct = scipy.io.loadmat(
            str(test_file), squeeze_me=True, struct_as_record=False
        )
        print(f"  Keys: {[k for k in mat_struct.keys() if not k.startswith('__')]}")

        # Method 3: Record loading
        print("Method 3: Record loading (struct_as_record=True)")
        mat_record = scipy.io.loadmat(
            str(test_file), squeeze_me=True, struct_as_record=True
        )
        print(f"  Keys: {[k for k in mat_record.keys() if not k.startswith('__')]}")

        print(f"\n2. DEEP STRUCTURE EXPLORATION")
        print("-" * 40)

        # Focus on structured loading (most promising)
        data_keys = [k for k in mat_struct.keys() if not k.startswith("__")]
        if data_keys:
            main_key = data_keys[0]
            main_data = mat_struct[main_key]

            print(f"Main key: '{main_key}'")
            print(f"Main data type: {type(main_data)}")
            print(f"Main data shape: {getattr(main_data, 'shape', 'No shape')}")
            print(f"Main data dtype: {getattr(main_data, 'dtype', 'No dtype')}")

            # If it's an array, explore its contents
            if hasattr(main_data, "__len__"):
                print(f"Length: {len(main_data)}")

                if len(main_data) > 0:
                    print(f"\n3. EXPLORING FIRST ELEMENT")
                    print("-" * 40)

                    first_elem = main_data[0]
                    print(f"First element type: {type(first_elem)}")

                    # Get all attributes/fields
                    if hasattr(first_elem, "__dict__"):
                        attrs = [
                            attr for attr in dir(first_elem) if not attr.startswith("_")
                        ]
                        print(f"Attributes: {attrs}")
                    elif hasattr(first_elem, "_fieldnames"):
                        print(f"Field names: {first_elem._fieldnames}")
                    elif hasattr(first_elem, "dtype") and hasattr(
                        first_elem.dtype, "names"
                    ):
                        print(f"Structured array fields: {first_elem.dtype.names}")

                    # Test every possible attribute for data
                    print(f"\n4. TESTING ALL POSSIBLE ATTRIBUTES")
                    print("-" * 40)

                    possible_attrs = []
                    if hasattr(first_elem, "__dict__"):
                        possible_attrs = [
                            attr for attr in dir(first_elem) if not attr.startswith("_")
                        ]
                    elif hasattr(first_elem, "_fieldnames"):
                        possible_attrs = list(first_elem._fieldnames)
                    elif hasattr(first_elem, "dtype") and hasattr(
                        first_elem.dtype, "names"
                    ):
                        possible_attrs = list(first_elem.dtype.names)

                    for attr in possible_attrs:
                        try:
                            if hasattr(first_elem, attr):
                                value = getattr(first_elem, attr)
                                print(
                                    f"  {attr}: {type(value)}, shape: {getattr(value, 'shape', 'no shape')}"
                                )

                                # If this looks like sentence data, explore deeper
                                if hasattr(value, "__len__") and len(value) > 0:
                                    try:
                                        sub_elem = (
                                            value[0]
                                            if hasattr(value, "__getitem__")
                                            else value
                                        )
                                        if hasattr(sub_elem, "__dict__") or hasattr(
                                            sub_elem, "_fieldnames"
                                        ):
                                            print(f"    -> Contains structured data")

                                            # Look for word-like structures
                                            sub_attrs = []
                                            if hasattr(sub_elem, "__dict__"):
                                                sub_attrs = [
                                                    a
                                                    for a in dir(sub_elem)
                                                    if not a.startswith("_")
                                                ]
                                            elif hasattr(sub_elem, "_fieldnames"):
                                                sub_attrs = list(sub_elem._fieldnames)

                                            word_attrs = [
                                                a
                                                for a in sub_attrs
                                                if "word" in a.lower()
                                            ]
                                            if word_attrs:
                                                print(
                                                    f"    -> Found word-related attrs: {word_attrs}"
                                                )

                                                # Explore word structure
                                                for word_attr in word_attrs:
                                                    try:
                                                        word_data = getattr(
                                                            sub_elem, word_attr
                                                        )
                                                        print(
                                                            f"      {word_attr}: {type(word_data)}"
                                                        )

                                                        if (
                                                            hasattr(
                                                                word_data, "__len__"
                                                            )
                                                            and len(word_data) > 0
                                                        ):
                                                            first_word = (
                                                                word_data[0]
                                                                if hasattr(
                                                                    word_data,
                                                                    "__getitem__",
                                                                )
                                                                else word_data
                                                            )
                                                            print(
                                                                f"        First word type: {type(first_word)}"
                                                            )

                                                            # Look for RT measures
                                                            word_attrs_list = []
                                                            if hasattr(
                                                                first_word, "__dict__"
                                                            ):
                                                                word_attrs_list = [
                                                                    a
                                                                    for a in dir(
                                                                        first_word
                                                                    )
                                                                    if not a.startswith(
                                                                        "_"
                                                                    )
                                                                ]
                                                            elif hasattr(
                                                                first_word,
                                                                "_fieldnames",
                                                            ):
                                                                word_attrs_list = list(
                                                                    first_word._fieldnames
                                                                )

                                                            rt_attrs = [
                                                                a
                                                                for a in word_attrs_list
                                                                if any(
                                                                    rt in a
                                                                    for rt in [
                                                                        "FFD",
                                                                        "GD",
                                                                        "TRT",
                                                                        "fix",
                                                                        "content",
                                                                        "word",
                                                                    ]
                                                                )
                                                            ]
                                                            if rt_attrs:
                                                                print(
                                                                    f"        RT/Word attrs: {rt_attrs}"
                                                                )
                                                    except Exception as e:
                                                        print(
                                                            f"      Error exploring {word_attr}: {e}"
                                                        )
                                    except Exception as e:
                                        print(f"    Error exploring sub-element: {e}")

                        except Exception as e:
                            print(f"  Error accessing {attr}: {e}")

            print(f"\n5. RAW DATA INSPECTION")
            print("-" * 40)

            # Show raw structure for manual inspection
            print("Raw main_data structure:")
            print(f"  Type: {type(main_data)}")
            if hasattr(main_data, "__array_interface__"):
                print(f"  Array interface: {main_data.__array_interface__}")
            if hasattr(main_data, "dtype"):
                print(f"  Dtype: {main_data.dtype}")
                if hasattr(main_data.dtype, "descr"):
                    print(f"  Dtype description: {main_data.dtype.descr}")

            # Try to access as different data types
            print(f"\n6. ALTERNATIVE ACCESS METHODS")
            print("-" * 40)

            # Try accessing as structured array
            if hasattr(main_data, "dtype") and main_data.dtype.names:
                print("Structured array access:")
                for field_name in main_data.dtype.names:
                    try:
                        field_data = main_data[field_name]
                        print(
                            f"  {field_name}: {type(field_data)}, shape: {getattr(field_data, 'shape', 'no shape')}"
                        )
                    except Exception as e:
                        print(f"  {field_name}: Error - {e}")

            # Try direct indexing patterns
            print("Direct access patterns:")
            try:
                print(f"  main_data.flat[0]: {type(main_data.flat[0])}")
            except:
                pass

            try:
                print(f"  main_data.item(): {type(main_data.item())}")
            except:
                pass

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    deep_zuco_analysis()

    print(f"\n🔍 ANALYSIS COMPLETE")
    print(
        "Based on the findings above, I can create a targeted fix for the ZuCo loader."
    )
    print("The key is to identify the exact path to sentence/word data.")
