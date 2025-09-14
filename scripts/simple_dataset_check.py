#!/usr/bin/env python3
"""
Diagnóstico Simples dos Datasets EEG/RT
Verifica status dos datasets: ZuCo v1/v2, DERCo, GECO, LPP, OneStop
"""

from pathlib import Path


def check_datasets():
    """Check status of all EEG/RT datasets"""
    base_path = Path(__file__).parent.parent

    print("🔍 DIAGNÓSTICO DOS DATASETS EEG/RT")
    print("=" * 50)

    datasets = {
        "ZuCo_v1": {
            "path": "data/raw_public/zuco/v1",
            "expected": ["task1- SR", "task3 - TSR"],
            "source": "https://osf.io/2urht/",
        },
        "ZuCo_v2": {
            "path": "data/raw_public/zuco/v2",
            "expected": ["task2 - TSR", "eeg"],
            "source": "https://osf.io/q3zws/",
        },
        "DERCo": {
            "path": "data/raw_public/derco",
            "expected": ["eeg", "et"],
            "source": "https://osf.io/8c7a6/",
        },
        "GECO": {
            "path": "data/raw_public/geco",
            "expected": ["et", "behavioral"],
            "source": "https://osf.io/9y4za/",
        },
        "LPP": {
            "path": "data/raw_public/lpp",
            "expected": ["eeg", "fmri"],
            "source": "https://openneuro.org/datasets/ds005345",
        },
        "OneStop": {
            "path": "data/raw_public/onestop",
            "expected": ["et", "behavioral"],
            "source": "https://osf.io/8c7a6/",
        },
    }

    print("\n📁 VERIFICAÇÃO DOS DATASETS BRUTOS:")
    print("-" * 40)

    missing_datasets = []

    for name, info in datasets.items():
        print(f"\n🔍 {name}")
        full_path = base_path / info["path"]

        if full_path.exists():
            print(f"   ✅ ENCONTRADO: {full_path}")

            # Contar arquivos
            try:
                files = list(full_path.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                print(f"   📊 Arquivos: {file_count}")

                # Verificar tipos esperados
                for expected_type in info["expected"]:
                    matching = [f for f in files if expected_type in f.name.lower()]
                    if matching:
                        print(f"   📁 {expected_type}: {len(matching)} arquivos")
                    else:
                        print(f"   ⚠️  {expected_type}: Não encontrado")

            except Exception as e:
                print(f"   ❌ Erro ao verificar: {e}")

        else:
            print(f"   ❌ NÃO ENCONTRADO: {full_path}")
            print(f"   📥 Fonte: {info['source']}")
            missing_datasets.append(name)

    print("\n🔬 VERIFICAÇÃO DOS DATASETS PROCESSADOS:")
    print("-" * 40)

    processed_files = [
        "data/processed/integrated_neuro_swow.csv",
        "data/processed/zuco_aligned_real_et_eeg.csv",
        "data/processed/zuco_word_level_all_subjects_real_et_eeg.csv",
    ]

    for file_path in processed_files:
        full_path = base_path / file_path
        if full_path.exists():
            size_mb = full_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {file_path} ({size_mb:.1f} MB)")
        else:
            print(f"   ❌ {file_path}")

    print("\n💡 RESUMO:")
    print("-" * 40)

    if missing_datasets:
        print(f"📥 Datasets faltando: {', '.join(missing_datasets)}")
        print("\n💡 Sugestões para download:")
        for dataset in missing_datasets:
            info = datasets[dataset]
            print(f"   • {dataset}: {info['source']}")
    else:
        print("✅ Todos os datasets foram encontrados!")

    print("\n📄 Relatório salvo em: reports/dataset_status.txt")

    # Salvar relatório simples
    report_path = base_path / "reports" / "dataset_status.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write("STATUS DOS DATASETS EEG/RT\n")
        f.write("=" * 30 + "\n\n")

        f.write("DATASETS FALTANDO:\n")
        for dataset in missing_datasets:
            f.write(f"- {dataset}\n")

        f.write("\nDATASETS ENCONTRADOS:\n")
        for name, info in datasets.items():
            if name not in missing_datasets:
                f.write(f"- {name}\n")


if __name__ == "__main__":
    check_datasets()
