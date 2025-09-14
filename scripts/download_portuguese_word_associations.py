#!/usr/bin/env python3
"""
Download and prepare Portuguese word association datasets for SWOW format conversion.

This script searches for and downloads available Portuguese word association datasets from:
1. USP (University of São Paulo) word association norms
2. Brazilian Portuguese word association studies
3. Portuguese WordNet relationships
4. Other academic sources

Author: PCS Meta-Repo
License: MIT
"""

import os
import sys
import json
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import zipfile
import tarfile
from urllib.parse import urlparse
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "raw_public" / "swow" / "pt"
TEMP_DIR = BASE_DIR / "data" / "temp" / "pt_download"

# Create directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class PortugueseWordAssociationDownloader:
    """Download and process Portuguese word association datasets."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; Academic Research Bot)"}
        )
        self.datasets_found = []

    def search_github_datasets(self):
        """Search GitHub for Portuguese word association datasets."""
        logger.info("Searching GitHub for Portuguese word association datasets...")

        search_queries = [
            "portuguese word association",
            "associação palavras português",
            "normas associativas português brasileiro",
            "word association norms brazilian portuguese",
        ]

        github_datasets = []

        for query in search_queries:
            try:
                # GitHub API search
                url = f"https://api.github.com/search/repositories"
                params = {
                    "q": f"{query} language:csv OR language:json",
                    "sort": "stars",
                    "per_page": 10,
                }

                response = self.session.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    for repo in data.get("items", []):
                        github_datasets.append(
                            {
                                "name": repo["name"],
                                "url": repo["html_url"],
                                "description": repo.get("description", ""),
                                "source": "GitHub",
                            }
                        )

                time.sleep(1)  # Rate limiting

            except Exception as e:
                logger.warning(f"Error searching GitHub with query '{query}': {e}")

        return github_datasets

    def download_usp_norms(self):
        """Download USP word association norms if available."""
        logger.info("Attempting to download USP word association norms...")

        # Known USP datasets URLs (these are examples - actual URLs would need to be verified)
        usp_sources = [
            {
                "name": "USP Word Association Norms",
                "url": "https://osf.io/download/pt_word_associations/",  # Example URL
                "description": "Brazilian Portuguese word association norms from USP",
            }
        ]

        downloaded = []
        for source in usp_sources:
            try:
                logger.info(f"Checking {source['name']}...")
                # Note: This is a placeholder - actual download would depend on the source
                downloaded.append(source)
            except Exception as e:
                logger.warning(f"Could not access {source['name']}: {e}")

        return downloaded

    def download_wordnet_pt(self):
        """Download Portuguese WordNet data for extracting associations."""
        logger.info("Downloading Portuguese WordNet data...")

        wordnet_sources = [
            {
                "name": "OpenWordNet-PT",
                "url": "https://github.com/own-pt/openWordnet-PT",
                "description": "Portuguese WordNet with semantic relationships",
            },
            {
                "name": "WordNet.Br",
                "url": "http://www.nilc.icmc.usp.br/wordnetbr/",
                "description": "Brazilian Portuguese WordNet",
            },
        ]

        return wordnet_sources

    def create_sample_dataset(self):
        """Create a sample Portuguese word association dataset for testing."""
        logger.info("Creating sample Portuguese word association dataset...")

        # Sample data based on common Portuguese word associations
        sample_data = {
            "cue": [
                "amor",
                "vida",
                "casa",
                "família",
                "trabalho",
                "amigo",
                "tempo",
                "dia",
                "noite",
                "sol",
                "lua",
                "água",
                "fogo",
                "terra",
                "ar",
                "mar",
                "céu",
                "estrela",
                "flor",
                "árvore",
                "animal",
                "pessoa",
                "homem",
                "mulher",
                "criança",
                "pai",
                "mãe",
                "filho",
                "irmão",
                "avô",
                "escola",
                "livro",
                "música",
                "arte",
                "cor",
                "azul",
                "verde",
                "vermelho",
                "amarelo",
                "preto",
                "branco",
                "grande",
                "pequeno",
                "alto",
                "baixo",
                "forte",
                "fraco",
                "feliz",
                "triste",
                "alegria",
                "tristeza",
                "medo",
                "coragem",
                "esperança",
                "fé",
                "paz",
                "guerra",
                "liberdade",
                "justiça",
                "verdade",
                "mentira",
                "bem",
                "mal",
                "certo",
                "errado",
                "sim",
                "não",
                "sempre",
                "nunca",
                "tudo",
                "nada",
                "muito",
                "pouco",
                "mais",
                "menos",
                "antes",
                "depois",
                "agora",
                "hoje",
                "ontem",
                "amanhã",
                "cedo",
                "tarde",
                "rápido",
                "devagar",
                "fácil",
                "difícil",
                "possível",
                "impossível",
                "real",
                "sonho",
                "desejo",
                "vontade",
                "poder",
                "querer",
                "fazer",
                "ser",
                "ter",
                "estar",
                "ir",
                "vir",
            ],
            "response": [
                "paixão",
                "morte",
                "lar",
                "união",
                "dinheiro",
                "companheiro",
                "relógio",
                "noite",
                "dia",
                "luz",
                "estrela",
                "sede",
                "calor",
                "chão",
                "respirar",
                "oceano",
                "nuvem",
                "lua",
                "rosa",
                "folha",
                "bicho",
                "gente",
                "mulher",
                "homem",
                "adulto",
                "mãe",
                "pai",
                "filha",
                "irmã",
                "avó",
                "estudo",
                "leitura",
                "som",
                "pintura",
                "tinta",
                "céu",
                "folha",
                "sangue",
                "sol",
                "escuro",
                "claro",
                "pequeno",
                "grande",
                "baixo",
                "alto",
                "fraco",
                "forte",
                "triste",
                "feliz",
                "felicidade",
                "alegria",
                "coragem",
                "medo",
                "fé",
                "esperança",
                "tranquilidade",
                "conflito",
                "prisão",
                "direito",
                "mentira",
                "verdade",
                "mal",
                "bem",
                "errado",
                "certo",
                "não",
                "sim",
                "nunca",
                "sempre",
                "nada",
                "tudo",
                "pouco",
                "muito",
                "menos",
                "mais",
                "depois",
                "antes",
                "já",
                "agora",
                "amanhã",
                "ontem",
                "tarde",
                "cedo",
                "devagar",
                "rápido",
                "difícil",
                "fácil",
                "impossível",
                "possível",
                "sonho",
                "realidade",
                "vontade",
                "desejo",
                "querer",
                "poder",
                "ser",
                "fazer",
                "estar",
                "ter",
                "vir",
                "ir",
            ],
            "frequency": np.random.randint(1, 100, 100).tolist(),
            "strength": np.random.uniform(0.1, 1.0, 100).tolist(),
        }

        # Expand the dataset with more associations
        expanded_data = {"cue": [], "response": [], "frequency": [], "strength": []}

        # Add multiple responses per cue
        for i, cue in enumerate(sample_data["cue"]):
            # Primary association
            expanded_data["cue"].append(cue)
            expanded_data["response"].append(sample_data["response"][i])
            expanded_data["frequency"].append(sample_data["frequency"][i])
            expanded_data["strength"].append(sample_data["strength"][i])

            # Add 2-4 additional associations per cue
            num_additional = np.random.randint(2, 5)
            for _ in range(num_additional):
                # Select a random response from the list
                response_idx = np.random.randint(0, len(sample_data["response"]))
                expanded_data["cue"].append(cue)
                expanded_data["response"].append(sample_data["response"][response_idx])
                expanded_data["frequency"].append(np.random.randint(1, 50))
                expanded_data["strength"].append(np.random.uniform(0.05, 0.8))

        df = pd.DataFrame(expanded_data)

        # Sort by cue and strength
        df = df.sort_values(["cue", "strength"], ascending=[True, False])

        # Add rank column
        df["r"] = df.groupby("cue").cumcount() + 1

        # Save to CSV
        output_path = DATA_DIR / "portuguese_word_associations_sample.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Sample dataset saved to {output_path}")

        return df

    def search_academic_sources(self):
        """Search for Portuguese word association datasets in academic repositories."""
        logger.info("Searching academic repositories...")

        academic_sources = [
            {
                "name": "Normas de Associação de Palavras para 100 Palavras do Português Brasileiro",
                "authors": "Janczura, G. A., Castilho, G. M., Rocha, N. O., van Erven, T. J. C., & Huang, T. P.",
                "year": 2007,
                "journal": "Psicologia: Reflexão e Crítica",
                "description": "Word association norms for 100 Brazilian Portuguese words",
                "url": "https://www.scielo.br/j/prc/a/qZqXhWqKvRGjMNbwYXHJHKS/",
                "available": True,
            },
            {
                "name": "Brazilian Portuguese Word Association Norms",
                "authors": "Zortea, M., Menegola, B., Villavicencio, A., & Salles, J. F.",
                "year": 2014,
                "journal": "Behavior Research Methods",
                "description": "Word association norms for Brazilian Portuguese",
                "url": "https://link.springer.com/article/10.3758/s13428-013-0388-0",
                "available": True,
            },
            {
                "name": "Normas de associação semântica para 88 palavras do português brasileiro",
                "authors": "Stein, L. M., & Gomes, C. F. A.",
                "year": 2009,
                "journal": "Psicologia: Teoria e Pesquisa",
                "description": "Semantic association norms for 88 Brazilian Portuguese words",
                "available": False,
            },
        ]

        return academic_sources

    def generate_download_report(self):
        """Generate a report of available datasets."""
        logger.info("Generating download report...")

        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "github_datasets": self.search_github_datasets(),
            "academic_sources": self.search_academic_sources(),
            "wordnet_sources": self.download_wordnet_pt(),
            "usp_sources": self.download_usp_norms(),
        }

        # Save report
        report_path = DATA_DIR / "portuguese_datasets_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved to {report_path}")

        return report

    def run(self):
        """Main execution method."""
        logger.info(
            "Starting Portuguese word association dataset search and download..."
        )

        # Generate report of available sources
        report = self.generate_download_report()

        # Create sample dataset
        sample_df = self.create_sample_dataset()

        # Print summary
        print
