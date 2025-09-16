# Relatório Multilíngue — Modelos RT/EEG

Data: gerado automaticamente

## RT/ET — Correlações Spearman (com FDR)

Total de testes: 9
Significativos (q≤0.05): 3

Top 5 efeitos:
- geco_et_kec_rt.parquet: timestamp ~ coherence r=-0.270, p=0.0, q=2.9999999999999996e-300, n=348333
- geco_et_kec_rt.parquet: timestamp ~ curvature r=-0.082, p=2.906185081015226e-212, q=2.9999999999999996e-300, n=144062
- geco_et_kec_rt.parquet: timestamp ~ entropy r=-0.058, p=2.1997434341757544e-107, q=2.9999999999999996e-300, n=144062

## EEG — Correlações Spearman (com FDR)

Total de testes: 12
Significativos (q≤0.05): 0

## Modelos Mistos (ZuCo/GECO)

Total de estimativas: 9
Significativos por DV (q≤0.05): 3

Top 5 efeitos (|coef|):
- zuco:trt_ms ~ curvature coef=-577.391, p=0.942, q_dv=1.0, n=415
- zuco:trt_ms ~ coherence coef=-56.999, p=0.412, q_dv=1.0, n=509
- geco_et:gaze_ms ~ coherence coef=-6.139, p=1, q_dv=1.4999999999999998e-300, n=71951
- zuco:nfix ~ curvature coef=-4.508, p=0.934, q_dv=1.0, n=415
- zuco:trt_ms ~ entropy coef=-3.360, p=0.984, q_dv=0.9836238350931849, n=415

## Visualizações
- multilingual_comparison.png
- multilingual_pca.png
