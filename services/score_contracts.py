"""Darwin Platform Score Contracts

Sandboxed execution environment for score calculation contracts.
Implements delta_kec_v1, zuco_reading_v1, and editorial_v1 contracts.
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContractType(Enum):
    """Available score contract types."""

    DELTA_KEC_V1 = "delta_kec_v1"
    ZUCO_READING_V1 = "zuco_reading_v1"
    EDITORIAL_V1 = "editorial_v1"


class ExecutionStatus(Enum):
    """Contract execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ContractInput:
    """Input data for score contract."""

    contract_type: ContractType
    data: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None
    timeout_seconds: float = 30.0
    execution_id: Optional[str] = None

    def __post_init__(self):
        if self.execution_id is None:
            self.execution_id = str(uuid.uuid4())[:8]


@dataclass
class ContractOutput:
    """Output from score contract execution."""

    execution_id: str
    contract_type: ContractType
    status: ExecutionStatus
    score: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    timestamp: Optional[str] = None


class ScoreContract(ABC):
    """Abstract base class for score contracts."""

    def __init__(self, contract_type: ContractType):
        self.contract_type = contract_type
        self.name = contract_type.value

    @abstractmethod
    async def execute(self, input_data: ContractInput) -> ContractOutput:
        """
        Execute the score contract.

        Args:
            input_data: Contract input data

        Returns:
            Contract execution output
        """
        pass

    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data format.

        Args:
            data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for input validation.

        Returns:
            JSON schema dictionary
        """
        return {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "parameters": {"type": "object"},
            },
            "required": ["data"],
        }


class DeltaKecV1Contract(ScoreContract):
    """
    Delta Knowledge Exchange Coefficient (KEC) v1 contract.

    Calculates knowledge exchange efficiency between source and target.
    """

    def __init__(self):
        super().__init__(ContractType.DELTA_KEC_V1)

    async def execute(self, input_data: ContractInput) -> ContractOutput:
        """Execute Delta KEC calculation."""
        start_time = time.time()

        try:
            if not self.validate_input(input_data.data):
                return ContractOutput(
                    execution_id=input_data.execution_id,
                    contract_type=self.contract_type,
                    status=ExecutionStatus.FAILED,
                    error_message="Invalid input data format",
                )

            # Extract required data
            source_entropy = input_data.data.get("source_entropy", 0.0)
            target_entropy = input_data.data.get("target_entropy", 0.0)
            mutual_information = input_data.data.get("mutual_information", 0.0)

            # Parameters with defaults
            params = input_data.parameters or {}
            alpha = params.get("alpha", 0.7)  # Source weight
            beta = params.get("beta", 0.3)  # Target weight

            # Calculate Delta KEC
            if source_entropy == 0 and target_entropy == 0:
                delta_kec = 0.0
                confidence = 0.0
            else:
                # KEC = Mutual Information / Combined Entropy
                combined_entropy = alpha * source_entropy + beta * target_entropy

                if combined_entropy > 0:
                    kec = mutual_information / combined_entropy
                    # Delta normalization (0 to 1 range)
                    delta_kec = min(max(kec, 0.0), 1.0)

                    # Confidence based on entropy levels
                    min_entropy = min(source_entropy, target_entropy)
                    confidence = min(min_entropy / 10.0, 1.0)  # Assume max entropy ~10
                else:
                    delta_kec = 0.0
                    confidence = 0.0

            execution_time = (time.time() - start_time) * 1000

            return ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=self.contract_type,
                status=ExecutionStatus.COMPLETED,
                score=delta_kec,
                confidence=confidence,
                metadata={
                    "source_entropy": source_entropy,
                    "target_entropy": target_entropy,
                    "mutual_information": mutual_information,
                    "combined_entropy": alpha * source_entropy + beta * target_entropy,
                    "alpha": alpha,
                    "beta": beta,
                },
                execution_time_ms=execution_time,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Delta KEC v1 execution failed: {e}")

            return ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=self.contract_type,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time,
            )

    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate Delta KEC input."""
        required_fields = ["source_entropy", "target_entropy", "mutual_information"]

        for field in required_fields:
            if field not in data:
                return False
            if not isinstance(data[field], (int, float)):
                return False

        return True

    def get_schema(self) -> Dict[str, Any]:
        """Get Delta KEC input schema."""
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "source_entropy": {"type": "number", "minimum": 0},
                        "target_entropy": {"type": "number", "minimum": 0},
                        "mutual_information": {"type": "number", "minimum": 0},
                    },
                    "required": [
                        "source_entropy",
                        "target_entropy",
                        "mutual_information",
                    ],
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "alpha": {"type": "number", "minimum": 0, "maximum": 1},
                        "beta": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                },
            },
            "required": ["data"],
        }


