#!/usr/bin/env python3
"""
Psychiatric Research Collector - RAG++ Extension
Coleta automaticamente descobertas recentes em psiquiatria (2020-2025)
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Nota: Evitar import cruzado de MCPRAGIntegration aqui para não criar ciclo


class PsychiatricResearchCollector:
    """Coleta e indexa descobertas recentes em psiquiatria computacional."""

    def __init__(self, output_dir: str = "ragpp/data/psychiatric_research"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Define search terms for psychiatric research
        self.psychiatric_terms = [
            # Psiquiatria Computacional
            "computational psychiatry machine learning",
            "digital biomarkers psychiatric disorders",
            "AI mental health diagnosis prediction",
            "network neuroscience psychiatric conditions",
            # Biomarcadores e Neuroimagem
            "neuroimaging biomarkers depression anxiety",
            "EEG psychiatric disorders classification",
            "fMRI connectivity psychiatric networks",
            "DTI white matter psychiatric conditions",
            # Análise de Linguagem e Fala
            "speech analysis psychiatric diagnosis",
            "natural language processing mental health",
            "semantic coherence psychotic disorders",
            "linguistic markers depression anxiety",
            # Tecnologias Emergentes
            "smartphone digital phenotyping psychiatry",
            "wearable sensors mental health monitoring",
            "virtual reality psychiatric treatment",
            "chatbots therapy mental health apps",
            # Neuroplasticidade e Tratamento
            "neuroplasticity psychiatric intervention",
            "transcranial stimulation depression treatment",
            "ketamine depression neuroplasticity mechanisms",
            "psychedelic therapy psychiatric disorders",
            # Genética e Epigenética
            "genomics psychiatric disorders GWAS",
            "epigenetic mechanisms mental illness",
            "polygenic risk scores psychiatry",
            "gene expression psychiatric conditions",
        ]

        # Journal focus areas
        self.target_journals = [
            "Nature Neuroscience",
            "Molecular Psychiatry",
            "American Journal of Psychiatry",
            "Biological Psychiatry",
            "Neuropsychopharmacology",
            "Psychological Medicine",
            "Journal of Psychiatric Research",
            "Psychiatry Research Neuroimaging",
            "NeuroImage Clinical",
            "Translational Psychiatry",
            "JAMA Psychiatry",
            "Lancet Psychiatry",
            "Nature Mental Health",
            "Digital Medicine",
        ]

    def search_pubmed_recent(
        self, query: str, years_back: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Busca artigos recentes no PubMed usando a API Entrez.
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years_back * 365)

            date_filter = f"({start_date.strftime('%Y/%m/%d')}[PDAT]:{end_date.strftime('%Y/%m/%d')}[PDAT])"

            # Build search query
            search_query = f"({query}) AND {date_filter} AND (humans[MeSH Terms])"

            # PubMed E-utilities base URL
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

            # Search for articles
            search_url = f"{base_url}esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": search_query,
                "retmax": 20,  # Limit results per query
                "sort": "relevance",
                "retmode": "json",
            }

            response = requests.get(search_url, params=search_params, timeout=10)
            response.raise_for_status()

            search_data = response.json()

            if (
                "esearchresult" not in search_data
                or "idlist" not in search_data["esearchresult"]
            ):
                return []

            pmids = search_data["esearchresult"]["idlist"]

            if not pmids:
                return []

            # Fetch detailed information
            fetch_url = f"{base_url}efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract",
            }

            # Add delay to respect API limits
            time.sleep(0.5)

            fetch_response = requests.get(fetch_url, params=fetch_params, timeout=15)
            fetch_response.raise_for_status()

            # Parse XML response (simplified)
            articles = self._parse_pubmed_xml(fetch_response.text, query)

            return articles

        except Exception as e:
            print(f"⚠️ Error searching PubMed for '{query}': {e}")
            return []

    def _parse_pubmed_xml(
        self, xml_text: str, search_term: str
    ) -> List[Dict[str, Any]]:
        """
        Parse XML response from PubMed (simplified parsing).
        """
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_text)
            articles = []

            for article in root.findall(".//PubmedArticle"):
                try:
                    # Extract basic information
                    title_elem = article.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else "No title"

                    abstract_elem = article.find(".//AbstractText")
                    abstract = (
                        abstract_elem.text
                        if abstract_elem is not None
                        else "No abstract available"
                    )

                    # Extract PMID
                    pmid_elem = article.find(".//PMID")
                    pmid = pmid_elem.text if pmid_elem is not None else "unknown"

                    # Extract journal
                    journal_elem = article.find(".//Journal/Title")
                    journal = (
                        journal_elem.text
                        if journal_elem is not None
                        else "Unknown journal"
                    )

                    # Extract year
                    year_elem = article.find(".//PubDate/Year")
                    year = year_elem.text if year_elem is not None else "unknown"

                    # Extract authors (first few)
                    authors = []
                    for author in article.findall(".//Author")[:3]:  # First 3 authors
                        lastname = author.find("LastName")
                        firstname = author.find("ForeName")
                        if lastname is not None:
                            author_name = lastname.text
                            if firstname is not None:
                                author_name = f"{firstname.text} {author_name}"
                            authors.append(author_name)

                    article_data = {
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract,
                        "journal": journal,
                        "year": year,
                        "authors": authors,
                        "search_term": search_term,
                        "collection_date": datetime.now().isoformat(),
                        "source": "pubmed_psychiatric_collection",
                    }

                    articles.append(article_data)

                except Exception as e:
                    print(f"⚠️ Error parsing article: {e}")
                    continue

            return articles

        except Exception as e:
            print(f"⚠️ Error parsing PubMed XML: {e}")
            return []

    def collect_psychiatric_research(
        self, max_articles_per_term: int = 20
    ) -> Dict[str, Any]:
        """
        Coleta descobertas recentes em psiquiatria.
        """
        print("🧠 Coletando Descobertas Recentes em Psiquiatria (2020-2025)")
        print("=" * 60)

        all_articles = []
        collection_stats = {
            "start_time": datetime.now().isoformat(),
            "search_terms_used": len(self.psychiatric_terms),
            "articles_collected": 0,
            "unique_journals": set(),
            "year_distribution": {},
            "search_term_results": {},
        }

        for i, term in enumerate(self.psychiatric_terms, 1):
            print(f"\n[{i}/{len(self.psychiatric_terms)}] Buscando: {term}")

            try:
                articles = self.search_pubmed_recent(term, years_back=5)

                if articles:
                    all_articles.extend(articles)
                    collection_stats["search_term_results"][term] = len(articles)

                    # Update statistics
                    for article in articles:
                        journal = article.get("journal", "Unknown")
                        year = article.get("year", "unknown")

                        collection_stats["unique_journals"].add(journal)
                        collection_stats["year_distribution"][year] = (
                            collection_stats["year_distribution"].get(year, 0) + 1
                        )

                    print(f"  ✅ Encontrados {len(articles)} artigos")
                else:
                    collection_stats["search_term_results"][term] = 0
                    print(f"  ⚪ Nenhum artigo encontrado")

                # Respect API rate limits
                time.sleep(1)

            except Exception as e:
                print(f"  ❌ Erro na busca: {e}")
                collection_stats["search_term_results"][term] = 0

        # Remove duplicates based on PMID
        unique_articles = {}
        for article in all_articles:
            pmid = article.get("pmid", "unknown")
            if pmid not in unique_articles:
                unique_articles[pmid] = article

        final_articles = list(unique_articles.values())

        # Update final statistics
        collection_stats["articles_collected"] = len(final_articles)
        collection_stats["unique_journals"] = list(collection_stats["unique_journals"])
        collection_stats["end_time"] = datetime.now().isoformat()

        print(f"\n📊 Coleta Concluída:")
        print(f"  • Artigos únicos coletados: {len(final_articles)}")
        print(f"  • Revistas científicas: {len(collection_stats['unique_journals'])}")
        print(f"  • Distribuição por ano: {collection_stats['year_distribution']}")

        return {"articles": final_articles, "statistics": collection_stats}

    def process_and_index_articles(
        self, articles: List[Dict[str, Any]], integration: Optional[object] = None
    ) -> Dict[str, Any]:
        """
        Processa e indexa artigos no sistema RAG++.
        """
        print("\n🔄 Processando e Indexando Artigos...")
        print("=" * 40)

        processing_stats = {
            "processed": 0,
            "indexed_in_rag": 0,
            "stored_in_mcp": 0,
            "high_relevance": 0,
            "categories": {},
        }

        for i, article in enumerate(articles, 1):
            try:
                print(f"[{i}/{len(articles)}] Processando: {article['title'][:50]}...")

                # Calculate relevance score
                relevance_score = self._calculate_relevance(article)

                # Create structured content for RAG
                rag_content = self._create_rag_content(article, relevance_score)

                # Store in RAG++ system if integration provided
                if relevance_score >= 3:
                    category = self._determine_category(article)
                    tags = self._extract_tags(article)

                    stored_ok = False
                    if integration and hasattr(integration, "store_research_finding"):
                        try:
                            stored_ok = integration.store_research_finding(
                                content=rag_content,
                                category=category,
                                tags=tags,
                                importance=min(relevance_score, 5),
                                auto_index_to_rag=True,
                            )
                        except Exception as e:
                            print(f"⚠️ Falha ao indexar via integração: {e}")

                    if stored_ok:
                        processing_stats["stored_in_mcp"] += 1
                        processing_stats["indexed_in_rag"] += 1

                        if relevance_score >= 4:
                            processing_stats["high_relevance"] += 1

                        processing_stats["categories"][category] = (
                            processing_stats["categories"].get(category, 0) + 1
                        )

                processing_stats["processed"] += 1

                # Add small delay to avoid overwhelming the system
                if i % 10 == 0:
                    time.sleep(0.5)

            except Exception as e:
                print(f"  ❌ Erro processando artigo {i}: {e}")
                continue

        print(f"\n✅ Processamento Concluído:")
        print(f"  • Artigos processados: {processing_stats['processed']}")
        print(f"  • Indexados no RAG: {processing_stats['indexed_in_rag']}")
        print(f"  • Armazenados no MCP: {processing_stats['stored_in_mcp']}")
        print(f"  • Alta relevância: {processing_stats['high_relevance']}")
        print(f"  • Categorias: {processing_stats['categories']}")

        return processing_stats

    def _calculate_relevance(self, article: Dict[str, Any]) -> int:
        """
        Calcula score de relevância para o projeto PCS.
        """
        score = 1

        title = article.get("title", "").lower()
        abstract = article.get("abstract", "").lower()
        journal = article.get("journal", "").lower()

        # Boost for computational/AI approaches
        if any(
            term in title + abstract
            for term in [
                "machine learning",
                "deep learning",
                "artificial intelligence",
                "computational",
                "algorithm",
                "neural network",
                "classification",
            ]
        ):
            score += 2

        # Boost for neuroimaging/EEG
        if any(
            term in title + abstract
            for term in [
                "eeg",
                "fmri",
                "neuroimaging",
                "brain network",
                "connectivity",
                "eye tracking",
                "neural",
                "neurofeedback",
            ]
        ):
            score += 2

        # Boost for language/semantic analysis
        if any(
            term in title + abstract
            for term in [
                "semantic",
                "language",
                "linguistic",
                "nlp",
                "speech",
                "text analysis",
                "discourse",
                "coherence",
            ]
        ):
            score += 2

        # Boost for high-impact journals
        if any(
            journal_name in journal
            for journal_name in ["nature", "science", "cell", "lancet", "jama"]
        ):
            score += 1

        # Boost for recent years
        year = article.get("year", "")
        if year in ["2024", "2025"]:
            score += 1
        elif year in ["2022", "2023"]:
            score += 0.5

        return min(score, 5)  # Cap at 5

    def _determine_category(self, article: Dict[str, Any]) -> str:
        """
        Determina categoria apropriada para o artigo.
        """
        title = article.get("title", "").lower()
        abstract = article.get("abstract", "").lower()
        content = title + " " + abstract

        if any(
            term in content
            for term in ["machine learning", "ai", "algorithm", "computational"]
        ):
            return "computational_methods"

        elif any(term in content for term in ["eeg", "fmri", "neuroimaging", "brain"]):
            return "neuroimaging_findings"

        elif any(
            term in content for term in ["semantic", "language", "linguistic", "speech"]
        ):
            return "language_analysis"

        elif any(term in content for term in ["treatment", "therapy", "intervention"]):
            return "therapeutic_insights"

        else:
            return "research_findings"

    def _extract_tags(self, article: Dict[str, Any]) -> List[str]:
        """
        Extrai tags relevantes do artigo.
        """
        tags = ["psychiatric_research", "recent_literature"]

        title = article.get("title", "").lower()
        abstract = article.get("abstract", "").lower()
        content = title + " " + abstract

        # Method tags
        method_tags = {
            "machine_learning": ["machine learning", "ml", "deep learning"],
            "neuroimaging": ["fmri", "mri", "eeg", "meg", "pet", "neuroimaging"],
            "language_analysis": ["nlp", "semantic", "linguistic", "language"],
            "network_analysis": ["network", "connectivity", "graph", "topology"],
            "biomarkers": ["biomarker", "diagnostic", "prediction"],
        }

        for tag, keywords in method_tags.items():
            if any(keyword in content for keyword in keywords):
                tags.append(tag)

        # Add year tag
        year = article.get("year", "")
        if year:
            tags.append(f"year_{year}")

        # Add search term as tag
        search_term = article.get("search_term", "")
        if search_term:
            # Create simplified tag from search term
            tag = search_term.replace(" ", "_").replace("-", "_").lower()[:20]
            tags.append(tag)

        return tags[:8]  # Limit number of tags

    def _create_rag_content(self, article: Dict[str, Any], relevance: int) -> str:
        """
        Cria conteúdo estruturado para indexação no RAG.
        """
        authors_str = ", ".join(article.get("authors", [])[:3])
        if len(article.get("authors", [])) > 3:
            authors_str += " et al."

        content = f"""
