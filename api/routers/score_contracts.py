"""Darwin Platform Score Contracts Router

REST endpoints for sandboxed score contract execution.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from api.security import rate_limit, require_api_key
from services.score_contracts import (
    ContractInput,
    ContractOutput,
    ContractType,
    ExecutionStatus,
    get_sandbox,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/contracts",
    tags=["Score Contracts"],
    dependencies=[Depends(require_api_key), Depends(rate_limit)],
)


class ExecuteContractRequest(BaseModel):
    """Contract execution request."""

    contract_type: str = Field(..., description="Contract type to execute")
    data: Dict[str, Any] = Field(..., description="Input data for contract")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Contract parameters"
    )
    timeout_seconds: Optional[float] = Field(
        30.0, ge=1.0, le=300.0, description="Timeout in seconds"
    )


class ContractExecutionResponse(BaseModel):
    """Contract execution response."""

    execution_id: str
    contract_type: str
    status: str
    score: Optional[float]
    confidence: Optional[float]
    metadata: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: Optional[float]
    timestamp: Optional[str]


class AvailableContract(BaseModel):
    """Available contract information."""

    type: str
    name: str
    description: str
    schema: Dict[str, Any]


class BatchExecuteRequest(BaseModel):
    """Batch contract execution request."""

    contracts: List[ExecuteContractRequest] = Field(..., max_items=10)


class BatchExecuteResponse(BaseModel):
    """Batch execution response."""

    results: List[ContractExecutionResponse]
    total_count: int
    success_count: int
    error_count: int


def _contract_type_from_string(type_str: str) -> ContractType:
    """Convert string to ContractType enum."""
    try:
        return ContractType(type_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown contract type: {type_str}. "
            f"Available types: {[t.value for t in ContractType]}",
        )


def _contract_output_to_response(output: ContractOutput) -> ContractExecutionResponse:
    """Convert ContractOutput to response model."""
    return ContractExecutionResponse(
        execution_id=output.execution_id,
        contract_type=output.contract_type.value,
        status=output.status.value,
        score=output.score,
        confidence=output.confidence,
        metadata=output.metadata,
        error_message=output.error_message,
        execution_time_ms=output.execution_time_ms,
        timestamp=output.timestamp,
    )


@router.post("/execute", response_model=ContractExecutionResponse)
async def execute_contract(
    request: ExecuteContractRequest, response: Response
) -> ContractExecutionResponse:
    """
    Execute a score contract in sandboxed environment.

    Args:
        request: Contract execution request
        response: FastAPI response for headers

    Returns:
        Contract execution result
    """
    try:
        # Convert string to contract type
        contract_type = _contract_type_from_string(request.contract_type)

        # Create contract input
        contract_input = ContractInput(
            contract_type=contract_type,
            data=request.data,
            parameters=request.parameters,
            timeout_seconds=request.timeout_seconds or 30.0,
        )

        # Execute in sandbox
        sandbox = get_sandbox()
        result = await sandbox.execute_contract(contract_input)

        # Set response headers
        response.headers["X-Contract-Type"] = contract_type.value
        response.headers["X-Execution-Status"] = result.status.value
        response.headers["X-Execution-ID"] = result.execution_id

        if result.execution_time_ms:
            response.headers["X-Execution-Time-MS"] = str(int(result.execution_time_ms))

        return _contract_output_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contract execution failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Contract execution failed: {str(e)}"
        )


@router.post("/batch-execute", response_model=BatchExecuteResponse)
async def batch_execute_contracts(
    request: BatchExecuteRequest, response: Response
) -> BatchExecuteResponse:
    """
    Execute multiple contracts in batch.

    Args:
        request: Batch execution request
        response: FastAPI response for headers

    Returns:
        Batch execution results
    """
    try:
        sandbox = get_sandbox()
        results = []
        success_count = 0
        error_count = 0

        for contract_request in request.contracts:
            try:
                # Convert and execute each contract
                contract_type = _contract_type_from_string(
                    contract_request.contract_type
                )

                contract_input = ContractInput(
                    contract_type=contract_type,
                    data=contract_request.data,
                    parameters=contract_request.parameters,
                    timeout_seconds=contract_request.timeout_seconds or 30.0,
                )

                result = await sandbox.execute_contract(contract_input)
                results.append(_contract_output_to_response(result))

                if result.status == ExecutionStatus.COMPLETED:
                    success_count += 1
                else:
                    error_count += 1

            except Exception as e:
                logger.warning(f"Individual contract execution failed: {e}")
                error_count += 1
                # Continue with other contracts

        # Set response headers
        response.headers["X-Batch-Total"] = str(len(request.contracts))
        response.headers["X-Batch-Success"] = str(success_count)
        response.headers["X-Batch-Errors"] = str(error_count)

        return BatchExecuteResponse(
            results=results,
            total_count=len(request.contracts),
            success_count=success_count,
            error_count=error_count,
        )

    except Exception as e:
        logger.error(f"Batch execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch execution failed: {str(e)}")


@router.get("/available", response_model=List[AvailableContract])
async def get_available_contracts() -> List[AvailableContract]:
    """
    Get list of available score contracts.

    Returns:
        List of available contracts with schemas
    """
    try:
        sandbox = get_sandbox()
        contracts = sandbox.get_available_contracts()

        return [
            AvailableContract(
                type=contract["type"],
                name=contract["name"],
                description=_get_contract_description(contract["type"]),
                schema=contract["schema"],
            )
            for contract in contracts
        ]

    except Exception as e:
        logger.error(f"Failed to get available contracts: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve available contracts"
        )


@router.get("/schema/{contract_type}")
async def get_contract_schema(contract_type: str) -> Dict[str, Any]:
    """
    Get input schema for a specific contract type.

    Args:
        contract_type: Contract type to get schema for

    Returns:
        JSON schema for contract input
    """
    try:
        contract_type_enum = _contract_type_from_string(contract_type)
        sandbox = get_sandbox()

        schema = sandbox.get_contract_schema(contract_type_enum)
        if not schema:
            raise HTTPException(
                status_code=404,
                detail=f"Schema not found for contract type: {contract_type}",
            )

        return schema

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get contract schema: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve contract schema"
        )


@router.get("/history", response_model=List[ContractExecutionResponse])
async def get_execution_history(
    contract_type: Optional[str] = None, limit: int = 50
) -> List[ContractExecutionResponse]:
    """
    Get contract execution history.

    Args:
        contract_type: Optional filter by contract type
        limit: Maximum number of results

    Returns:
        List of recent executions
    """
    try:
        sandbox = get_sandbox()

        contract_type_enum = None
        if contract_type:
            contract_type_enum = _contract_type_from_string(contract_type)

        history = sandbox.get_execution_history(contract_type_enum, limit)

        return [_contract_output_to_response(result) for result in history]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution history: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve execution history"
        )


@router.get("/examples/{contract_type}")
async def get_contract_examples(contract_type: str) -> Dict[str, Any]:
    """
    Get example inputs for a contract type.

    Args:
        contract_type: Contract type to get examples for

    Returns:
        Example input data and parameters
    """
    contract_type_enum = _contract_type_from_string(contract_type)

    examples = {
        ContractType.DELTA_KEC_V1: {
            "data": {
                "source_entropy": 8.5,
                "target_entropy": 7.2,
                "mutual_information": 3.1,
            },
            "parameters": {"alpha": 0.7, "beta": 0.3},
        },
        ContractType.ZUCO_READING_V1: {
            "data": {
                "eeg_features": {
                    "theta_power": 12.5,
                    "alpha_power": 8.3,
                    "beta_power": 15.7,
                    "gamma_power": 9.2,
                },
                "eye_tracking_features": {
                    "avg_fixation_duration": 245.0,
                    "avg_saccade_velocity": 180.0,
                    "regression_rate": 0.15,
                    "reading_speed_wpm": 220.0,
                },
            },
            "parameters": {"eeg_weight": 0.6, "et_weight": 0.4},
        },
        ContractType.EDITORIAL_V1: {
            "data": {
                "text_metrics": {
                    "readability_score": 85.0,
                    "grammar_score": 92.0,
                    "vocabulary_diversity": 0.75,
                    "coherence_score": 88.0,
                    "originality_score": 78.0,
                }
            },
            "parameters": {
                "weights": {
                    "readability": 0.2,
                    "grammar": 0.25,
                    "vocabulary": 0.15,
                    "coherence": 0.25,
                    "originality": 0.15,
                }
            },
        },
    }

    example = examples.get(contract_type_enum)
    if not example:
        raise HTTPException(
            status_code=404,
            detail=f"No examples available for contract type: {contract_type}",
        )

    return example


def _get_contract_description(contract_type: str) -> str:
    """Get human-readable description for contract type."""
    descriptions = {
        "delta_kec_v1": "Delta Knowledge Exchange Coefficient - measures knowledge transfer efficiency",
        "zuco_reading_v1": "ZuCo Reading Score - EEG and eye-tracking based reading comprehension",
        "editorial_v1": "Editorial Quality Score - comprehensive text quality assessment",
    }

    return descriptions.get(contract_type, f"Score contract: {contract_type}")


@router.get("/health")
async def contracts_health() -> Dict[str, Any]:
    """
    Health check for score contracts service.

    Returns:
        Health status and contract availability
    """
    try:
        sandbox = get_sandbox()
        contracts = sandbox.get_available_contracts()

        return {
            "status": "healthy",
            "message": "Score contracts service operational",
            "available_contracts": len(contracts),
            "contract_types": [c["type"] for c in contracts],
        }

    except Exception as e:
        logger.error(f"Contracts health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Score contracts error: {str(e)}",
            "available_contracts": 0,
            "contract_types": [],
        }
