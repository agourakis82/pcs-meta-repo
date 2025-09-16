"""
Sistema H4 - Format Handlers

Manipuladores para diferentes formatos de dados.
Suporte a JSON, CSV, Parquet, XML, Excel e formatos científicos.
"""

import asyncio
import csv
import io
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

from ..config import DataFormat, DataSinkConfig, DataSourceConfig
from ..engine import DataSink, DataSource, ProcessingContext

logger = logging.getLogger(__name__)


class FormatHandler(ABC):
    """Classe base para manipuladores de formato."""

    def __init__(self, format_type: DataFormat):
        self.format_type = format_type
        self.logger = logging.getLogger(f"h4.format.{format_type.value}")

    @abstractmethod
    async def read_file(self, file_path: Path) -> AsyncIterator[Any]:
        """Lê arquivo e retorna dados."""
        pass

    @abstractmethod
    async def write_file(self, file_path: Path, data: Any) -> bool:
        """Escreve dados em arquivo."""
        pass

    @abstractmethod
    def parse_data(self, raw_data: bytes) -> Any:
        """Parseia dados brutos."""
        pass

    @abstractmethod
    def serialize_data(self, data: Any) -> bytes:
        """Serializa dados."""
        pass

    def get_file_extensions(self) -> List[str]:
        """Retorna extensões de arquivo suportadas."""
        return []


class JSONHandler(FormatHandler):
    """Manipulador para formato JSON."""

    def __init__(self):
        super().__init__(DataFormat.JSON)

    async def read_file(self, file_path: Path) -> AsyncIterator[Any]:
        """Lê arquivo JSON."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Se for lista, retorna item por item
                if isinstance(data, list):
                    for item in data:
                        yield item
                else:
                    yield data

        except Exception as e:
            self.logger.error(f"Error reading JSON file {file_path}: {e}")
            raise

    async def write_file(self, file_path: Path, data: Any) -> bool:
        """Escreve arquivo JSON."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            self.logger.error(f"Error writing JSON file {file_path}: {e}")
            return False

    def parse_data(self, raw_data: bytes) -> Any:
        """Parseia JSON de bytes."""
        return json.loads(raw_data.decode("utf-8"))

    def serialize_data(self, data: Any) -> bytes:
        """Serializa para JSON bytes."""
        return json.dumps(data, ensure_ascii=False).encode("utf-8")

    def get_file_extensions(self) -> List[str]:
        return [".json", ".jsonl"]