RECENT PSYCHIATRIC RESEARCH ({article.get('year', 'unknown')})

Title: {article.get('title', 'No title')}

Authors: {authors_str}

Journal: {article.get('journal', 'Unknown journal')}

PMID: {article.get('pmid', 'unknown')}

Relevance Score: {relevance}/5

Abstract:
{article.get('abstract', 'No abstract available')}

Search Context: {article.get('search_term', 'general psychiatric research')}

Collection Date: {article.get('collection_date', 'unknown')}

---
This article was automatically collected and indexed as part of the PCS project's 
literature monitoring system for recent advances in computational psychiatry and 
related fields.
""".strip()

        return content

    def save_collection_summary(self, results: Dict[str, Any]) -> str:
        """
        Salva resumo da coleta em arquivo.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.output_dir / f"psychiatric_collection_{timestamp}.json"

        # Create summary without full article content
        summary = {
            "collection_metadata": results["statistics"],
            "articles_summary": [
                {
                    "pmid": art.get("pmid"),
                    "title": art.get("title"),
                    "journal": art.get("journal"),
                    "year": art.get("year"),
                    "search_term": art.get("search_term"),
                }
                for art in results["articles"]
            ],
        }

        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Resumo salvo em: {summary_file}")
        return str(summary_file)

    def run_full_collection(self) -> Dict[str, Any]:
        """
        Executa coleta completa de descobertas psiquiátricas.
        """
        print("🚀 INICIANDO COLETA COMPLETA - DESCOBERTAS PSIQUIÁTRICAS 2020-2025")
        print("=" * 70)

        try:
            # Step 1: Collect articles
            collection_results = self.collect_psychiatric_research()

            if not collection_results["articles"]:
                print("❌ Nenhum artigo coletado. Verifique a conexão com a internet.")
                return {"success": False, "error": "No articles collected"}

            # Step 2: Process and index
            processing_stats = self.process_and_index_articles(
                collection_results["articles"]
            )

            # Step 3: Save summary
            summary_file = self.save_collection_summary(collection_results)

            # Final results
            final_results = {
                "success": True,
                "collection_stats": collection_results["statistics"],
                "processing_stats": processing_stats,
                "summary_file": summary_file,
                "total_articles": len(collection_results["articles"]),
            }

            print("\n" + "=" * 70)
            print("✅ COLETA COMPLETA FINALIZADA COM SUCESSO!")
            print(f"\n📊 Resumo Final:")
            print(f"  • Artigos coletados: {final_results['total_articles']}")
            print(f"  • Indexados no RAG++: {processing_stats['indexed_in_rag']}")
            print(f"  • Alta relevância: {processing_stats['high_relevance']}")
            print(f"  • Resumo salvo: {summary_file}")

            print(f"\n🎯 Próximos passos:")
            print(f"  • Use ./ragpp_search.sh para explorar as descobertas")
            print(f"  • Pergunte sobre 'recent psychiatric research machine learning'")
            print(
                f"  • Explore categorias: {list(processing_stats['categories'].keys())}"
            )

            return final_results

        except Exception as e:
            print(f"\n❌ Erro durante coleta: {e}")
            return {"success": False, "error": str(e)}