class ZucoReadingV1Contract(ScoreContract):
    """
    ZuCo Reading Score v1 contract.

    Calculates reading comprehension score based on EEG and eye-tracking data.
    """

    def __init__(self):
        super().__init__(ContractType.ZUCO_READING_V1)

    async def execute(self, input_data: ContractInput) -> ContractOutput:
        """Execute ZuCo reading score calculation."""
        start_time = time.time()

        try:
            if not self.validate_input(input_data.data):
                return ContractOutput(
                    execution_id=input_data.execution_id,
                    contract_type=self.contract_type,
                    status=ExecutionStatus.FAILED,
                    error_message="Invalid input data format",
                )

            # Extract EEG and eye-tracking features
            eeg_features = input_data.data.get("eeg_features", {})
            et_features = input_data.data.get("eye_tracking_features", {})

            # EEG components (theta, alpha, beta, gamma power)
            theta_power = eeg_features.get("theta_power", 0.0)
            alpha_power = eeg_features.get("alpha_power", 0.0)
            beta_power = eeg_features.get("beta_power", 0.0)
            gamma_power = eeg_features.get("gamma_power", 0.0)

            # Eye-tracking components
            fixation_duration = et_features.get("avg_fixation_duration", 0.0)
            saccade_velocity = et_features.get("avg_saccade_velocity", 0.0)
            regression_rate = et_features.get("regression_rate", 0.0)
            reading_speed = et_features.get("reading_speed_wpm", 0.0)

            # Parameters
            params = input_data.parameters or {}
            eeg_weight = params.get("eeg_weight", 0.6)
            et_weight = params.get("et_weight", 0.4)

            # EEG-based comprehension score
            # Higher theta (4-8Hz) and gamma (30-100Hz) indicate comprehension
            # Lower alpha (8-13Hz) indicates active processing
            eeg_score = 0.0
            if theta_power + alpha_power + beta_power + gamma_power > 0:
                # Normalize and weight frequency bands
                total_power = theta_power + alpha_power + beta_power + gamma_power
                theta_norm = theta_power / total_power
                alpha_norm = alpha_power / total_power
                gamma_norm = gamma_power / total_power

                # Higher theta and gamma, lower alpha = better comprehension
                eeg_score = 0.4 * theta_norm + 0.1 * (1 - alpha_norm) + 0.5 * gamma_norm

            # Eye-tracking-based reading efficiency
            et_score = 0.0
            if fixation_duration > 0 and saccade_velocity > 0:
                # Optimal fixation duration (200-300ms), higher reading speed = better
                fixation_efficiency = max(0, 1 - abs(fixation_duration - 250) / 250)
                speed_efficiency = min(reading_speed / 300.0, 1.0)  # Assume 300 WPM max
                regression_penalty = max(0, 1 - regression_rate)

                et_score = (
                    0.4 * fixation_efficiency
                    + 0.4 * speed_efficiency
                    + 0.2 * regression_penalty
                )

            # Combined ZuCo reading score
            zuco_score = eeg_weight * eeg_score + et_weight * et_score

            # Confidence based on data quality
            eeg_quality = (
                1.0
                if (theta_power + alpha_power + beta_power + gamma_power) > 0
                else 0.0
            )
            et_quality = 1.0 if fixation_duration > 0 and reading_speed > 0 else 0.0
            confidence = (eeg_quality + et_quality) / 2.0

            execution_time = (time.time() - start_time) * 1000

            return ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=self.contract_type,
                status=ExecutionStatus.COMPLETED,
                score=zuco_score,
                confidence=confidence,
                metadata={
                    "eeg_score": eeg_score,
                    "et_score": et_score,
                    "eeg_features": eeg_features,
                    "et_features": et_features,
                    "weights": {"eeg": eeg_weight, "et": et_weight},
                },
                execution_time_ms=execution_time,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"ZuCo Reading v1 execution failed: {e}")

            return ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=self.contract_type,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time,
            )

    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate ZuCo reading input."""
        if "eeg_features" not in data and "eye_tracking_features" not in data:
            return False

        # At least one feature set must have valid data
        eeg_valid = False
        et_valid = False

        if "eeg_features" in data:
            eeg = data["eeg_features"]
            eeg_valid = isinstance(eeg, dict) and len(eeg) > 0

        if "eye_tracking_features" in data:
            et = data["eye_tracking_features"]
            et_valid = isinstance(et, dict) and len(et) > 0

        return eeg_valid or et_valid

    def get_schema(self) -> Dict[str, Any]:
        """Get ZuCo reading input schema."""
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "eeg_features": {
                            "type": "object",
                            "properties": {
                                "theta_power": {"type": "number", "minimum": 0},
                                "alpha_power": {"type": "number", "minimum": 0},
                                "beta_power": {"type": "number", "minimum": 0},
                                "gamma_power": {"type": "number", "minimum": 0},
                            },
                        },
                        "eye_tracking_features": {
                            "type": "object",
                            "properties": {
                                "avg_fixation_duration": {
                                    "type": "number",
                                    "minimum": 0,
                                },
                                "avg_saccade_velocity": {
                                    "type": "number",
                                    "minimum": 0,
                                },
                                "regression_rate": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "reading_speed_wpm": {"type": "number", "minimum": 0},
                            },
                        },
                    },
                    "anyOf": [
                        {"required": ["eeg_features"]},
                        {"required": ["eye_tracking_features"]},
                    ],
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "eeg_weight": {"type": "number", "minimum": 0, "maximum": 1},
                        "et_weight": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                },
            },
            "required": ["data"],
        }


class EditorialV1Contract(ScoreContract):
    """
    Editorial Quality v1 contract.

    Calculates editorial quality score based on text metrics.
    """

    def __init__(self):
        super().__init__(ContractType.EDITORIAL_V1)

    async def execute(self, input_data: ContractInput) -> ContractOutput:
        """Execute editorial quality calculation."""
        start_time = time.time()

        try:
            if not self.validate_input(input_data.data):
                return ContractOutput(
                    execution_id=input_data.execution_id,
                    contract_type=self.contract_type,
                    status=ExecutionStatus.FAILED,
                    error_message="Invalid input data format",
                )

            # Extract text metrics
            text_metrics = input_data.data.get("text_metrics", {})

            readability_score = text_metrics.get("readability_score", 0.0)
            grammar_score = text_metrics.get("grammar_score", 0.0)
            vocabulary_diversity = text_metrics.get("vocabulary_diversity", 0.0)
            coherence_score = text_metrics.get("coherence_score", 0.0)
            originality_score = text_metrics.get("originality_score", 0.0)

            # Parameters
            params = input_data.parameters or {}
            weights = params.get(
                "weights",
                {
                    "readability": 0.2,
                    "grammar": 0.25,
                    "vocabulary": 0.15,
                    "coherence": 0.25,
                    "originality": 0.15,
                },
            )

            # Normalize scores to 0-1 range (assuming input scores are 0-100)
            readability_norm = readability_score / 100.0
            grammar_norm = grammar_score / 100.0
            vocabulary_norm = min(vocabulary_diversity, 1.0)  # Already 0-1 ratio
            coherence_norm = coherence_score / 100.0
            originality_norm = originality_score / 100.0

            # Calculate weighted editorial score
            editorial_score = (
                weights["readability"] * readability_norm
                + weights["grammar"] * grammar_norm
                + weights["vocabulary"] * vocabulary_norm
                + weights["coherence"] * coherence_norm
                + weights["originality"] * originality_norm
            )

            # Confidence based on metric availability
            available_metrics = sum(
                [
                    1 if readability_score > 0 else 0,
                    1 if grammar_score > 0 else 0,
                    1 if vocabulary_diversity > 0 else 0,
                    1 if coherence_score > 0 else 0,
                    1 if originality_score > 0 else 0,
                ]
            )
            confidence = available_metrics / 5.0

            execution_time = (time.time() - start_time) * 1000

            return ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=self.contract_type,
                status=ExecutionStatus.COMPLETED,
                score=editorial_score,
                confidence=confidence,
                metadata={
                    "normalized_scores": {
                        "readability": readability_norm,
                        "grammar": grammar_norm,
                        "vocabulary": vocabulary_norm,
                        "coherence": coherence_norm,
                        "originality": originality_norm,
                    },
                    "weights": weights,
                    "available_metrics": available_metrics,
                },
                execution_time_ms=execution_time,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Editorial v1 execution failed: {e}")

            return ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=self.contract_type,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time,
            )

    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate editorial input."""
        if "text_metrics" not in data:
            return False

        text_metrics = data["text_metrics"]
        if not isinstance(text_metrics, dict):
            return False

        # At least one metric must be present
        required_metrics = [
            "readability_score",
            "grammar_score",
            "vocabulary_diversity",
            "coherence_score",
            "originality_score",
        ]

        return any(metric in text_metrics for metric in required_metrics)

    def get_schema(self) -> Dict[str, Any]:
        """Get editorial input schema."""
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "text_metrics": {
                            "type": "object",
                            "properties": {
                                "readability_score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                                "grammar_score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                                "vocabulary_diversity": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "coherence_score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                                "originality_score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                            },
                        }
                    },
                    "required": ["text_metrics"],
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "weights": {
                            "type": "object",
                            "properties": {
                                "readability": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "grammar": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "vocabulary": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "coherence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "originality": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                            },
                        }
                    },
                },
            },
            "required": ["data"],
        }