class CSVHandler(FormatHandler):
    """Manipulador para formato CSV."""

    def __init__(self):
        super().__init__(DataFormat.CSV)
        self.delimiter = ","
        self.quotechar = '"'
        self.encoding = "utf-8"

    async def read_file(self, file_path: Path) -> AsyncIterator[Dict[str, Any]]:
        """Lê arquivo CSV."""
        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                reader = csv.DictReader(
                    f, delimiter=self.delimiter, quotechar=self.quotechar
                )

                for row in reader:
                    # Converte valores vazios para None
                    cleaned_row = {k: (v if v != "" else None) for k, v in row.items()}
                    yield cleaned_row

        except Exception as e:
            self.logger.error(f"Error reading CSV file {file_path}: {e}")
            raise

    async def write_file(self, file_path: Path, data: List[Dict[str, Any]]) -> bool:
        """Escreve arquivo CSV."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if not data:
                return True

            # Obtém cabeçalhos da primeira linha
            fieldnames = list(data[0].keys())

            with open(file_path, "w", newline="", encoding=self.encoding) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                )

                writer.writeheader()
                writer.writerows(data)

            return True

        except Exception as e:
            self.logger.error(f"Error writing CSV file {file_path}: {e}")
            return False

    def parse_data(self, raw_data: bytes) -> List[Dict[str, Any]]:
        """Parseia CSV de bytes."""
        text_data = raw_data.decode(self.encoding)
        reader = csv.DictReader(
            io.StringIO(text_data), delimiter=self.delimiter, quotechar=self.quotechar
        )
        return list(reader)

    def serialize_data(self, data: List[Dict[str, Any]]) -> bytes:
        """Serializa para CSV bytes."""
        if not data:
            return b""

        output = io.StringIO()
        fieldnames = list(data[0].keys())

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
        )

        writer.writeheader()
        writer.writerows(data)

        return output.getvalue().encode(self.encoding)

    def get_file_extensions(self) -> List[str]:
        return [".csv", ".tsv"]


class XMLHandler(FormatHandler):
    """Manipulador para formato XML."""

    def __init__(self):
        super().__init__(DataFormat.XML)

    async def read_file(self, file_path: Path) -> AsyncIterator[Any]:
        """Lê arquivo XML."""
        try:
            # Importa biblioteca XML se disponível
            import xml.etree.ElementTree as ET

            tree = ET.parse(file_path)
            root = tree.getroot()

            # Converte XML para dicionário
            def xml_to_dict(element):
                result = {}

                # Adiciona atributos
                if element.attrib:
                    result.update(element.attrib)

                # Adiciona texto
                if element.text and element.text.strip():
                    if len(element) == 0:
                        return element.text.strip()
                    result["text"] = element.text.strip()

                # Adiciona filhos
                for child in element:
                    child_data = xml_to_dict(child)
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = child_data

                return result

            yield xml_to_dict(root)

        except ImportError:
            self.logger.error("XML parsing requires xml.etree.ElementTree")
            raise
        except Exception as e:
            self.logger.error(f"Error reading XML file {file_path}: {e}")
            raise

    async def write_file(self, file_path: Path, data: Any) -> bool:
        """Escreve arquivo XML."""
        try:
            import xml.etree.ElementTree as ET

            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Converte dicionário para XML
            def dict_to_xml(data, root_name="root"):
                root = ET.Element(root_name)

                def add_element(parent, key, value):
                    if isinstance(value, dict):
                        elem = ET.SubElement(parent, key)
                        for k, v in value.items():
                            add_element(elem, k, v)
                    elif isinstance(value, list):
                        for item in value:
                            add_element(parent, key, item)
                    else:
                        elem = ET.SubElement(parent, key)
                        elem.text = str(value)

                if isinstance(data, dict):
                    for key, value in data.items():
                        add_element(root, key, value)
                else:
                    root.text = str(data)

                return root

            root = dict_to_xml(data)
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding="utf-8", xml_declaration=True)

            return True

        except ImportError:
            self.logger.error("XML writing requires xml.etree.ElementTree")
            return False
        except Exception as e:
            self.logger.error(f"Error writing XML file {file_path}: {e}")
            return False

    def parse_data(self, raw_data: bytes) -> Any:
        """Parseia XML de bytes."""
        import xml.etree.ElementTree as ET

        root = ET.fromstring(raw_data.decode("utf-8"))
        # TODO: Implementar conversão XML para dict
        return {"xml_root": root.tag}

    def serialize_data(self, data: Any) -> bytes:
        """Serializa para XML bytes."""
        # TODO: Implementar serialização para XML
        return b"<root></root>"

    def get_file_extensions(self) -> List[str]:
        return [".xml"]


class ExcelHandler(FormatHandler):
    """Manipulador para formato Excel."""

    def __init__(self):
        super().__init__(DataFormat.EXCEL)

    async def read_file(self, file_path: Path) -> AsyncIterator[Dict[str, Any]]:
        """Lê arquivo Excel."""
        try:
            # Tenta importar pandas para Excel
            import pandas as pd

            # Lê todas as planilhas
            excel_file = pd.ExcelFile(file_path)

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Converte para dicionários
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    # Adiciona metadados da planilha
                    row_dict["_sheet"] = sheet_name
                    yield row_dict

        except ImportError:
            self.logger.error("Excel support requires pandas and openpyxl")
            raise
        except Exception as e:
            self.logger.error(f"Error reading Excel file {file_path}: {e}")
            raise

    async def write_file(self, file_path: Path, data: List[Dict[str, Any]]) -> bool:
        """Escreve arquivo Excel."""
        try:
            import pandas as pd

            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Agrupa dados por planilha
            sheets = {}
            for row in data:
                sheet_name = row.pop("_sheet", "Sheet1")
                if sheet_name not in sheets:
                    sheets[sheet_name] = []
                sheets[sheet_name].append(row)

            # Escreve arquivo Excel
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                for sheet_name, sheet_data in sheets.items():
                    df = pd.DataFrame(sheet_data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            return True

        except ImportError:
            self.logger.error("Excel support requires pandas and openpyxl")
            return False
        except Exception as e:
            self.logger.error(f"Error writing Excel file {file_path}: {e}")
            return False

    def parse_data(self, raw_data: bytes) -> Any:
        """Parseia Excel de bytes."""
        # TODO: Implementar parsing de Excel de bytes
        return []

    def serialize_data(self, data: Any) -> bytes:
        """Serializa para Excel bytes."""
        # TODO: Implementar serialização para Excel
        return b""

    def get_file_extensions(self) -> List[str]:
        return [".xlsx", ".xls"]


class FileDataSource(DataSource):
    """Fonte de dados baseada em arquivo."""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.file_path = Path(config.location)
        self.handler = self._get_format_handler()

    def _get_format_handler(self) -> FormatHandler:
        """Obtém manipulador de formato apropriado."""
        handlers = {
            DataFormat.JSON: JSONHandler(),
            DataFormat.CSV: CSVHandler(),
            DataFormat.XML: XMLHandler(),
            DataFormat.EXCEL: ExcelHandler(),
        }

        handler = handlers.get(self.config.format)
        if handler is None:
            raise ValueError(f"Unsupported format: {self.config.format}")

        return handler

    async def read(self, context: ProcessingContext) -> AsyncIterator[Any]:
        """Lê dados do arquivo."""
        try:
            chunk_size = self.config.chunk_size or 1000
            batch = []

            async for item in self.handler.read_file(self.file_path):
                batch.append(item)

                if len(batch) >= chunk_size:
                    yield batch
                    batch = []

                    # Rate limiting se configurado
                    if self.config.rate_limit:
                        await asyncio.sleep(1.0 / self.config.rate_limit)

            # Retorna último batch se houver
            if batch:
                yield batch

        except Exception as e:
            self.logger.error(f"Error reading from {self.file_path}: {e}")
            raise

    async def validate(self) -> bool:
        """Valida se arquivo existe e é legível."""
        return self.file_path.exists() and self.file_path.is_file()

    async def estimate_size(self) -> Optional[int]:
        """Estima número de registros."""
        if not await self.validate():
            return None

        try:
            # Para CSV, conta linhas
            if self.config.format == DataFormat.CSV:
                with open(self.file_path, "r") as f:
                    return sum(1 for _ in f) - 1  # -1 para cabeçalho

            # Para outros formatos, retorna None (desconhecido)
            return None

        except Exception:
            return None


class FileSink(DataSink):
    """Destino de dados baseado em arquivo."""

    def __init__(self, config: DataSinkConfig):
        super().__init__(config)
        self.file_path = Path(config.location)
        self.handler = self._get_format_handler()
        self.data_buffer = []

    def _get_format_handler(self) -> FormatHandler:
        """Obtém manipulador de formato apropriado."""
        handlers = {
            DataFormat.JSON: JSONHandler(),
            DataFormat.CSV: CSVHandler(),
            DataFormat.XML: XMLHandler(),
            DataFormat.EXCEL: ExcelHandler(),
        }

        handler = handlers.get(self.config.format)
        if handler is None:
            raise ValueError(f"Unsupported format: {self.config.format}")

        return handler

    async def write(self, data: Any, context: ProcessingContext) -> bool:
        """Escreve dados no arquivo."""
        try:
            # Adiciona ao buffer
            if isinstance(data, list):
                self.data_buffer.extend(data)
            else:
                self.data_buffer.append(data)

            # Flush se atingiu tamanho do batch
            if len(self.data_buffer) >= self.config.batch_size:
                await self._flush_buffer()

            return True

        except Exception as e:
            self.logger.error(f"Error writing to {self.file_path}: {e}")
            return False

    async def _flush_buffer(self):
        """Flush buffer para arquivo."""
        if not self.data_buffer:
            return

        try:
            # Prepara arquivo de saída
            if self.config.overwrite or not self.file_path.exists():
                await self.handler.write_file(self.file_path, self.data_buffer)
            else:
                # Append para formatos que suportam
                if self.config.format == DataFormat.JSON:
                    # Para JSON, carrega dados existentes e adiciona novos
                    existing_data = []
                    if self.file_path.exists():
                        async for item in self.handler.read_file(self.file_path):
                            if isinstance(item, list):
                                existing_data.extend(item)
                            else:
                                existing_data.append(item)

                    existing_data.extend(self.data_buffer)
                    await self.handler.write_file(self.file_path, existing_data)

                elif self.config.format == DataFormat.CSV:
                    # Para CSV, adiciona linhas
                    with open(self.file_path, "a", newline="", encoding="utf-8") as f:
                        if self.data_buffer:
                            fieldnames = list(self.data_buffer[0].keys())
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writerows(self.data_buffer)

            self.data_buffer.clear()

        except Exception as e:
            self.logger.error(f"Error flushing buffer to {self.file_path}: {e}")
            raise

    async def validate(self) -> bool:
        """Valida se diretório de destino existe."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        return True

    async def finalize(self) -> bool:
        """Finaliza escrita."""
        await self._flush_buffer()
        return True


# Registry de handlers
FORMAT_HANDLERS = {
    DataFormat.JSON: JSONHandler,
    DataFormat.CSV: CSVHandler,
    DataFormat.XML: XMLHandler,
    DataFormat.EXCEL: ExcelHandler,
}


def get_format_handler(format_type: DataFormat) -> FormatHandler:
    """Obtém instância de handler para formato."""
    handler_class = FORMAT_HANDLERS.get(format_type)
    if handler_class is None:
        raise ValueError(f"Unsupported format: {format_type}")
    return handler_class()


def create_file_source(config: DataSourceConfig) -> FileDataSource:
    """Cria fonte de dados de arquivo."""
    return FileDataSource(config)


def create_file_sink(config: DataSinkConfig) -> FileSink:
    """Cria destino de dados de arquivo."""
    return FileSink(config)
