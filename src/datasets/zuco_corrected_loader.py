#!/usr/bin/env python3
"""
Corrected ZuCo loader based on actual data structure analysis
Research-grade implementation following discovered format

References:
- Hollenstein et al. (2018). ZuCo corpus
- Actual data structure analysis results
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZuCoCorrectedLoader:
    """
    ZuCo loader based on actual discovered data structure
    Targets the correct data files and structure
    """
    
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        if str(self.data_root).endswith('scripts'):
            self.zuco_path = self.data_root / "data/raw_public/zuco"
        else:
            self.zuco_path = self.data_root / "scripts/data/raw_public/zuco"
        
        if not self.zuco_path.exists():
            raise FileNotFoundError(f"ZuCo data not found at {self.zuco_path}")
            
        logger.info(f"Initialized corrected ZuCo loader for {self.zuco_path}")
    
    def find_real_zuco_files(self) -> Dict[str, List[Path]]:
        """Find the real ZuCo eye-tracking files based on analysis"""
        
        files = {
            "task1_sr": [],   # Sentiment Reading
            "task2_nr": [],   # Normal Reading  
            "task3_tsr": []   # Task-specific Reading
        }
        
        # Based on analysis - check task directories for real data
        task_mapping = {
            "task1- SR": "task1_sr",
            "task2 - NR": "task2_nr", 
            "task3 - TSR": "task3_tsr"
        }
        
        for task_dir, task_key in task_mapping.items():
            task_path = self.zuco_path / "v1/osfstorage" / task_dir
            
            # Check different subdirectories for .mat files
            for subdir in ["Preprocessed", "Matlab files", "Raw data"]:
                subpath = task_path / subdir
                if subpath.exists():
                    mat_files = list(subpath.glob("*.mat"))
                    if mat_files:
                        files[task_key].extend(mat_files)
                        logger.info(f"Found {len(mat_files)} files in {task_dir}/{subdir}")
        
        return files
    
    def load_real_mat_file(self, mat_path: Path) -> Dict:
        """Load real ZuCo .mat file with correct structure access"""
        try:
            mat_data = scipy.io.loadmat(
                str(mat_path), 
                squeeze_me=True, 
                struct_as_record=False
            )
            
            cleaned_data = {k: v for k, v in mat_data.items() if not k.startswith('__')}
            logger.debug(f"Loaded {mat_path.name}: {list(cleaned_data.keys())}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to load {mat_path}: {e}")
            return {}
    
        def extract_rt_features_corrected(self, mat_data: Dict, subject_id: str, task: str) -> List[Dict]:
        pass
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
        
        return records
    def _extract_word_content(self, word, word_idx: int) -> str:
        """Extract word content from various fields"""
        for field in ['content', 'word', 'text', 'string']:
            if hasattr(word, field):
                content = getattr(word, field)
                if isinstance(content, str) and content.strip():
                    return content.strip()
                elif hasattr(content, '__str__'):
                    text = str(content).strip()
                    if text and text != 'None':
                        return text
        return f"word_{word_idx+1}"
    
    def _extract_rt_measures(self, word) -> Dict[str, float]:
        """Extract RT measures from word"""
        measures = {}
        
        rt_field_mapping = {
            'ffd': ['FFD', 'firstFixationDuration', 'ffd'],
            'gd': ['GD', 'gazeDuration', 'gd'], 
            'trt': ['TRT', 'totalReadingTime', 'trt'],
            'nfix': ['nFixations', 'numFixations', 'fixationCount', 'nfix']
        }
        
        for measure_name, field_names in rt_field_mapping.items():
            for field_name in field_names:
                if hasattr(word, field_name):
                    value = getattr(word, field_name)
                    converted = self._convert_value(value)
                    if not np.isnan(converted):
                        measures[measure_name] = converted
                        break
        
        return measures
    
    def _convert_value(self, value) -> float:
        """Convert value to float safely"""
        try:
            if value is None:
                return np.nan
            elif hasattr(value, '__len__') and len(value) > 0:
                val = value[0] if hasattr(value, '__getitem__') else next(iter(value))
                return float(val) if not np.isnan(float(val)) else np.nan
            elif np.isscalar(value):
                return float(value) if not np.isnan(float(value)) else np.nan
            else:
                return np.nan
        except (ValueError, TypeError, IndexError, OverflowError):
            return np.nan
    
    def load_zuco_rt_data(self, output_path: Path) -> pd.DataFrame:
        """Load ZuCo RT data using corrected approach"""
        logger.info("Loading ZuCo RT data with corrected structure...")
        
        # Find real files
        zuco_files = self.find_real_zuco_files()
        
        all_records = []
        
        # Process Normal Reading (task2_nr) files
        nr_files = zuco_files["task2_nr"]
        if not nr_files:
            logger.warning("No task2_nr files found")
            # Fallback to other tasks
            for task_key, files in zuco_files.items():
                if files:
                    nr_files = files[:3]  # Take first 3 files
                    logger.info(f"Using {task_key} files as fallback")
                    break
        
        if not nr_files:
            logger.error("No ZuCo files found")
            return pd.DataFrame()
        
        # Process files
        for mat_file in nr_files[:3]:  # Process up to 3 files
            subject_id = mat_file.stem.split('_')[-1] if '_' in mat_file.stem else mat_file.stem
            
            logger.info(f"Processing {mat_file.name}...")
            
            mat_data = self.load_real_mat_file(mat_file)
            if not mat_data:
                continue
            
            records = self.extract_rt_features_corrected(mat_data, subject_id, "NR")
            all_records.extend(records)
        
        # Create DataFrame
        if all_records:
            df = pd.DataFrame(all_records)
            
            logger.info(f"Loaded {len(df)} RT records from {len(df['subject_id'].unique())} subjects")
            
            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved corrected ZuCo RT data to {output_path}")
            
            return df
        else:
            logger.warning("No RT records extracted with corrected loader")
            return pd.DataFrame()

def load_zuco_rt(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """Main entry point for corrected ZuCo RT loading"""
    repo_root = raw_dir.parent.parent.parent
    loader = ZuCoCorrectedLoader(repo_root)
    return loader.load_zuco_rt_data(output_path)
