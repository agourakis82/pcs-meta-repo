"""
GraphQL Integration for PCS H3 System
Main FastAPI app with GraphQL endpoint
"""

from fastapi import FastAPI
from strawberry import Schema
from strawberry.fastapi import GraphQLRouter

from .schema import Mutation, Query

# Create GraphQL schema
schema = Schema(query=Query, mutation=Mutation)

# Create GraphQL router
graphql_app = GraphQLRouter(schema)

# Main FastAPI application
app = FastAPI(
    title="PCS H3 GraphQL API",
    description="Unified GraphQL API for PCS H3 Integration System",
    version="1.0.0",
)

# Include GraphQL router
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PCS H3 GraphQL API",
        "version": "1.0.0",
        "endpoints": {"graphql": "/graphql", "graphql_playground": "/graphql"},
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pcs-h3-graphql", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
