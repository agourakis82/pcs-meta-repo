#!/usr/bin/env python3
"""
Targeted ZuCo data extraction based on discovered structure
Research-grade implementation following actual data format
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_specific_zuco_structure():
    """Analyze the specific ZuCo structure we discovered"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    zuco_path = repo_path / "scripts/data/raw_public/zuco/v1/osfstorage/answers"

    print("🎯 TARGETED ZUCO STRUCTURE ANALYSIS")
    print("Based on discovered keys: answers, nBreaks_all, par")
    print("=" * 60)

    # Get one NR file
    nr_files = list(zuco_path.glob("Fullresults_NR_*.mat"))
    if not nr_files:
        print("❌ No NR files found")
        return

    test_file = nr_files[0]
    print(f"Analyzing: {test_file.name}")

    try:
        # Load with structured loading
        mat_data = scipy.io.loadmat(
            str(test_file), squeeze_me=True, struct_as_record=False
        )

        print(f"\nKeys found: {[k for k in mat_data.keys() if not k.startswith('__')]}")

        # Analyze each key
        for key in ["answers", "nBreaks_all", "par"]:
            if key in mat_data:
                data = mat_data[key]
                print(f"\n{key.upper()}:")
                print(f"  Type: {type(data)}")
                print(f"  Shape: {getattr(data, 'shape', 'No shape')}")
                print(f"  Dtype: {getattr(data, 'dtype', 'No dtype')}")

                if hasattr(data, "__len__"):
                    print(f"  Length: {len(data)}")

                    if len(data) > 0:
                        print(
                            f"  First element: {data[0] if hasattr(data, '__getitem__') else 'No indexing'}"
                        )
                        print(
                            f"  First element type: {type(data[0]) if hasattr(data, '__getitem__') else 'No indexing'}"
                        )

                        # If it's a matrix, show some values
                        if hasattr(data, "shape") and len(data.shape) == 2:
                            print(f"  Sample values (first 3x3):")
                            try:
                                sample = data[
                                    : min(3, data.shape[0]), : min(3, data.shape[1])
                                ]
                                print(f"    {sample}")
                            except:
                                print("    Could not extract sample")

        # Check if this might be task materials data instead of eye-tracking data
        print(f"\n🤔 HYPOTHESIS:")
        print("This might be task answers/responses rather than eye-tracking data")
        print("Let's check other ZuCo data sources...")

        # Check task materials
        task_materials = (
            repo_path / "scripts/data/raw_public/zuco/v1/osfstorage/task_materials"
        )
        if task_materials.exists():
            print(f"\nTask materials directory found: {task_materials}")
            csv_files = list(task_materials.glob("*.csv"))
            print(f"CSV files: {[f.name for f in csv_files]}")

            # Check one CSV file for structure
            if csv_files:
                sample_csv = csv_files[0]
                print(f"\nSample CSV: {sample_csv.name}")
                try:
                    df = pd.read_csv(sample_csv, nrows=3)
                    print(f"Columns: {list(df.columns)}")
                    print("Sample data:")
                    print(df)
                except Exception as e:
                    print(f"Could not read CSV: {e}")

        # Check for preprocessed data
        print(f"\nChecking for preprocessed data...")

        # ZuCo v1 task directories
        for task_dir in ["task1- SR", "task2 - NR", "task3 - TSR"]:
            task_path = (
                repo_path / f"scripts/data/raw_public/zuco/v1/osfstorage/{task_dir}"
            )
            if task_path.exists():
                print(f"\nFound task directory: {task_dir}")

                # Check for different data types
                for subdir in ["Preprocessed", "Raw data", "Matlab files"]:
                    subpath = task_path / subdir
                    if subpath.exists():
                        files = list(subpath.glob("*"))
                        print(f"  {subdir}: {len(files)} files")
                        if files:
                            # Show sample filenames
                            sample_files = [f.name for f in files[:3]]
                            print(f"    Sample: {sample_files}")

                            # If it's a .mat file, check its structure
                            mat_files = [f for f in files if f.suffix == ".mat"]
                            if mat_files:
                                try:
                                    sample_mat = mat_files[0]
                                    print(f"  Checking {sample_mat.name}...")
                                    mat_check = scipy.io.loadmat(
                                        str(sample_mat),
                                        squeeze_me=True,
                                        struct_as_record=False,
                                    )
                                    mat_keys = [
                                        k
                                        for k in mat_check.keys()
                                        if not k.startswith("__")
                                    ]
                                    print(f"    Keys: {mat_keys}")

                                    # Check for sentence/word structures
                                    for key in mat_keys:
                                        data_check = mat_check[key]
                                        if (
                                            hasattr(data_check, "__len__")
                                            and len(data_check) > 0
                                        ):
                                            first_elem = (
                                                data_check[0]
                                                if hasattr(data_check, "__getitem__")
                                                else data_check
                                            )
                                            if hasattr(first_elem, "__dict__"):
                                                attrs = [
                                                    a
                                                    for a in dir(first_elem)
                                                    if not a.startswith("_")
                                                    and "sentence" in a.lower()
                                                    or "word" in a.lower()
                                                ]
                                                if attrs:
                                                    print(
                                                        f"    -> Found sentence/word attrs in {key}: {attrs}"
                                                    )

                                                    # This might be the real eye-tracking data!
                                                    print(
                                                        f"    -> POTENTIAL EYE-TRACKING DATA FOUND!"
                                                    )
                                                    return sample_mat, key, attrs

                                except Exception as e:
                                    print(f"    Error checking {sample_mat.name}: {e}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback

        traceback.print_exc()

    return None, None, None


def create_corrected_zuco_loader(data_file_info):
    """Create corrected ZuCo loader based on findings"""

    if data_file_info[0] is None:
        print("\n❌ No eye-tracking data structure found")
        return

    data_file, data_key, data_attrs = data_file_info

    print(f"\n🎯 CREATING CORRECTED LOADER")
    print(f"Based on: {data_file.name}, key: {data_key}, attrs: {data_attrs}")

    corrected_loader_code = f'''#!/usr/bin/env python3
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
            raise FileNotFoundError(f"ZuCo data not found at {{self.zuco_path}}")
            
        logger.info(f"Initialized corrected ZuCo loader for {{self.zuco_path}}")
    
    def find_real_zuco_files(self) -> Dict[str, List[Path]]:
        """Find the real ZuCo eye-tracking files based on analysis"""
        
        files = {{
            "task1_sr": [],   # Sentiment Reading
            "task2_nr": [],   # Normal Reading  
            "task3_tsr": []   # Task-specific Reading
        }}
        
        # Based on analysis - check task directories for real data
        task_mapping = {{
            "task1- SR": "task1_sr",
            "task2 - NR": "task2_nr", 
            "task3 - TSR": "task3_tsr"
        }}
        
        for task_dir, task_key in task_mapping.items():
            task_path = self.zuco_path / "v1/osfstorage" / task_dir
            
            # Check different subdirectories for .mat files
            for subdir in ["Preprocessed", "Matlab files", "Raw data"]:
                subpath = task_path / subdir
                if subpath.exists():
                    mat_files = list(subpath.glob("*.mat"))
                    if mat_files:
                        files[task_key].extend(mat_files)
                        logger.info(f"Found {{len(mat_files)}} files in {{task_dir}}/{{subdir}}")
        
        return files
    
    def load_real_mat_file(self, mat_path: Path) -> Dict:
        """Load real ZuCo .mat file with correct structure access"""
        try:
            mat_data = scipy.io.loadmat(
                str(mat_path), 
                squeeze_me=True, 
                struct_as_record=False
            )
            
            cleaned_data = {{k: v for k, v in mat_data.items() if not k.startswith('__')}}
            logger.debug(f"Loaded {{mat_path.name}}: {{list(cleaned_data.keys())}}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to load {{mat_path}}: {{e}}")
            return {{}}
    
    def extract_rt_features_corrected(self, mat_data: Dict, subject_id: str, task: str) -> List[Dict]:
        """
        Extract RT features using corrected structure access
        Based on analysis findings: key='{data_key}', attrs={data_attrs}
        """
        records = []
        
        try:
            # Use the discovered data key
            if '{data_key}' not in mat_data:
                logger.warning(f"Key '{data_key}' not found in {{subject_id}} {{task}}")
                return records
            
            main_data = mat_data['{data_key}']
            logger.debug(f"Processing {{subject_id}} {{task}}: main_data type = {{type(main_data)}}")
            
            # Access structure based on discovered attributes
            sentences = None
            
            # Try the discovered sentence attributes
            for attr in {data_attrs}:
                if hasattr(main_data, attr):
                    sentences = getattr(main_data, attr)
                    logger.debug(f"Found sentences via {{attr}}")
                    break
            
            if sentences is None and hasattr(main_data, '__len__') and len(main_data) > 0:
                # Try accessing first element
                first_elem = main_data[0]
                for attr in {data_attrs}:
                    if hasattr(first_elem, attr):
                        sentences = getattr(first_elem, attr)
                        logger.debug(f"Found sentences via first_elem.{{attr}}")
                        break
            
            if sentences is None:
                logger.warning(f"No sentence structure found in {{subject_id}} {{task}}")
                return records
            
            # Ensure sentences is iterable
            if not hasattr(sentences, '__len__'):
                sentences = [sentences]
            
            # Process sentences and extract word-level data
            for sent_idx in range(len(sentences)):
                try:
                    sentence = sentences[sent_idx]
                    
                    # Look for word data
                    words = None
                    for word_attr in ['word', 'words', 'wordData']:
                        if hasattr(sentence, word_attr):
                            words = getattr(sentence, word_attr)
                            break
                    
                    if words is None:
                        continue
                    
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
                            
                            # Extract RT measures
                            rt_measures = self._extract_rt_measures(word)
                            
                            record = {{
                                'subject_id': subject_id,
                                'task_id': task.lower(),
                                'doc_id': f'sent_{{sent_idx+1:03d}}',
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
                            }}
                            
                            records.append(record)
                            
                        except Exception as e:
                            logger.debug(f"Failed to process word {{word_idx}}: {{e}}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Failed to process sentence {{sent_idx}}: {{e}}")
                    continue
            
            if records:
                logger.info(f"Extracted {{len(records)}} RT records from {{subject_id}} {{task}}")
            
        except Exception as e:
            logger.error(f"Failed to extract RT features from {{subject_id}} {{task}}: {{e}}")
        
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
        return f"word_{{word_idx+1}}"
    
    def _extract_rt_measures(self, word) -> Dict[str, float]:
        """Extract RT measures from word"""
        measures = {{}}
        
        rt_field_mapping = {{
            'ffd': ['FFD', 'firstFixationDuration', 'ffd'],
            'gd': ['GD', 'gazeDuration', 'gd'], 
            'trt': ['TRT', 'totalReadingTime', 'trt'],
            'nfix': ['nFixations', 'numFixations', 'fixationCount', 'nfix']
        }}
        
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
                    logger.info(f"Using {{task_key}} files as fallback")
                    break
        
        if not nr_files:
            logger.error("No ZuCo files found")
            return pd.DataFrame()
        
        # Process files
        for mat_file in nr_files[:3]:  # Process up to 3 files
            subject_id = mat_file.stem.split('_')[-1] if '_' in mat_file.stem else mat_file.stem
            
            logger.info(f"Processing {{mat_file.name}}...")
            
            mat_data = self.load_real_mat_file(mat_file)
            if not mat_data:
                continue
            
            records = self.extract_rt_features_corrected(mat_data, subject_id, "NR")
            all_records.extend(records)
        
        # Create DataFrame
        if all_records:
            df = pd.DataFrame(all_records)
            
            logger.info(f"Loaded {{len(df)}} RT records from {{len(df['subject_id'].unique())}} subjects")
            
            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved corrected ZuCo RT data to {{output_path}}")
            
            return df
        else:
            logger.warning("No RT records extracted with corrected loader")
            return pd.DataFrame()

def load_zuco_rt(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """Main entry point for corrected ZuCo RT loading"""
    repo_root = raw_dir.parent.parent.parent
    loader = ZuCoCorrectedLoader(repo_root)
    return loader.load_zuco_rt_data(output_path)
'''

    # Write the corrected loader
    corrected_loader_file = Path(
        "/home/agourakis82/workspace/pcs-meta-repo/src/datasets/zuco_corrected_loader.py"
    )
    with open(corrected_loader_file, "w") as f:
        f.write(corrected_loader_code)

    print(f"✅ Created corrected loader: {corrected_loader_file}")
    return corrected_loader_file


def main():
    """Main analysis and correction"""

    print("🔬 TARGETED ZUCO ANALYSIS & CORRECTION")
    print("=" * 60)

    # Analyze structure
    data_info = analyze_specific_zuco_structure()

    # Create corrected loader
    corrected_loader = create_corrected_zuco_loader(data_info)

    if corrected_loader:
        print(f"\n🎯 NEXT STEPS:")
        print("1. Test the corrected loader")
        print("2. Update pipeline to use corrected loader")
        print("3. Validate with real data")

        return True
    else:
        print(f"\n⚠️  Could not create corrected loader")
        print("Manual investigation needed")
        return False


if __name__ == "__main__":
    success = main()
    print(f"\nAnalysis completed: {'Success' if success else 'Needs manual review'}")
