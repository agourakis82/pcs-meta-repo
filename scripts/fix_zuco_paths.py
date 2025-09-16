#!/usr/bin/env python3
"""
Script para corrigir nomes de diretórios com espaços no dataset ZuCo
Parte do Plano de Recuperação PCS v1.0
"""

import os
import shutil
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fix_zuco_directory_names():
    """Corrige nomes de diretórios com espaços no ZuCo"""

    print("🔧 CORRETOR DE CAMINHOS ZUCO")
    print("=" * 50)

    base_paths = ["data/raw_public/zuco/v1", "data/raw_public/zuco/v2"]

    # Mapear nomes problemáticos
    name_fixes = {
        "task1- SR": "task1_SR",
        "task2- NR": "task2_NR",
        "task3 - TSR": "task3_TSR",
        "Matlab files": "matlab_files",
        "Raw data": "raw_data",
        "Preprocessed": "preprocessed",
    }

    total_fixes = 0

    for base_path in base_paths:
        if not os.path.exists(base_path):
            logger.warning(f"Caminho não encontrado: {base_path}")
            continue

        print(f"\n📁 Processando: {base_path}")

        # Corrigir nomes no nível raiz
        for old_name, new_name in name_fixes.items():
            old_path = os.path.join(base_path, old_name)
            new_path = os.path.join(base_path, new_name)

            if os.path.exists(old_path) and not os.path.exists(new_path):
                try:
                    shutil.move(old_path, new_path)
                    print(f"  ✅ Renomeado: {old_name} -> {new_name}")
                    total_fixes += 1
                except Exception as e:
                    logger.error(f"Erro ao renomear {old_name}: {e}")
            elif os.path.exists(old_path) and os.path.exists(new_path):
                print(f"  ⚠️  Destino já existe: {new_name}")
            else:
                print(f"  ℹ️  Não encontrado: {old_name}")

        # Corrigir nomes em subdiretórios recursivamente
        for root, dirs, files in os.walk(base_path):
            for dir_name in dirs[:]:  # Cópia da lista para modificação segura
                if any(char in dir_name for char in [" ", "-"]):
                    old_dir_path = os.path.join(root, dir_name)
                    new_dir_name = (
                        dir_name.replace(" ", "_").replace("-", "_").replace("__", "_")
                    )
                    new_dir_path = os.path.join(root, new_dir_name)

                    if not os.path.exists(new_dir_path):
                        try:
                            shutil.move(old_dir_path, new_dir_path)
                            print(
                                f"  ✅ Subdir renomeado: {dir_name} -> {new_dir_name}"
                            )
                            total_fixes += 1
                        except Exception as e:
                            logger.error(
                                f"Erro ao renomear subdiretório {dir_name}: {e}"
                            )

    print(f"\n🎯 RESULTADO: {total_fixes} correções aplicadas")
    return total_fixes


def validate_zuco_structure():
    """Valida a estrutura corrigida do ZuCo"""

    print("\n🔍 VALIDANDO ESTRUTURA CORRIGIDA")
    print("=" * 40)

    expected_structure = {
        "data/raw_public/zuco/v1": [
            "task1_SR",
            "task3_TSR",
            "preprocessed",
            "matlab_files",
        ],
        "data/raw_public/zuco/v2": ["preprocessed", "matlab_files"],
    }

    validation_results = {}

    for base_path, expected_dirs in expected_structure.items():
        if not os.path.exists(base_path):
            validation_results[base_path] = {"status": "missing", "found": []}
            continue

        found_dirs = [
            d
            for d in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, d))
        ]

        missing_dirs = [d for d in expected_dirs if d not in found_dirs]
        extra_dirs = [d for d in found_dirs if d not in expected_dirs]

        validation_results[base_path] = {
            "status": "ok" if not missing_dirs else "incomplete",
            "found": found_dirs,
            "missing": missing_dirs,
            "extra": extra_dirs,
        }

        print(f"\n📁 {base_path}:")
        print(f"  ✅ Encontrados: {len(found_dirs)} diretórios")
        if missing_dirs:
            print(f"  ❌ Faltando: {missing_dirs}")
        if extra_dirs:
            print(f"  ℹ️  Extras: {extra_dirs}")

    return validation_results


def create_zuco_index():
    """Cria índice dos arquivos ZuCo disponíveis"""

    print("\n📋 CRIANDO ÍNDICE DE ARQUIVOS ZUCO")
    print("=" * 40)

    zuco_index = {}
    base_paths = ["data/raw_public/zuco/v1", "data/raw_public/zuco/v2"]

    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue

        version = os.path.basename(base_path)
        zuco_index[version] = {}

        for root, dirs, files in os.walk(base_path):
            rel_path = os.path.relpath(root, base_path)
            if rel_path != ".":
                # Contar arquivos por tipo
                file_types = {}
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1

                if file_types:  # Só adicionar se houver arquivos
                    zuco_index[version][rel_path] = {
                        "total_files": len(files),
                        "file_types": file_types,
                        "sample_files": files[:3],  # Primeiros 3 arquivos como amostra
                    }

    # Salvar índice
    import json

    index_path = "reports/zuco_file_index.json"
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    with open(index_path, "w") as f:
        json.dump(zuco_index, f, indent=2)

    print(f"📄 Índice salvo em: {index_path}")

    # Mostrar resumo
    for version, dirs in zuco_index.items():
        print(f"\n📊 {version.upper()}:")
        for dir_path, info in dirs.items():
            print(f"  📁 {dir_path}: {info['total_files']} arquivos")
            for ext, count in info["file_types"].items():
                print(f"    {ext}: {count}")

    return zuco_index


def main():
    """Função principal"""

    print("🚀 INICIANDO CORREÇÃO DE CAMINHOS ZUCO")
    print("=" * 60)

    try:
        # Passo 1: Corrigir nomes de diretórios
        fixes_applied = fix_zuco_directory_names()

        # Passo 2: Validar estrutura
        validation_results = validate_zuco_structure()

        # Passo 3: Criar índice
        zuco_index = create_zuco_index()

        # Resumo final
        print("\n" + "=" * 60)
        print("🎯 RESUMO DA CORREÇÃO")
        print("=" * 60)
        print(f"✅ Correções aplicadas: {fixes_applied}")

        all_ok = all(result["status"] == "ok" for result in validation_results.values())
        print(f"✅ Estrutura validada: {'SIM' if all_ok else 'PARCIAL'}")

        total_files = sum(
            sum(dir_info["total_files"] for dir_info in version_dirs.values())
            for version_dirs in zuco_index.values()
        )
        print(f"✅ Arquivos indexados: {total_files}")

        if fixes_applied > 0:
            print("\n⚠️  IMPORTANTE: Reinicie qualquer script que use dados ZuCo")
            print("   Os caminhos foram alterados e podem afetar imports existentes")

        print("\n🚀 Próximo passo: Executar scripts/extract_real_fixation_data.py")

        return True

    except Exception as e:
        logger.error(f"Erro durante correção: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