class ContractSandbox:
    """
    Sandboxed execution environment for score contracts.

    Provides isolation and timeout protection for contract execution.
    """

    def __init__(self):
        self.contracts: Dict[ContractType, ScoreContract] = {
            ContractType.DELTA_KEC_V1: DeltaKecV1Contract(),
            ContractType.ZUCO_READING_V1: ZucoReadingV1Contract(),
            ContractType.EDITORIAL_V1: EditorialV1Contract(),
        }
        self.execution_history: List[ContractOutput] = []

    async def execute_contract(self, input_data: ContractInput) -> ContractOutput:
        """
        Execute a score contract in sandbox.

        Args:
            input_data: Contract input data

        Returns:
            Contract execution output
        """
        contract = self.contracts.get(input_data.contract_type)
        if not contract:
            return ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=input_data.contract_type,
                status=ExecutionStatus.FAILED,
                error_message=f"Unknown contract type: {input_data.contract_type}",
            )

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                contract.execute(input_data), timeout=input_data.timeout_seconds
            )

            # Store in history
            self.execution_history.append(result)

            return result

        except asyncio.TimeoutError:
            logger.warning(f"Contract {input_data.contract_type} timed out")

            result = ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=input_data.contract_type,
                status=ExecutionStatus.TIMEOUT,
                error_message=f"Execution timed out after {input_data.timeout_seconds}s",
            )

            self.execution_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")

            result = ContractOutput(
                execution_id=input_data.execution_id,
                contract_type=input_data.contract_type,
                status=ExecutionStatus.FAILED,
                error_message=f"Sandbox error: {str(e)}",
            )

            self.execution_history.append(result)
            return result

    def get_contract_schema(
        self, contract_type: ContractType
    ) -> Optional[Dict[str, Any]]:
        """Get input schema for a contract type."""
        contract = self.contracts.get(contract_type)
        if contract:
            return contract.get_schema()
        return None

    def get_available_contracts(self) -> List[Dict[str, Any]]:
        """Get list of available contracts."""
        return [
            {
                "type": contract_type.value,
                "name": contract.name,
                "schema": contract.get_schema(),
            }
            for contract_type, contract in self.contracts.items()
        ]

    def get_execution_history(
        self, contract_type: Optional[ContractType] = None, limit: int = 100
    ) -> List[ContractOutput]:
        """Get execution history."""
        history = self.execution_history

        if contract_type:
            history = [
                result for result in history if result.contract_type == contract_type
            ]

        return history[-limit:]


# Global sandbox instance
sandbox = ContractSandbox()


def get_sandbox() -> ContractSandbox:
    """Get the global contract sandbox instance."""
    return sandbox
