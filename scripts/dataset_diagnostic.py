#!/usr/bin/env python3
"""
Diagnóstico Abrangente dos Datasets EEG/RT
Verifica status e localização de todos os datasets: ZuCo v1/v2, DERCo, GECO, LPP, OneStop
"""

from pathlib import Path
from datetime import datetime
import pandas as pd


class DatasetDiagnostic:
    """Comprehensive diagnostic for EEG/RT datasets"""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.datasets = {
            "ZuCo_v1": {
                "name": "ZuCo v1 (Task 1-2-3)",
                "expected_path": "data/raw_public/zuco/v1",
                "files": ["task1-SR", "task2-NR", "task3-TSR"],
                "source": "https://osf.io/2urht/",
                "description": "EEG durante leitura de sentenças",
            },
            "ZuCo_v2": {
                "name": "ZuCo v2 (Task 2)",
                "expected_path": "data/raw_public/zuco/v2",
                "files": ["task2-TSR"],
                "source": "https://osf.io/q3zws/",
                "description": "EEG durante leitura de texto natural",
            },
            "DERCo": {
                "name": "DERCo (Dutch Reading Corpus)",
                "expected_path": "data/raw_public/derco",
                "files": ["eeg", "et"],
                "source": "https://osf.io/8c7a6/",
                "description": "Corpus holandês com EEG e eye-tracking",
            },
            "GECO": {
                "name": "GECO (Groningen Eyetracking Corpus)",
                "expected_path": "data/raw_public/geco",
                "files": ["et", "behavioral"],
                "source": "https://osf.io/9y4za/",
                "description": "Corpus holandês com eye-tracking",
            },
            "LPP": {
                "name": "LPP (Le Petit Prince)",
                "expected_path": "data/raw_public/lpp",
                "files": ["eeg", "fmri", "stimuli"],
                "source": "https://openneuro.org/datasets/ds005345",
                "description": "EEG/fMRI durante audição de história",
            },
            "OneStop": {
                "name": "OneStop (English Reading Corpus)",
                "expected_path": "data/raw_public/onestop",
                "files": ["et", "behavioral"],
                "source": "https://osf.io/8c7a6/",
                "description": "Corpus inglês com eye-tracking",
            },
        }

        self.processed_datasets = {
            "integrated_neuro_swow": "data/processed/integrated_neuro_swow.csv",
            "zuco_aligned": "data/processed/zuco_aligned_real_et_eeg.csv",
            "zuco_word_level": "data/processed/zuco_word_level_all_subjects_real_et_eeg.csv",
        }

    def run_full_diagnostic(self):
        """Run comprehensive diagnostic of all datasets"""
        print("🔍 DIAGNÓSTICO ABRANGENTE DOS DATASETS EEG/RT")
        print("=" * 70)

        self.check_raw_datasets()
        self.check_processed_datasets()
        self.check_configuration_files()
        self.generate_diagnostic_report()

    def check_raw_datasets(self):
        """Check status of raw datasets"""
        print("\n📁 VERIFICAÇÃO DOS DATASETS BRUTOS:")
        print("-" * 50)

        for dataset_id, info in self.datasets.items():
            print(f"\n🔍 {info['name']}")
            print(f"   Descrição: {info['description']}")
            print(f"   Fonte: {info['source']}")

            expected_path = self.base_path / info["expected_path"]
            if expected_path.exists():
                print(f"   ✅ Diretório encontrado: {expected_path}")

                # Verificar conteúdo
                try:
                    contents = list(expected_path.rglob("*"))
                    files_count = len([f for f in contents if f.is_file()])
                    dirs_count = len([f for f in contents if f.is_dir()])

                    print(
                        f"   📊 Conteúdo: {files_count} arquivos, {dirs_count} pastas"
                    )

                    # Verificar arquivos específicos
                    for file_type in info["files"]:
                        matching_files = [
                            f for f in contents if file_type.lower() in f.name.lower()
                        ]
                        if matching_files:
                            print(
                                f"   📁 {file_type}: {len(matching_files)} arquivos encontrados"
                            )
                        else:
                            print(f"   ⚠️  {file_type}: Nenhum arquivo encontrado")

                except Exception as e:
                    print(f"   ❌ Erro ao verificar conteúdo: {e}")
            else:
                print(f"   ❌ Diretório NÃO encontrado: {expected_path}")
                print("   💡 Sugestão: Execute o download do dataset")

    def check_processed_datasets(self):
        """Check status of processed datasets"""
        print("\n🔬 VERIFICAÇÃO DOS DATASETS PROCESSADOS:")
        print("-" * 50)

        for dataset_id, file_path in self.processed_datasets.items():
            full_path = self.base_path / file_path
            print(f"\n🔍 {dataset_id.replace('_', ' ').title()}")

            if full_path.exists():
                try:
                    # Verificar tamanho e estrutura básica
                    file_size = full_path.stat().st_size / (1024 * 1024)  # MB
                    print(f"   📊 Tamanho: {file_size:.1f} MB")
                    # Tentar ler primeiras linhas para verificar estrutura
                    if file_path.endswith(".csv"):
                        try:
                            df = pd.read_csv(full_path, nrows=5)
                            print(f"   📊 Colunas: {len(df.columns)}")
                            print(f"   📊 Linhas de exemplo: {len(df)}")
                            print(
                                f"   📋 Colunas encontradas: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}"
                            )
                        except Exception as e:
                            print(f"   ⚠️  Erro ao ler CSV: {e}")
                    else:
                        print("   📄 Arquivo encontrado (não CSV)")

                except Exception as e:
                    print(f"   ❌ Erro ao verificar arquivo: {e}")
            else:
                print(f"   ❌ Arquivo NÃO encontrado: {full_path}")

    def check_configuration_files(self):
        """Check configuration files for dataset references"""
        print("\n⚙️  VERIFICAÇÃO DOS ARQUIVOS DE CONFIGURAÇÃO:")
        print("-" * 50)

        config_files = [
            "scripts/config/swow_zuco_pipeline.yaml",
            "PROVENANCE.yaml",
            "data/provenance_templates/provenance_zuco.yaml",
        ]

        for config_file in config_files:
            full_path = self.base_path / config_file
            print(f"\n🔍 {config_file}")

            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Procurar referências aos datasets
                    dataset_refs = []
                    for dataset in ["derco", "geco", "lpp", "onestop", "zuco"]:
                        if dataset.lower() in content.lower():
                            dataset_refs.append(dataset.upper())

                    if dataset_refs:
                        print(
                            f"   ✅ Referências encontradas: {', '.join(dataset_refs)}"
                        )
                    else:
                        print("   ⚠️  Nenhuma referência específica encontrada")

                    # Verificar se há caminhos absolutos problemáticos
                    if "/home/agourakis82/FASTDATA" in content:
                        print("   ⚠️  Contém caminhos absolutos desatualizados")
                except Exception as e:
                    print(f"   ❌ Erro ao ler arquivo: {e}")
            else:
                print(f"   ❌ Arquivo NÃO encontrado: {full_path}")

    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n📝 GERANDO RELATÓRIO DE DIAGNÓSTICO...")
        print("-" * 50)

        report_path = self.base_path / "reports" / "dataset_diagnostic_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 🔍 DIAGNÓSTICO ABRANGENTE DOS DATASETS EEG/RT\n\n")
            f.write(
                f"**Data de geração:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write("## 📋 RESUMO EXECUTIVO\n\n")
            f.write(
                "Este relatório diagnostica o status de todos os datasets EEG/RT mencionados:\n"
            )
            f.write("- **ZuCo v1 & v2**: Datasets de EEG durante leitura\n")
            f.write("- **DERCo**: Dutch Reading Corpus (EEG + Eye-tracking)\n")
            f.write("- **GECO**: Groningen Eyetracking Corpus\n")
            f.write("- **LPP**: Le Petit Prince (EEG + fMRI)\n")
            f.write("- **OneStop**: English Reading Corpus (Eye-tracking)\n\n")

            f.write("## 📁 STATUS DOS DATASETS BRUTOS\n\n")

            for dataset_id, info in self.datasets.items():
                f.write(f"### {info['name']}\n\n")
                f.write(f"- **Descrição**: {info['description']}\n")
                f.write(f"- **Fonte**: {info['source']}\n")

                expected_path = self.base_path / info["expected_path"]
                if expected_path.exists():
                    f.write(f"- **Status**: ✅ Encontrado em `{expected_path}`\n")

                    # Verificar conteúdo detalhado
                    try:
                        contents = list(expected_path.rglob("*"))
                        files_count = len([f for f in contents if f.is_file()])
                        f.write(f"- **Conteúdo**: {files_count} arquivos encontrados\n")

                        for file_type in info["files"]:
                            matching_files = [
                                f
                                for f in contents
                                if file_type.lower() in f.name.lower()
                            ]
                            if matching_files:
                                f.write(
                                    f"- **{file_type}**: ✅ {len(matching_files)} arquivos\n"
                                )
                            else:
                                f.write(
                                    f"- **{file_type}**: ❌ Nenhum arquivo encontrado\n"
                                )
                    except Exception as e:
                        f.write(f"- **Erro**: {e}\n")
                else:
                    f.write(f"- **Status**: ❌ NÃO encontrado em `{expected_path}`\n")
                    f.write("- **Ação necessária**: Download do dataset\n")

                f.write("\n")

            f.write("## 🔬 STATUS DOS DATASETS PROCESSADOS\n\n")

            for dataset_id, file_path in self.processed_datasets.items():
                f.write(f"### {dataset_id.replace('_', ' ').title()}\n\n")
                full_path = self.base_path / file_path

                if full_path.exists():
                    file_size = full_path.stat().st_size / (1024 * 1024)
                    f.write(f"- **Tamanho**: {file_size:.1f} MB\n")
                    if file_path.endswith(".csv"):
                        try:
                            df = pd.read_csv(full_path, nrows=1)
                            f.write(f"- **Colunas**: {len(df.columns)}\n")
                        except Exception:
                            f.write(
                                "- **Status**: Arquivo encontrado (formato não CSV)\n"
                            )
                    else:
                        f.write("- **Status**: Arquivo encontrado\n")
                else:
                    f.write(f"- **Status**: ❌ NÃO encontrado em `{full_path}`\n")

                f.write("\n")

            f.write("## ⚙️  CONFIGURAÇÕES E SCRIPTS\n\n")

            # Scripts relacionados aos datasets
            scripts = [
                "scripts/swow_zuco_pipeline.py",
                "scripts/optimize_zuco_v2.py",
                "tools/zuco_loader.py",
                "tools/auto_discover_zuco.py",
            ]

            for script in scripts:
                script_path = self.base_path / script
                if script_path.exists():
                    f.write(f"- ✅ `{script}` - Encontrado\n")
                else:
                    f.write(f"- ❌ `{script}` - NÃO encontrado\n")

            f.write("\n## 🎯 RECOMENDAÇÕES\n\n")

            # Verificar quais datasets estão faltando
            missing_datasets = []
            for dataset_id, info in self.datasets.items():
                expected_path = self.base_path / info["expected_path"]
                if not expected_path.exists():
                    missing_datasets.append(info["name"])

            if missing_datasets:
                f.write("### Datasets Faltando:\n\n")
                for dataset in missing_datasets:
                    f.write(
                        f"1. **{dataset}**: Precisa ser baixado da fonte correspondente\n"
                    )
                f.write("\n")

            f.write("### Ações Sugeridas:\n\n")
            f.write(
                "1. **Verificar downloads**: Confirmar se todos os datasets foram baixados corretamente\n"
            )
            f.write(
                "2. **Atualizar caminhos**: Revisar arquivos de configuração para caminhos absolutos\n"
            )
            f.write(
                "3. **Executar pipeline**: Rodar o pipeline de integração SWOW-ZuCo\n"
            )
            f.write(
                "4. **Validar integridade**: Verificar integridade dos dados processados\n\n"
            )

            f.write("### Scripts Úteis:\n\n")
            f.write(
                "- `scripts/swow_zuco_pipeline.py` - Pipeline principal de integração\n"
            )
            f.write("- `tools/zuco_loader.py` - Loader específico para ZuCo\n")
            f.write("- `scripts/optimize_zuco_v2.py` - Otimizações para ZuCo v2\n\n")

        print(f"  📄 Relatório salvo: {report_path}")

    def suggest_download_commands(self):
        """Suggest commands to download missing datasets"""
        print("\n💡 SUGESTÕES PARA DOWNLOAD DOS DATASETS:")
        print("-" * 50)

        download_suggestions = {
            "ZuCo_v1": "wget https://osf.io/2urht/download -O zuco_v1.zip",
            "ZuCo_v2": "wget https://osf.io/q3zws/download -O zuco_v2.zip",
            "DERCo": "wget https://osf.io/8c7a6/download -O derco.zip",
            "GECO": "wget https://osf.io/9y4za/download -O geco.zip",
            "LPP": "wget https://openneuro.org/crn/datasets/ds005345/snapshots/1.0.0/download -O lpp.tar.gz",
            "OneStop": "wget https://osf.io/8c7a6/download -O onestop.zip",
        }

        for dataset_id, command in download_suggestions.items():
            info = self.datasets[dataset_id]
            expected_path = self.base_path / info["expected_path"]

            if not expected_path.exists():
                print(f"\n📥 {info['name']}:")
                print(f"   Comando: {command}")
                print(f"   Destino: {expected_path}")
                print("   Após download: unzip/mkdir conforme necessário")


def main():
    """Main execution function"""
    try:
        diagnostic = DatasetDiagnostic()
        diagnostic.run_full_diagnostic()
        diagnostic.suggest_download_commands()

        print("\n🎉 Diagnóstico concluído!")
        print("📄 Relatório salvo em: reports/dataset_diagnostic_report.md")

    except Exception as e:
        print(f"\n❌ Erro durante diagnóstico: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