def main():
    """CLI para coleta de descobertas psiquiátricas."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Coleta descobertas recentes em psiquiatria para RAG++"
    )
    parser.add_argument(
        "--action",
        choices=["collect", "test", "terms"],
        default="collect",
        help="Ação a executar",
    )
    parser.add_argument(
        "--years", type=int, default=5, help="Número de anos para buscar (padrão: 5)"
    )
    parser.add_argument(
        "--output", help="Diretório de saída (padrão: ragpp/data/psychiatric_research)"
    )

    args = parser.parse_args()

    output_dir = args.output or "ragpp/data/psychiatric_research"
    collector = PsychiatricResearchCollector(output_dir)

    if args.action == "terms":
        print("🔍 Termos de Busca Configurados:")
        print("=" * 40)
        for i, term in enumerate(collector.psychiatric_terms, 1):
            print(f"{i:2d}. {term}")
        print(f"\nTotal: {len(collector.psychiatric_terms)} termos")

    elif args.action == "test":
        print("🧪 Teste Rápido - Buscando 1 termo...")
        test_term = collector.psychiatric_terms[0]
        articles = collector.search_pubmed_recent(test_term, years_back=args.years)
        print(
            f"✅ Teste concluído: {len(articles)} artigos encontrados para '{test_term}'"
        )

        if articles:
            print(f"\nExemplo de artigo coletado:")
            article = articles[0]
            print(f"  • Título: {article['title'][:80]}...")
            print(f"  • Revista: {article['journal']}")
            print(f"  • Ano: {article['year']}")
            print(f"  • PMID: {article['pmid']}")

    elif args.action == "collect":
        results = collector.run_full_collection()

        if results["success"]:
            print(f"\n🎉 Coleta finalizada com sucesso!")
        else:
            print(f"\n❌ Falha na coleta: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
