#!/usr/bin/env python3
"""
Working ZuCo loader based on complete structure analysis
Research-grade implementation following discovered format

Structure discovered:
- File: resultsZJM_SR.mat 
- Key: sentenceData (400 sentences)
- Path: sentenceData -> word -> FFD/GD/TRT/nFixations/content
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZuCoWorkingLoader:
    """
    ZuCo loader based on actual discovered data structure
    """
    
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        if str(self.data_root).endswith('scripts'):
            self.zuco_path = self.data_root / "data/raw_public/zuco"
        else:
            self.zuco_path = self.data_root / "scripts/data/raw_public/zuco"
        
        if not self.zuco_path.exists():
            raise FileNotFoundError(f"ZuCo data not found at {self.zuco_path}")
            
        logger.info(f"Initialized working ZuCo loader for {self.zuco_path}")
    
    def find_zuco_files(self) -> List[Path]:
        """Find ZuCo files with the working structure"""
        
        files = []
        
        # Look in task directories for Matlab files
        task_dirs = ["task1- SR", "task2 - NR", "task3 - TSR"]
        
        for task_dir in task_dirs:
            matlab_dir = self.zuco_path / "v1/osfstorage" / task_dir / "Matlab files"
            if matlab_dir.exists():
                mat_files = list(matlab_dir.glob("results*.mat"))
                files.extend(mat_files)
                logger.info(f"Found {len(mat_files)} files in {task_dir}/Matlab files")
        
        return files[:5]  # Limit to first 5 files for testing
    
    def load_mat_file(self, mat_path: Path) -> Dict:
        """Load .mat file with discovered structure"""
        try:
            mat_data = scipy.io.loadmat(
                str(mat_path), 
                squeeze_me=True, 
                struct_as_record=False
            )
            
            cleaned_data = {k: v for k, v in mat_data.items() if not k.startswith('__')}
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to load {mat_path}: {e}")
            return {}
    
    def extract_rt_features(self, mat_data: Dict, subject_id: str, task: str) -> List[Dict]:
        """
        Extract RT features using discovered structure
        sentenceData -> word -> FFD/GD/TRT/nFixations/content
        """
        records = []
        
        try:
            if 'sentenceData' not in mat_data:
                logger.warning(f"No sentenceData in {subject_id} {task}")
                return records
            
            sentence_data = mat_data['sentenceData']
            logger.debug(f"Processing {subject_id} {task}: {len(sentence_data)} sentences")
            
            # Process sentences (limit for testing)
            for sent_idx in range(min(len(sentence_data), 10)):
                try:
                    sentence = sentence_data[sent_idx]
                    
                    if not hasattr(sentence, 'word'):
                        continue
                    
                    words = sentence.word
                    if not hasattr(words, '__len__'):
                        words = [words]
                    
                    # Process words (limit for testing)
                    for word_idx in range(min(len(words), 20)):
                        try:
                            word = words[word_idx]
                            
                            # Extract word content
                            word_text = "unknown"
                            if hasattr(word, 'content'):
                                content = word.content
                                if isinstance(content, str):
                                    word_text = content.strip()
                                elif hasattr(content, '__str__'):
                                    word_text = str(content).strip()
                            
                            if not word_text or word_text == "unknown":
                                word_text = f"word_{word_idx+1}"
                            
                            # Extract RT measures using discovered fields
                            ffd = self._safe_extract(word, 'FFD')
                            gd = self._safe_extract(word, 'GD') 
                            trt = self._safe_extract(word, 'TRT')
                            nfix = self._safe_extract(word, 'nFixations')
                            
                            record = {
                                'subject_id': subject_id,
                                'task_id': task.lower(),
                                'doc_id': f'sent_{sent_idx+1:03d}',
                                'sent_id': sent_idx + 1,
                                'word_id': word_idx + 1,
                                'word': word_text,
                                'ffd_ms': ffd,
                                'gd_ms': gd,
                                'trt_ms': trt,
                                'nfix': nfix,
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
            
            logger.info(f"Extracted {len(records)} RT records from {subject_id} {task}")
            
        except Exception as e:
            logger.error(f"Failed to extract RT features from {subject_id} {task}: {e}")
        
        return records
    
    def _safe_extract(self, word, field_name: str) -> float:
        """Safely extract and convert RT measure"""
        try:
            if hasattr(word, field_name):
                value = getattr(word, field_name)
                
                # Handle different value types
                if isinstance(value, (int, float)):
                    return float(value) if not np.isnan(value) else np.nan
                elif hasattr(value, '__len__') and len(value) > 0:
                    # Array-like, take first element
                    val = value[0] if hasattr(value, '__getitem__') else next(iter(value))
                    return float(val) if not np.isnan(float(val)) else np.nan
                else:
                    return np.nan
            else:
                return np.nan
        except (ValueError, TypeError, IndexError, OverflowError):
            return np.nan
    
    def load_zuco_rt_data(self, output_path: Path) -> pd.DataFrame:
        """Load ZuCo RT data using working structure"""
        logger.info("Loading ZuCo RT data with working structure...")
        
        # Find files
        zuco_files = self.find_zuco_files()
        
        if not zuco_files:
            logger.error("No ZuCo files found")
            return pd.DataFrame()
        
        all_records = []
        
        # Process files
        for mat_file in zuco_files:
            # Extract subject ID from filename
            subject_id = mat_file.stem.split('_')[-1] if '_' in mat_file.stem else mat_file.stem
            
            logger.info(f"Processing {mat_file.name}...")
            
            mat_data = self.load_mat_file(mat_file)
            if not mat_data:
                continue
            
            records = self.extract_rt_features(mat_data, subject_id, "ZuCo")
            all_records.extend(records)
        
        # Create DataFrame
        if all_records:
            df = pd.DataFrame(all_records)
            
            logger.info(f"Loaded {len(df)} RT records from {len(df['subject_id'].unique())} subjects")
            
            # Show RT measure statistics
            for measure in ['ffd_ms', 'gd_ms', 'trt_ms', 'nfix']:
                valid_count = df[measure].notna().sum()
                percentage = valid_count / len(df) * 100
                logger.info(f"Valid {measure}: {valid_count}/{len(df)} ({percentage:.1f}%)")
            
            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved working ZuCo RT data to {output_path}")
            
            return df
        else:
            logger.warning("No RT records extracted with working loader")
            return pd.DataFrame()

def load_zuco_rt(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """Main entry point for working ZuCo RT loading"""
    repo_root = raw_dir.parent.parent.parent
    loader = ZuCoWorkingLoader(repo_root)
    return loader.load_zuco_rt_data(output_path)

if __name__ == "__main__":
    # Test the working loader
    repo_root = Path("/home/agourakis82/workspace/pcs-meta-repo")
    output_file = repo_root / "data/L1_tidy/zuco_rt/word_events_rt.parquet"
    
    df = load_zuco_rt(repo_root / "scripts/data/raw_public/zuco", output_file)
    print(f"Loaded {len(df)} RT records")
    if len(df) > 0:
        print(df.head())
