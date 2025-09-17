# Externalização de Dados Grandes (v5.0)

Os arquivos CSV SWOW e pesos de modelo >100MB foram removidos do histórico git para cumprir limites do GitHub.

Mover para armazenamento externo (Zenodo / Hugging Face / GCS) antes da release formal:
- data/en/raw/SWOW-EN.complete.20180827.csv
- data/en/raw/SWOW-EN.R100.20180827.csv
- data/es/raw/SWOWRP.raw.20220426.csv
- data/es/raw/SWOWRP.spellchecked.20220426.csv
- data/es/raw/SWOWRP.R70.20220426.csv
- models/mistral-7b/model-00001-of-00002.safetensors

Próximos passos:
1. Publicar datasets no Zenodo (ou conjunto DOI existente) com checksum.
2. Adicionar script de download (ex: scripts/fetch_large_data.sh) validando hash.
3. Atualizar README com seção 'Obtendo Dados Grandes'.
