# Template - Nova API

## Estrutura Básica

### 1. Router (`api/routers/new_router.py`)
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from api.auth import require_api_key
from api.services.new_service import NewService

router = APIRouter(prefix="/new", tags=["new"])
service = NewService()

@router.get("/")
async def list_items(user: dict = Depends(require_api_key)) -> List[Dict[str, Any]]:
    """Lista todos os itens."""
    try:
        return await service.list_items()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_item(
    item_data: dict,
    user: dict = Depends(require_api_key)
) -> Dict[str, Any]:
    """Cria novo item."""
    try:
        return await service.create_item(item_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Serviço (`api/services/new_service.py`)
```python
from typing import List, Dict, Any
from api.config import get_settings

class NewService:
    """Serviço para gerenciar novos itens."""
    
    def __init__(self):
        self.config = get_settings()
        self.items = []  # Substituir por persistência real
    
    async def list_items(self) -> List[Dict[str, Any]]:
        """Lista todos os itens."""
        return self.items
    
    async def create_item(self, item_data: dict) -> Dict[str, Any]:
        """Cria novo item."""
        # Validação
        if not item_data.get("name"):
            raise ValueError("Nome é obrigatório")
        
        # Processamento
        item = {
            "id": len(self.items) + 1,
            "name": item_data["name"],
            "created_at": "2025-01-01T00:00:00"
        }
        
        self.items.append(item)
        return item
```

### 3. Testes (`tests/api/test_new_router.py`)
```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture  
def auth_headers():
    return {"Authorization": "Bearer test-key"}

def test_list_items(client, auth_headers):
    response = client.get("/new/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_item(client, auth_headers):
    item_data = {"name": "Test Item"}
    response = client.post("/new/", json=item_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"
```

### 4. Registro no Main (`api/main.py`)
```python
from api.routers import new_router

app.include_router(new_router.router)
```

## Checklist de Implementação

- [ ] Criar router com endpoints básicos
- [ ] Implementar serviço com lógica de negócio
- [ ] Adicionar validações e tratamento de erros
- [ ] Criar testes unitários e de integração
- [ ] Registrar router na aplicação principal
- [ ] Atualizar documentação da API
- [ ] Adicionar entrada no changelog

---

*Template pronto para uso! 🚀*
