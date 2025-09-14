# Dataset Processing Instructions
# Research-grade data processing based on official documentation

## ZuCo Corpus Processing

### Official Source
- OSF Repository: https://osf.io/2urht/
- Paper: Hollenstein et al. (2018). ZuCo, a simultaneous EEG and eye-tracking corpus

### Data Structure (from official utils_ZuCo.py):

### Official Python Functions:
- def get_matfiles(task:str, subdir = '\\results_zuco\\'):
- def __init__(self, task:str, level:str, scaling='min-max', fillna='zeros'):
- def __call__(self, subject:int):
- def check_inf(features):
- def split_data(sbjs):

### Data Structure Hints:
- levels = ['sentence', 'word']
- raise Exception('Data can only be processed on sentence or word level')
- Return: DataFrame with normalized features (i.e., attributes) on sentence or word level
- data = io.loadmat(files[subject], squeeze_me=True, struct_as_record=False)['sentenceData']
- if self.level == 'sentence':
- fields = ['SentLen',  'omissionRate', 'nFixations', 'meanPupilSize', 'GD', 'TRT',
- 'FFD', 'SFD', 'GPT']
- elif self.level == 'word':
- n_words = sum([len(sent.word) for i, sent in enumerate(data[:-1]) if i < 150 or i > 249])
- n_words = sum([len(sent.word) for i, sent in enumerate(data) if i > 49])

### Processing Notes:
- Use official utils_ZuCo.py as reference
- Data stored in .mat files with MATLAB struct format
- Word-level measures: FFD, GD, TRT, nFixations
- Sentence-level organization with nested word structures

## GECO Corpus Processing

### Official Source
- URL: http://expsy.ugent.be/downloads/geco/
- Paper: Cop et al. (2017). Presenting GECO

### Data Format:
- Tab-separated values (.tsv)
- Word-level eye-tracking measures
- Standard RT measures: FFD, SFD, GD, TRT

### Processing Notes:
- Bilingual (English/Dutch) and monolingual data
- Established eye-tracking measure definitions
- CSV/TSV format with headers

## OneStop Corpus Processing

### Source
- Reading comprehension corpus with eye-tracking
- Multi-level text complexity

### Processing Notes:
- Focus on comprehension-related measures
- Variable data formats (check local files)
- May require custom parsing logic

## Implementation Strategy

### 1. ZuCo Loader Priority
- Study official utils_ZuCo.py implementation
- Mirror official data access patterns
- Handle MATLAB struct hierarchy correctly

### 2. Validation Approach
- Compare extracted data with known benchmarks
- Validate RT measure distributions
- Cross-reference with published statistics

### 3. Error Handling
- Robust parsing for different ZuCo versions
- Graceful handling of missing measures
- Data quality validation

### 4. Research Standards
- Document all processing decisions
- Maintain traceability to source data
- Include uncertainty quantification
