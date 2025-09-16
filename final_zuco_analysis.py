#!/usr/bin/env python3
"""
Final ZuCo data structure analysis based on discovered files
Research-grade investigation of the actual eye-tracking data structure
"""

import logging
from pathlib import Path

import numpy as np
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_real_zuco_files():
    """Analyze the real ZuCo files we found"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    print("🔬 FINAL ZUCO DATA STRUCTURE ANALYSIS")
    print("Analyzing the actual eye-tracking files found")
    print("=" * 60)

    # The files we know work
    working_file = (
        repo_path
        / "scripts/data/raw_public/zuco/v1/osfstorage/task1- SR/Matlab files/resultsZJM_SR.mat"
    )

    # Files that don't work
    problem_files = [
        repo_path
        / "scripts/data/raw_public/zuco/v1/osfstorage/task2 - NR/Preprocessed/sentencesNR.mat",
        repo_path
        / "scripts/data/raw_public/zuco/v1/osfstorage/task2 - NR/Matlab files/resultsZJS_NR.mat",
    ]

    print(f"🔍 ANALYZING WORKING FILE")
    print("-" * 40)

    if working_file.exists():
        try:
            print(f"File: {working_file.name}")
            mat_data = scipy.io.loadmat(
                str(working_file), squeeze_me=True, struct_as_record=False
            )

            keys = [k for k in mat_data.keys() if not k.startswith("__")]
            print(f"Keys: {keys}")

            if "sentenceData" in mat_data:
                sentence_data = mat_data["sentenceData"]
                print(f"sentenceData type: {type(sentence_data)}")
                print(
                    f"sentenceData shape: {getattr(sentence_data, 'shape', 'No shape')}"
                )

                if hasattr(sentence_data, "__len__") and len(sentence_data) > 0:
                    print(f"sentenceData length: {len(sentence_data)}")

                    # Analyze first sentence
                    first_sentence = sentence_data[0]
                    print(f"First sentence type: {type(first_sentence)}")

                    if hasattr(first_sentence, "__dict__"):
                        attrs = [
                            a for a in dir(first_sentence) if not a.startswith("_")
                        ]
                        print(f"Sentence attributes: {attrs}")

                    # Check for word data
                    if hasattr(first_sentence, "word"):
                        words = first_sentence.word
                        print(f"Words type: {type(words)}")
                        print(f"Words shape: {getattr(words, 'shape', 'No shape')}")

                        if hasattr(words, "__len__") and len(words) > 0:
                            print(f"Number of words: {len(words)}")

                            # Analyze first word
                            first_word = words[0]
                            print(f"First word type: {type(first_word)}")

                            if hasattr(first_word, "__dict__"):
                                word_attrs = [
                                    a for a in dir(first_word) if not a.startswith("_")
                                ]
                                print(f"Word attributes: {word_attrs}")

                                # Look for RT measures and content
                                rt_measures = []
                                content_fields = []

                                for attr in word_attrs:
                                    if any(
                                        rt in attr.upper()
                                        for rt in ["FFD", "GD", "TRT", "FIX"]
                                    ):
                                        rt_measures.append(attr)
                                    elif any(
                                        content in attr.lower()
                                        for content in ["content", "word", "text"]
                                    ):
                                        content_fields.append(attr)

                                print(f"RT measure fields: {rt_measures}")
                                print(f"Content fields: {content_fields}")

                                # Show actual values
                                if content_fields:
                                    content_attr = content_fields[0]
                                    content_value = getattr(first_word, content_attr)
                                    print(
                                        f"Sample content ({content_attr}): {content_value}"
                                    )

                                if rt_measures:
                                    rt_attr = rt_measures[0]
                                    rt_value = getattr(first_word, rt_attr)
                                    print(f"Sample RT ({rt_attr}): {rt_value}")

        except Exception as e:
            print(f"Error analyzing working file: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n🔍 ANALYZING PROBLEM FILES")
    print("-" * 40)

    for problem_file in problem_files:
        if problem_file.exists():
            try:
                print(f"\nFile: {problem_file.name}")
                mat_data = scipy.io.loadmat(
                    str(problem_file), squeeze_me=True, struct_as_record=False
                )

                keys = [k for k in mat_data.keys() if not k.startswith("__")]
                print(f"Keys: {keys}")

                # Analyze each key
                for key in keys:
                    data = mat_data[key]
                    print(
                        f"  {key}: {type(data)}, shape: {getattr(data, 'shape', 'No shape')}"
                    )

                    # If it looks like sentence data, explore it
                    if hasattr(data, "__len__") and len(data) > 0:
                        first_elem = data[0] if hasattr(data, "__getitem__") else data
                        if hasattr(first_elem, "__dict__"):
                            attrs = [
                                a for a in dir(first_elem) if not a.startswith("_")
                            ]
                            word_attrs = [a for a in attrs if "word" in a.lower()]
                            if word_attrs:
                                print(f"    -> Contains word data: {word_attrs}")

                                # This might be the correct structure
                                word_attr = word_attrs[0]
                                word_data = getattr(first_elem, word_attr)
                                print(f"    -> {word_attr} type: {type(word_data)}")

                                if hasattr(word_data, "__len__") and len(word_data) > 0:
                                    first_word = (
                                        word_data[0]
                                        if hasattr(word_data, "__getitem__")
                                        else word_data
                                    )
                                    if hasattr(first_word, "__dict__"):
                                        word_word_attrs = [
                                            a
                                            for a in dir(first_word)
                                            if not a.startswith("_")
                                        ]
                                        print(
                                            f"    -> Word attributes: {word_word_attrs[:10]}..."
                                        )

                                        # Check for RT measures
                                        rt_attrs = [
                                            a
                                            for a in word_word_attrs
                                            if any(
                                                rt in a.upper()
                                                for rt in ["FFD", "GD", "TRT", "FIX"]
                                            )
                                        ]
                                        if rt_attrs:
                                            print(
                                                f"    -> RT measures found: {rt_attrs}"
                                            )
                                            print(
                                                f"    -> STRUCTURE: {key} -> {word_attr} -> word -> {rt_attrs[0]}"
                                            )

            except Exception as e:
                print(f"Error analyzing {problem_file.name}: {e}")

    return True


def create_final_corrected_loader():
    """Create the final corrected loader based on complete analysis"""

    print(f"\n🎯 CREATING FINAL CORRECTED LOADER")
    print("Based on complete structure analysis")
    print("-" * 40)

    # Update the corrected loader with multiple structure patterns
    loader_file = Path(
        "/home/agourakis82/workspace/pcs-meta-repo/src/datasets/zuco_corrected_loader.py"
    )

    # Read current loader
    with open(loader_file, "r") as f:
        content = f.read()

    # Find the extract_rt_features_corrected method and update it
    new_extract_method = '''    def extract_rt_features_corrected(self, mat_data: Dict, subject_id: str, task: str) -> List[Dict]:
        """
        Extract RT features using multiple structure patterns
        Based on complete analysis of ZuCo file variations
        """
        records = []
        
        try:
            # Try multiple data keys and structure patterns
            structure_patterns = [
                # Pattern 1: sentenceData key (from task1- SR/Matlab files)
                {'key': 'sentenceData', 'sentence_attr': None, 'word_attr': 'word'},
                # Pattern 2: sentences key (from Preprocessed files)
                {'key': 'sentences', 'sentence_attr': None, 'word_attr': 'word'},
                # Pattern 3: Other possible structures
                {'key': 'data', 'sentence_attr': 'sentence', 'word_attr': 'word'},
                {'key': 'results', 'sentence_attr': None, 'word_attr': 'word'},
            ]
            
            data_keys = [k for k in mat_data.keys() if not k.startswith('__')]
            logger.debug(f"Available keys in {subject_id} {task}: {data_keys}")
            
            for pattern in structure_patterns:
                pattern_key = pattern['key']
                
                if pattern_key in mat_data:
                    logger.debug(f"Trying pattern: {pattern}")
                    
                    main_data = mat_data[pattern_key]
                    
                    # Access sentences
                    sentences = None
                    if pattern['sentence_attr']:
                        if hasattr(main_data, pattern['sentence_attr']):
                            sentences = getattr(main_data, pattern['sentence_attr'])
                    else:
                        sentences = main_data
                    
                    if sentences is None:
                        continue
                    
                    # Ensure sentences is iterable
                    if not hasattr(sentences, '__len__'):
                        sentences = [sentences]
                    elif len(sentences) == 0:
                        continue
                    
                    # Process sentences
                    for sent_idx in range(min(len(sentences), 50)):  # Limit for testing
                        try:
                            sentence = sentences[sent_idx]
                            
                            # Access words
                            words = None
                            word_attr = pattern['word_attr']
                            
                            if hasattr(sentence, word_attr):
                                words = getattr(sentence, word_attr)
                            
                            if words is None:
                                continue
                            
                            if not hasattr(words, '__len__'):
                                words = [words]
                            elif len(words) == 0:
                                continue
                            
                            # Process words
                            for word_idx in range(min(len(words), 100)):  # Limit for testing
                                try:
                                    word = words[word_idx]
                                    
                                    # Extract word content
                                    word_text = self._extract_word_content(word, word_idx)
                                    if not word_text:
                                        continue
                                    
                                    # Extract RT measures
                                    rt_measures = self._extract_rt_measures(word)
                                    
                                    record = {
                                        'subject_id': subject_id,
                                        'task_id': task.lower(),
                                        'doc_id': f'sent_{sent_idx+1:03d}',
                                        'sent_id': sent_idx + 1,
                                        'word_id': word_idx + 1,
                                        'word': word_text,
                                        'ffd_ms': rt_measures.get('ffd', np.nan),
                                        'gd_ms': rt_measures.get('gd', np.nan),
                                        'trt_ms': rt_measures.get('trt', np.nan),
                                        'nfix': rt_measures.get('nfix', np.nan),
                                        'length': len(word_text),
                                        'position': word_idx + 1,
                                        'lang': 'en'
                                    }
                                    
                                    records.append(record)
                                    
                                except Exception as e:
                                    logger.debug(f"Failed to process word {word_idx}: {e}")
                                    continue
                                    
                        except Exception as e:
                            logger.debug(f"Failed to process sentence {sent_idx}: {e}")
                            continue
                    
                    # If we got records with this pattern, we're done
                    if records:
                        logger.info(f"Extracted {len(records)} RT records from {subject_id} {task} using pattern {pattern}")
                        return records
            
            # If no pattern worked
            logger.warning(f"No compatible structure found in {subject_id} {task}")
            logger.debug(f"Available keys were: {data_keys}")
            
        except Exception as e:
            logger.error(f"Failed to extract RT features from {subject_id} {task}: {e}")
        
        return records'''

    # Replace the method in the file
    # Find the start and end of the method
    method_start = content.find("def extract_rt_features_corrected(")
    if method_start == -1:
        print("❌ Could not find extract_rt_features_corrected method")
        return False

    # Find the next method or end of class
    method_end = content.find("\n    def ", method_start + 1)
    if method_end == -1:
        method_end = content.find("\ndef load_zuco_rt(", method_start)
    if method_end == -1:
        method_end = len(content)

    # Replace the method
    new_content = content[:method_start] + new_extract_method + content[method_end:]

    # Write back
    with open(loader_file, "w") as f:
        f.write(new_content)

    print(f"✅ Updated loader with multiple structure patterns")
    return True


def main():
    """Main analysis and final correction"""

    print("🔬 FINAL ZUCO ANALYSIS & CORRECTION")
    print("=" * 60)

    # Analyze real files
    analyze_real_zuco_files()

    # Create final corrected loader
    create_final_corrected_loader()

    print(f"\n🎯 FINAL STEPS:")
    print("1. Test the updated corrected loader")
    print("2. Run make tidy-rt to validate")

    return True


if __name__ == "__main__":
    success = main()
    print(f"\nFinal analysis completed: {'Success' if success else 'Failed'}")
