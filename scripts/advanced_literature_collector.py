#!/usr/bin/env python3
"""
Advanced Literature Collector for RAG++
Sistema avançado para coletar papers recentes em modelagem, estatística, gráficos e matemática
"""

import asyncio
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import aiohttp
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Paper:
    """Estrutura de dados para papers científicos"""

    title: str
    authors: List[str]
    abstract: str
    url: str
    source: str  # arXiv, PubMed, SemanticScholar
    categories: List[str]
    published_date: str
    keywords: List[str]
    citation_count: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    significance_score: float = 0.0
    technical_concepts: List[str] = None
    methodology: str = ""
    results_summary: str = ""
    code_availability: bool = False

    def __post_init__(self):
        if self.technical_concepts is None:
            self.technical_concepts = []


class AdvancedLiteratureCollector:
    """Coletor avançado de literatura científica"""

    def __init__(self):
        self.session = None

        # Configurações de busca por área
        self.search_configs = {
            "machine_learning": {
                "arxiv_categories": ["cs.LG", "cs.AI", "stat.ML"],
                "keywords": [
                    "deep learning",
                    "neural networks",
                    "transformers",
                    "diffusion models",
                    "attention mechanisms",
                    "BERT",
                    "GPT",
                    "reinforcement learning",
                    "federated learning",
                    "meta-learning",
                    "few-shot learning",
                    "self-supervised learning",
                    "contrastive learning",
                ],
                "pubmed_terms": [
                    "machine learning",
                    "deep learning",
                    "artificial intelligence",
                    "neural network",
                    "predictive modeling",
                ],
            },
            "statistics": {
                "arxiv_categories": ["stat.ME", "stat.TH", "stat.CO", "math.ST"],
                "keywords": [
                    "bayesian inference",
                    "causal inference",
                    "survival analysis",
                    "time series",
                    "MCMC",
                    "variational inference",
                    "gaussian processes",
                    "bootstrap",
                    "regularization",
                    "hypothesis testing",
                    "experimental design",
                    "A/B testing",
                    "multiple testing",
                    "false discovery rate",
                ],
                "pubmed_terms": [
                    "statistical methods",
                    "bayesian analysis",
                    "survival analysis",
                    "time series analysis",
                    "statistical inference",
                ],
            },
            "visualization": {
                "arxiv_categories": ["cs.GR", "cs.HC", "cs.CV"],
                "keywords": [
                    "data visualization",
                    "information visualization",
                    "visual analytics",
                    "interactive visualization",
                    "dashboard design",
                    "chart design",
                    "network visualization",
                    "3D visualization",
                    "augmented reality",
                    "virtual reality",
                    "scientific visualization",
                    "exploratory data analysis",
                ],
                "pubmed_terms": [
                    "data visualization",
                    "information visualization",
                    "graphical methods",
                    "visual analytics",
                    "scientific visualization",
                ],
            },
            "mathematics": {
                "arxiv_categories": ["math.OC", "math.NA", "math.AP", "cs.NA"],
                "keywords": [
                    "optimization",
                    "numerical methods",
                    "linear algebra",
                    "convex optimization",
                    "stochastic optimization",
                    "gradient descent",
                    "automatic differentiation",
                    "computational geometry",
                    "graph theory",
                    "network analysis",
                    "differential equations",
                    "finite element",
                    "monte carlo",
                ],
                "pubmed_terms": [
                    "mathematical modeling",
                    "computational methods",
                    "numerical analysis",
                    "optimization methods",
                    "algorithmic methods",
                ],
            },
        }

        # Filtros de qualidade
        self.quality_filters = {
            "min_abstract_length": 100,
            "min_title_length": 10,
            "required_sections": ["abstract"],
            "exclude_keywords": [
                "review",
                "survey",
                "tutorial",
            ],  # Focar em trabalhos originais
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_arxiv(
        self, area: str, days_back: int = 7, max_results: int = 50
    ) -> List[Paper]:
        """Busca papers no arXiv"""
        config = self.search_configs[area]
        categories = "+OR+".join([f"cat:{cat}" for cat in config["arxiv_categories"]])

        # Data limite
        date_limit = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")

        # Query de busca
        query = f"({categories})+AND+submittedDate:[{date_limit}*+TO+*]"

        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_arxiv_response(content, area)
                else:
                    logger.error(f"Erro na busca arXiv: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Erro ao buscar no arXiv: {e}")
            return []

    def _parse_arxiv_response(self, xml_content: str, area: str) -> List[Paper]:
        """Parse da resposta XML do arXiv"""
        papers = []

        try:
            root = ET.fromstring(xml_content)
            namespace = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", namespace):
                title = entry.find("atom:title", namespace)
                summary = entry.find("atom:summary", namespace)
                published = entry.find("atom:published", namespace)

                if title is None or summary is None:
                    continue

                # Extrair autores
                authors = []
                for author in entry.findall("atom:author", namespace):
                    name = author.find("atom:name", namespace)
                    if name is not None:
                        authors.append(name.text.strip())

                # Extrair categorias
                categories = []
                for category in entry.findall("atom:category", namespace):
                    term = category.get("term")
                    if term:
                        categories.append(term)

                # URL do paper
                url = ""
                for link in entry.findall("atom:link", namespace):
                    if link.get("title") == "pdf":
                        url = link.get("href", "")
                        break

                # Extrair conceitos técnicos do abstract
                abstract_text = summary.text.strip()
                technical_concepts = self._extract_technical_concepts(
                    abstract_text, area
                )
                keywords = self._extract_keywords(
                    title.text + " " + abstract_text, area
                )

                paper = Paper(
                    title=title.text.strip(),
                    authors=authors,
                    abstract=abstract_text,
                    url=url,
                    source="arXiv",
                    categories=categories,
                    published_date=published.text if published is not None else "",
                    keywords=keywords,
                    technical_concepts=technical_concepts,
                    significance_score=self._calculate_significance_score(
                        title.text, abstract_text, area
                    ),
                )

                if self._passes_quality_filter(paper):
                    papers.append(paper)

        except ET.ParseError as e:
            logger.error(f"Erro ao parsear XML do arXiv: {e}")

        return papers

    async def search_semantic_scholar(
        self, area: str, days_back: int = 7, max_results: int = 30
    ) -> List[Paper]:
        """Busca papers no Semantic Scholar"""
        config = self.search_configs[area]
        papers = []

        # Buscar por palavras-chave importantes da área
        for keyword in config["keywords"][:5]:  # Limitar para evitar rate limiting
            try:
                url = "https://api.semanticscholar.org/graph/v1/paper/search"
                params = {
                    "query": keyword,
                    "limit": max_results // 5,
                    "fields": "title,authors,abstract,url,venue,year,citationCount,influentialCitationCount,publicationDate",
                    "year": f"{datetime.now().year - 1}-{datetime.now().year}",  # Últimos 2 anos
                }

                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        papers.extend(
                            self._parse_semantic_scholar_response(data, area, keyword)
                        )
                    else:
                        logger.warning(
                            f"Erro na busca Semantic Scholar para '{keyword}': {response.status}"
                        )

                # Rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(
                    f"Erro ao buscar no Semantic Scholar para '{keyword}': {e}"
                )

        return papers

    def _parse_semantic_scholar_response(
        self, data: Dict, area: str, search_keyword: str
    ) -> List[Paper]:
        """Parse da resposta do Semantic Scholar"""
        papers = []

        if "data" not in data:
            return papers

        for item in data["data"]:
            if not item.get("abstract") or not item.get("title"):
                continue

            authors = [author.get("name", "") for author in item.get("authors", [])]

            technical_concepts = self._extract_technical_concepts(
                item["abstract"], area
            )
            keywords = self._extract_keywords(
                item["title"] + " " + item["abstract"], area
            )

            paper = Paper(
                title=item["title"],
                authors=authors,
                abstract=item["abstract"],
                url=item.get("url", ""),
                source="Semantic Scholar",
                categories=[area, search_keyword],
                published_date=item.get("publicationDate", ""),
                keywords=keywords,
                citation_count=item.get("citationCount", 0),
                venue=item.get("venue", ""),
                technical_concepts=technical_concepts,
                significance_score=self._calculate_significance_score(
                    item["title"],
                    item["abstract"],
                    area,
                    citation_count=item.get("citationCount", 0),
                ),
            )

            if self._passes_quality_filter(paper):
                papers.append(paper)

        return papers

    def _extract_technical_concepts(self, text: str, area: str) -> List[str]:
        """Extrai conceitos técnicos do texto baseado na área"""
        concepts = set()
        text_lower = text.lower()

        # Conceitos específicos por área
        area_concepts = {
            "machine_learning": [
                "transformer",
                "attention",
                "bert",
                "gpt",
                "diffusion",
                "gan",
                "vae",
                "reinforcement learning",
                "federated learning",
                "meta-learning",
                "few-shot",
                "zero-shot",
                "self-supervised",
                "contrastive learning",
                "neural architecture search",
                "knowledge distillation",
            ],
            "statistics": [
                "bayesian",
                "mcmc",
                "variational inference",
                "gaussian process",
                "bootstrap",
                "cross-validation",
                "regularization",
                "lasso",
                "ridge",
                "false discovery rate",
                "multiple testing",
                "causal inference",
                "instrumental variables",
                "propensity score",
                "survival analysis",
            ],
            "visualization": [
                "interactive visualization",
                "dashboard",
                "d3.js",
                "plotly",
                "bokeh",
                "network visualization",
                "force-directed",
                "treemap",
                "heatmap",
                "parallel coordinates",
                "scatterplot matrix",
                "brushing and linking",
            ],
            "mathematics": [
                "convex optimization",
                "gradient descent",
                "newton method",
                "quasi-newton",
                "conjugate gradient",
                "automatic differentiation",
                "finite element",
                "spectral methods",
                "monte carlo",
                "linear programming",
                "semidefinite programming",
            ],
        }

        if area in area_concepts:
            for concept in area_concepts[area]:
                if concept in text_lower:
                    concepts.add(concept)

        # Conceitos matemáticos gerais
        math_patterns = [
            r"\b(algorithm|optimization|convergence|complexity)\b",
            r"\b(theorem|lemma|proof|proposition)\b",
            r"\b(matrix|tensor|vector|eigenvalue)\b",
            r"\b(probability|distribution|likelihood|posterior)\b",
        ]

        for pattern in math_patterns:
            matches = re.findall(pattern, text_lower)
            concepts.update(matches)

        return list(concepts)

    def _extract_keywords(self, text: str, area: str) -> List[str]:
        """Extrai palavras-chave relevantes do texto"""
        config = self.search_configs[area]
        keywords = set()
        text_lower = text.lower()

        # Buscar palavras-chave conhecidas da área
        for keyword in config["keywords"]:
            if keyword in text_lower:
                keywords.add(keyword)

        # Extrair termos técnicos usando regex
        technical_terms = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        keywords.update([term.lower() for term in technical_terms if len(term) > 3])

        return list(keywords)[:10]  # Limitar a 10 keywords

    def _calculate_significance_score(
        self, title: str, abstract: str, area: str, citation_count: Optional[int] = None
    ) -> float:
        """Calcula score de significância do paper"""
        score = 0.0
        text = (title + " " + abstract).lower()

        # Pontos por palavras-chave importantes
        important_keywords = {
            "machine_learning": [
                "breakthrough",
                "state-of-the-art",
                "novel",
                "efficient",
                "scalable",
            ],
            "statistics": ["unbiased", "consistent", "asymptotic", "robust", "optimal"],
            "visualization": [
                "interactive",
                "real-time",
                "scalable",
                "intuitive",
                "novel",
            ],
            "mathematics": [
                "convergence",
                "optimal",
                "efficient",
                "complexity",
                "theoretical",
            ],
        }

        if area in important_keywords:
            for keyword in important_keywords[area]:
                if keyword in text:
                    score += 0.2

        # Pontos por citações (se disponível)
        if citation_count is not None:
            score += min(citation_count / 100, 1.0)  # Max 1.0 ponto

        # Pontos por novidade (palavras como "new", "novel", "first")
        novelty_terms = ["new", "novel", "first", "breakthrough", "innovative"]
        for term in novelty_terms:
            if term in text:
                score += 0.1

        # Penalizar se for review/survey
        if any(term in text for term in ["review", "survey", "tutorial"]):
            score -= 0.5

        return max(0.0, min(5.0, score))  # Score entre 0 e 5

    def _passes_quality_filter(self, paper: Paper) -> bool:
        """Verifica se o paper passa nos filtros de qualidade"""
        if len(paper.abstract) < self.quality_filters["min_abstract_length"]:
            return False

        if len(paper.title) < self.quality_filters["min_title_length"]:
            return False

        # Verificar se não é apenas review/survey
        text = (paper.title + " " + paper.abstract).lower()
        exclude_count = sum(
            1 for keyword in self.quality_filters["exclude_keywords"] if keyword in text
        )

        # Permitir se tiver conceitos técnicos suficientes mesmo sendo review
        if exclude_count > 0 and len(paper.technical_concepts) < 3:
            return False

        return True

    async def collect_recent_papers(
        self, areas: List[str] = None, days_back: int = 7, max_per_source: int = 30
    ) -> Dict[str, List[Paper]]:
        """Coleta papers recentes de todas as fontes"""
        if areas is None:
            areas = list(self.search_configs.keys())

        all_papers = {}

        for area in areas:
            logger.info(f"🔍 Coletando papers para área: {area}")
            area_papers = []

            # Buscar no arXiv
            logger.info(f"  📚 Buscando no arXiv...")
            arxiv_papers = await self.search_arxiv(area, days_back, max_per_source)
            area_papers.extend(arxiv_papers)
            logger.info(f"  ✅ {len(arxiv_papers)} papers encontrados no arXiv")

            # Buscar no Semantic Scholar
            logger.info(f"  🔬 Buscando no Semantic Scholar...")
            semantic_papers = await self.search_semantic_scholar(
                area, days_back, max_per_source
            )
            area_papers.extend(semantic_papers)
            logger.info(
                f"  ✅ {len(semantic_papers)} papers encontrados no Semantic Scholar"
            )

            # Remover duplicatas
            unique_papers = self._remove_duplicates(area_papers)

            # Ordenar por score de significância
            unique_papers.sort(key=lambda p: p.significance_score, reverse=True)

            all_papers[area] = unique_papers[:max_per_source]  # Limitar resultado final
            logger.info(
                f"  🎯 {len(all_papers[area])} papers únicos selecionados para {area}"
            )

        return all_papers

    def _remove_duplicates(self, papers: List[Paper]) -> List[Paper]:
        """Remove papers duplicados baseado no título"""
        seen_titles = set()
        unique_papers = []

        for paper in papers:
            title_normalized = re.sub(r"\W+", "", paper.title.lower())
            if title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_papers.append(paper)

        return unique_papers

    def save_papers_to_file(self, papers: Dict[str, List[Paper]], output_file: str):
        """Salva papers coletados em arquivo JSON"""
        output_data = {}

        for area, area_papers in papers.items():
            output_data[area] = [asdict(paper) for paper in area_papers]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📁 Papers salvos em: {output_file}")


async def main():
    """Função principal para teste"""
    async with AdvancedLiteratureCollector() as collector:
        # Coletar papers dos últimos 7 dias
        papers = await collector.collect_recent_papers(
            areas=["machine_learning", "statistics", "visualization", "mathematics"],
            days_back=7,
            max_per_source=20,
        )

        # Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"/tmp/advanced_papers_{timestamp}.json"
        collector.save_papers_to_file(papers, output_file)

        # Estatísticas
        total_papers = sum(len(area_papers) for area_papers in papers.values())
        print(f"\n📊 RELATÓRIO DE COLETA:")
        print(f"Total de papers coletados: {total_papers}")
        for area, area_papers in papers.items():
            avg_score = (
                sum(p.significance_score for p in area_papers) / len(area_papers)
                if area_papers
                else 0
            )
            print(f"  {area}: {len(area_papers)} papers (score médio: {avg_score:.2f})")

        return papers


if __name__ == "__main__":
    asyncio.run(main())
