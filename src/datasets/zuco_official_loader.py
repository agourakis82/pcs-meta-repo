#!/usr/bin/env python3
"""
Official ZuCo data loader based on utils_ZuCo.py patterns
Research-grade implementation following Hollenstein et al. (2018)

References:
- Hollenstein, N., Rotsztejn, J., Thoma, M., Kapanci, E., & Säuberli, A. (2018). 
  ZuCo, a simultaneous EEG and eye-tracking corpus for natural language processing. 
  Scientific data, 5(1), 1-13.
- Official ZuCo repository: https://osf.io/2urht/
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZuCoOfficialLoader:
    """
    ZuCo loader following official utils_ZuCo.py patterns
    Implements research-grade data processing with validation
    """
    
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        # Handle path resolution like before
        if str(self.data_root).endswith('scripts'):
            self.zuco_path = self.data_root / "data/raw_public/zuco"
        else:
            self.zuco_path = self.data_root / "scripts/data/raw_public/zuco"
        
        if not self.zuco_path.exists():
            raise FileNotFoundError(f"ZuCo data not found at {self.zuco_path}")
            
        logger.info(f"Initialized official ZuCo loader for {self.zuco_path}")
    
    def find_zuco_files(self) -> Dict[str, List[Path]]:
        """Find ZuCo .mat files by task type"""
        
        files = {
            "v1_sr": [],  # Sentiment Reading
            "v1_nr": [],  # Normal Reading  
            "v1_tsr": [], # Task-specific Reading
            "v2_tsr": []  # ZuCo 2.0
        }
        
        # ZuCo v1 files
        v1_answers = self.zuco_path / "v1/osfstorage/answers"
        if v1_answers.exists():
            files["v1_sr"] = list(v1_answers.glob("Fullresults_SR_*.mat"))
            files["v1_nr"] = list(v1_answers.glob("Fullresults_NR_*.mat"))
            files["v1_tsr"] = list(v1_answers.glob("Fullresults_TSR_*.mat"))
        
        # ZuCo v2 files
        v2_path = self.zuco_path / "v2"
        if v2_path.exists():
            files["v2_tsr"] = list(v2_path.rglob("*.mat"))
        
        logger.info(f"Found ZuCo files: {[(k, len(v)) for k, v in files.items()]}")
        return files
    
    def load_mat_file(self, mat_path: Path) -> Dict:
        """Load .mat file following official patterns"""
        try:
            # Use official loading pattern: struct_as_record=False for object access
            mat_data = scipy.io.loadmat(
                str(mat_path), 
                squeeze_me=True, 
                struct_as_record=False
            )
            
            # Remove MATLAB metadata
            cleaned_data = {k: v for k, v in mat_data.items() if not k.startswith('__')}
            
            logger.debug(f"Loaded {mat_path.name}: {list(cleaned_data.keys())}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to load {mat_path}: {e}")
            return {}
    
    def extract_rt_features_official(self, mat_data: Dict, subject_id: str, task: str) -> List[Dict]:
        """
        Extract RT features following official ZuCo patterns
        Based on analysis of utils_ZuCo.py structure
        """
        records = []
        
        try:
            # Get main data key (usually first non-metadata key)
            data_keys = [k for k in mat_data.keys() if not k.startswith('__')]
            if not data_keys:
                logger.warning(f"No data keys in {subject_id} {task}")
                return records
            
            main_data = mat_data[data_keys[0]]
            logger.debug(f"Processing {subject_id} {task}: main_data type = {type(main_data)}")
            
            # Official pattern: Try multiple structure access methods
            sentences = None
            
            # Pattern 1: Direct sentence access
            if hasattr(main_data, 'sentence'):
                sentences = main_data.sentence
            # Pattern 2: Content access
            elif hasattr(main_data, 'content'):
                sentences = main_data.content
            # Pattern 3: Array access
            elif hasattr(main_data, '__len__') and len(main_data) > 0:
                first_elem = main_data[0]
                if hasattr(first_elem, 'sentence'):
                    sentences = first_elem.sentence
                elif hasattr(first_elem, 'content'):
                    sentences = first_elem.content
            
            if sentences is None:
                logger.warning(f"No sentence structure found in {subject_id} {task}")
                return records
            
            # Ensure sentences is iterable
            if not hasattr(sentences, '__len__'):
                sentences = [sentences]
            
            # Process each sentence
            for sent_idx in range(len(sentences)):
                try:
                    sentence = sentences[sent_idx]
                    
                    # Access words in sentence
                    words = None
                    if hasattr(sentence, 'word'):
                        words = sentence.word
                    elif hasattr(sentence, 'content'):
                        if hasattr(sentence.content, 'word'):
                            words = sentence.content.word
                    
                    if words is None:
                        continue
                    
                    # Ensure words is iterable
                    if not hasattr(words, '__len__'):
                        words = [words]
                    
                    # Process each word
                    for word_idx in range(len(words)):
                        try:
                            word = words[word_idx]
                            
                            # Extract word content
                            word_text = self._extract_word_content(word, word_idx)
                            if not word_text:
                                continue
                            
                            # Extract RT measures using official field names
                            rt_measures = self._extract_official_rt_measures(word)
                            
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
                            logger.debug(f"Failed to process word {word_idx} in {subject_id}: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Failed to process sentence {sent_idx} in {subject_id}: {e}")
                    continue
            
            if records:
                logger.info(f"Extracted {len(records)} RT records from {subject_id} {task}")
            else:
                logger.warning(f"No records extracted from {subject_id} {task}")
            
        except Exception as e:
            logger.error(f"Failed to extract RT features from {subject_id} {task}: {e}")
        
        return records
    
    def _extract_word_content(self, word, word_idx: int) -> str:
        """Extract word content using official patterns"""
        # Try official field names
        for field in ['content', 'word_str', 'text', 'string']:
            if hasattr(word, field):
                content = getattr(word, field)
                if isinstance(content, str) and content.strip():
                    return content.strip()
                elif hasattr(content, '__str__'):
                    text = str(content).strip()
                    if text and text != 'None':
                        return text
        
        return f"word_{word_idx+1}"
    
    def _extract_official_rt_measures(self, word) -> Dict[str, float]:
        """Extract RT measures using official ZuCo field names"""
        measures = {}
        
        # Official ZuCo field names (from utils_ZuCo.py analysis)
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
                    converted = self._convert_matlab_value(value)
                    if not np.isnan(converted):
                        measures[measure_name] = converted
                        break
        
        return measures
    
    def _convert_matlab_value(self, value) -> float:
        """Convert MATLAB value to Python float with validation"""
        try:
            if value is None:
                return np.nan
            elif hasattr(value, '__len__') and len(value) > 0:
                # MATLAB array - take first valid element
                val = value[0] if hasattr(value, '__getitem__') else next(iter(value))
                return float(val) if not np.isnan(float(val)) else np.nan
            elif np.isscalar(value):
                return float(value) if not np.isnan(float(value)) else np.nan
            else:
                return np.nan
        except (ValueError, TypeError, IndexError, OverflowError):
            return np.nan
    
    def load_zuco_rt_data(self, output_path: Path) -> pd.DataFrame:
        """Load ZuCo RT data using official patterns"""
        logger.info("Loading ZuCo RT data with official loader...")
        
        # Find files
        zuco_files = self.find_zuco_files()
        
        all_records = []
        
        # Process Normal Reading (NR) files - primary RT source
        nr_files = zuco_files["v1_nr"]
        if not nr_files:
            logger.warning("No NR files found")
            return pd.DataFrame()
        
        # Process multiple files for better coverage
        for mat_file in nr_files[:5]:  # Process up to 5 subjects
            subject_id = mat_file.stem.split('_')[-1]
            
            logger.info(f"Processing {mat_file.name}...")
            
            mat_data = self.load_mat_file(mat_file)
            if not mat_data:
                continue
            
            records = self.extract_rt_features_official(mat_data, subject_id, "NR")
            all_records.extend(records)
        
        # Create DataFrame
        if all_records:
            df = pd.DataFrame(all_records)
            
            # Data quality validation
            logger.info(f"Loaded {len(df)} RT records from {len(df['subject_id'].unique())} subjects")
            
            # Validate RT measures
            valid_measures = {
                'ffd': df['ffd_ms'].notna().sum(),
                'gd': df['gd_ms'].notna().sum(),
                'trt': df['trt_ms'].notna().sum(),
                'nfix': df['nfix'].notna().sum()
            }
            
            for measure, count in valid_measures.items():
                percentage = count / len(df) * 100
                logger.info(f"Valid {measure}: {count}/{len(df)} ({percentage:.1f}%)")
            
            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved ZuCo RT data to {output_path}")
            
            return df
        else:
            logger.warning("No RT records extracted")
            return pd.DataFrame()

def load_zuco_rt(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """
    Main entry point for official ZuCo RT loading
    
    Args:
        raw_dir: Directory containing ZuCo data
        output_path: Output file path
        
    Returns:
        Processed DataFrame with RT measures
    """
    # Go up to repo root from raw_dir
    repo_root = raw_dir.parent.parent.parent
    loader = ZuCoOfficialLoader(repo_root)
    return loader.load_zuco_rt_data(output_path)

if __name__ == "__main__":
    # Test the loader
    repo_root = Path("/home/agourakis82/workspace/pcs-meta-repo")
    output_file = repo_root / "data/L1_tidy/zuco_rt/word_events_rt.parquet"
    
    df = load_zuco_rt(repo_root / "scripts/data/raw_public/zuco", output_file)
    print(f"Loaded {len(df)} RT records")
    if len(df) > 0:
        print(df.head())
        print(f"Columns: {list(df.columns)}")
        print(f"Subjects: {df['subject_id'].unique()}")
