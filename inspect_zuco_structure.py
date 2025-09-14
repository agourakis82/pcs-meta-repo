#!/usr/bin/env python3
"""
Inspect ZuCo .mat file structure to understand the data format
Research-grade analysis of ZuCo data structure
"""

import logging
from pathlib import Path

import numpy as np
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def inspect_zuco_structure():
    """Inspect the actual structure of ZuCo .mat files"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    zuco_path = repo_path / "scripts/data/raw_public/zuco/v1/osfstorage/answers"

    print("🔍 INSPECTING ZuCo .mat File Structure")
    print("=" * 60)

    # Find one NR file to inspect
    nr_files = list(zuco_path.glob("Fullresults_NR_*.mat"))
    if not nr_files:
        print("❌ No NR files found")
        return

    test_file = nr_files[0]
    print(f"Inspecting: {test_file.name}")

    try:
        # Load the .mat file
        mat_data = scipy.io.loadmat(
            str(test_file), squeeze_me=True, struct_as_record=False
        )

        print(
            f"\nTop-level keys: {[k for k in mat_data.keys() if not k.startswith('__')]}"
        )

        # Examine the main data structure
        data_keys = [k for k in mat_data.keys() if not k.startswith("__")]
        if data_keys:
            main_key = data_keys[0]
            main_data = mat_data[main_key]

            print(f"\nMain data key: '{main_key}'")
            print(f"Main data type: {type(main_data)}")

            # If it's a struct-like object, explore its attributes
            if hasattr(main_data, "__dict__"):
                attrs = [attr for attr in dir(main_data) if not attr.startswith("_")]
                print(f"Attributes: {attrs}")
            elif hasattr(main_data, "_fieldnames"):
                print(f"Field names: {main_data._fieldnames}")

            # Try to explore common ZuCo data patterns
            print(f"\nExploring data structure...")

            # Check if it's an array of structs
            if hasattr(main_data, "__len__") and len(main_data) > 0:
                print(f"Data length: {len(main_data)}")
                first_item = (
                    main_data[0]
                    if isinstance(main_data, (list, np.ndarray))
                    else main_data
                )

                if hasattr(first_item, "__dict__"):
                    item_attrs = [
                        attr for attr in dir(first_item) if not attr.startswith("_")
                    ]
                    print(f"First item attributes: {item_attrs}")
                elif hasattr(first_item, "_fieldnames"):
                    print(f"First item fields: {first_item._fieldnames}")

                # Look for common ZuCo fields
                common_fields = [
                    "sentence",
                    "content",
                    "word",
                    "data",
                    "sentenceData",
                    "rawData",
                ]
                for field in common_fields:
                    if hasattr(first_item, field):
                        field_data = getattr(first_item, field)
                        print(f"Found field '{field}': {type(field_data)}")

                        # If it's sentence data, explore further
                        if field in ["sentence", "sentenceData"] and hasattr(
                            field_data, "__len__"
                        ):
                            if len(field_data) > 0:
                                first_sent = (
                                    field_data[0]
                                    if isinstance(field_data, (list, np.ndarray))
                                    else field_data
                                )
                                if hasattr(first_sent, "__dict__"):
                                    sent_attrs = [
                                        attr
                                        for attr in dir(first_sent)
                                        if not attr.startswith("_")
                                    ]
                                    print(f"  Sentence attributes: {sent_attrs}")
                                elif hasattr(first_sent, "_fieldnames"):
                                    print(
                                        f"  Sentence fields: {first_sent._fieldnames}"
                                    )

                                # Look for word-level data
                                if hasattr(first_sent, "word") and hasattr(
                                    first_sent.word, "__len__"
                                ):
                                    if len(first_sent.word) > 0:
                                        first_word = (
                                            first_sent.word[0]
                                            if isinstance(
                                                first_sent.word, (list, np.ndarray)
                                            )
                                            else first_sent.word
                                        )
                                        if hasattr(first_word, "__dict__"):
                                            word_attrs = [
                                                attr
                                                for attr in dir(first_word)
                                                if not attr.startswith("_")
                                            ]
                                            print(f"    Word attributes: {word_attrs}")
                                        elif hasattr(first_word, "_fieldnames"):
                                            print(
                                                f"    Word fields: {first_word._fieldnames}"
                                            )

                                        # Check for RT measures
                                        rt_fields = [
                                            "FFD",
                                            "GD",
                                            "TRT",
                                            "nFixations",
                                            "firstFixationDuration",
                                            "gazeDuration",
                                            "totalReadingTime",
                                        ]
                                        for rt_field in rt_fields:
                                            if hasattr(first_word, rt_field):
                                                rt_value = getattr(first_word, rt_field)
                                                print(
                                                    f"      Found RT measure '{rt_field}': {rt_value} (type: {type(rt_value)})"
                                                )

            # Show raw structure for debugging
            print(f"\nRaw main_data inspection:")
            if hasattr(main_data, "dtype"):
                print(f"dtype: {main_data.dtype}")
            if hasattr(main_data, "shape"):
                print(f"shape: {main_data.shape}")

    except Exception as e:
        print(f"❌ Failed to inspect file: {e}")
        import traceback

        traceback.print_exc()


def suggest_fixes():
    """Suggest fixes based on inspection"""
    print(f"\n🔧 SUGGESTED FIXES:")
    print("=" * 30)
    print("1. Update zuco_real_loader.py to handle the discovered structure")
    print("2. Look for alternative field names for sentences/words")
    print("3. Handle different ZuCo data format versions")
    print("4. Add more robust structure detection")


if __name__ == "__main__":
    inspect_zuco_structure()
    suggest_fixes()
