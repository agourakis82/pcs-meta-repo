LPP (Le Petit Prince) Study Notes
=================================

This document summarizes participant demographics, experimental procedure, stimuli, acquisition, and preprocessing details for the LPP EEG/fMRI dataset used in DX-CODEX (OpenNeuro ds005345).

Participants
------------
- 25 native Mandarin Chinese speakers (14 females, mean age = 24.04 ± 2.28) participated in both EEG and fMRI experiments.
- All right-handed, no reported neurological disorders; undergraduate/graduate students in Shanghai.
- Informed consent obtained; ethics approval: SH9H-2019-T33-2 and SH9H-2022-T379-2 (Ninth People's Hospital, Shanghai Jiao Tong University School of Medicine).
- French cohort had shorter sessions due to legal constraints.

Experiment Procedure
--------------------
- Task: listening to the Chinese version of Le Petit Prince under different talker conditions (single male, single female, mixed male/female), attending to the designated talker in multitalker runs.
- fMRI session lasted ~70 minutes, comprising 4 conditions; comprehension quizzes administered after each run.
- French sessions adjusted for legal time limits.

Stimuli
-------
- Audio clips from the Chinese version of Le Petit Prince (http://www.xiaowangzi.org/).
- Previously used in EEG (Li et al., 2024) and fMRI (Li et al., 2022) studies.
- English/Chinese versions enhanced with visuals; French version presented without visuals to comply with legal restrictions.

Acquisition
-----------
- EEG: 64-channel actiCAP, 500 Hz sampling, band-pass 0.016–80 Hz.
- fMRI (7T Siemens Terra):
  - Functional MRI: 85 interleaved axial slices, 1.6×1.6×1.6 mm voxel size, TR = 1000 ms, TE = 22.2 ms.
  - Anatomical MRI: MP-RAGE, 0.7×0.7×0.7 mm voxel size.

Preprocessing (MRI)
-------------------
1. DICOM→NIfTI via dcm2niix (v1.0.20220505) and fMRIPrep 20.2.0.
2. Anatomical: skull stripping; GM/WM/CSF segmentation; registration to MNI152NLin2009cAsym:res-2.
3. Functional: motion correction, slice-timing correction, multi-echo ICA denoising; resampling to native and MNI spaces.

Note: visual stimuli in English/Chinese handled separately from French to avoid bias.

