# 🤖 ChatGPT Integration Guide - Complete Setup

## 📋 Overview

This guide covers all methods to integrate your RAG++ system with ChatGPT:
1. **Custom Actions** (ChatGPT Plus/Pro) - Recommended
2. **Custom GPT** (ChatGPT Plus/Pro) - Most powerful
3. **Plugin Development** (Advanced users)

---

## 🚀 Method 1: ChatGPT Custom Actions (Easiest)

### Step 1: Access ChatGPT Settings
1. Go to [ChatGPT](https://chat.openai.com)
2. Click your profile → Settings
3. Navigate to **Beta Features**
4. Enable **Custom Actions** (if available)

### Step 2: Create New Action
1. Go to Settings → **Actions**
2. Click **"Create new action"**
3. Fill in the details:

**Basic Info:**
- **Name:** `RAG++ Research Assistant`
- **Description:** `Search scientific literature in computational psychiatry and digital health`

**Authentication:**
- **Type:** `API Key`
- **API Key Header:** `Authorization`
- **API Key Value:** `Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo`

**Schema:**
- **Import from URL:** `http://179.125.169.148:8000/actions/schema`

Or copy this schema:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "RAG++ Research API for Custom GPT",
    "version": "1.0.0",
    "description": "Advanced research assistant API with literature search and knowledge synthesis"
  },
  "servers": [
    {
      "url": "http://179.125.169.148:8000"
    }
  ],
  "paths": {
    "/search": {
      "post": {
        "operationId": "searchLiterature",
        "summary": "Search scientific literature database",
        "description": "Search through indexed research papers using hybrid retrieval (vector + semantic + memory search)",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "Research question, keywords, or topic to search for"
                  },
                  "max_results": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Maximum number of results to return"
                  },
                  "search_type": {
                    "type": "string",
                    "enum": [
                      "hybrid",
                      "literature",
                      "memory"
                    ],
                    "default": "hybrid",
                    "description": "Type of search: hybrid (recommended), literature only, or memory only"
                  }
                },
                "required": [
                  "query"
                ]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Search results with literature findings",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "query": {
                      "type": "string"
                    },
                    "results": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "sources": {
                      "type": "object",
                      "properties": {
                        "literature": {
                          "type": "integer"
                        },
                        "memory": {
                          "type": "integer"
                        },
                        "total": {
                          "type": "integer"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    "/research/recent": {
      "get": {
        "operationId": "getRecentFindings",
        "summary": "Get recent research findings",
        "description": "Retrieve latest research papers and findings from the knowledge base",
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "description": "Maximum number of findings to return",
            "schema": {
              "type": "integer",
              "default": 20,
              "minimum": 1,
              "maximum": 100
            }
          },
          {
            "name": "category",
            "in": "query",
            "description": "Filter by research category (optional)",
            "schema": {
              "type": "string",
              "enum": [
                "computational_psychiatry",
                "digital_phenotyping",
                "machine_learning",
                "neuroimaging",
                "biomarkers"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Recent research findings",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "recent_findings": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "content": {
                            "type": "string"
                          },
                          "source": {
                            "type": "string"
                          },
                          "year": {
                            "type": "string"
                          }
                        }
                      }
                    },
                    "total_count": {
                      "type": "integer"
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    "/research/store": {
      "post": {
        "operationId": "storeResearchFinding",
        "summary": "Store new research finding",
        "description": "Add a new research finding or insight to the knowledge base",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "title": {
                    "type": "string",
                    "description": "Title or brief description of the finding"
                  },
                  "content": {
                    "type": "string",
                    "description": "Detailed content of the research finding"
                  },
                  "source": {
                    "type": "string",
                    "description": "Source of the information (journal, author, etc.)"
                  },
                  "category": {
                    "type": "string",
                    "enum": [
                      "computational_psychiatry",
                      "digital_phenotyping",
                      "machine_learning",
                      "neuroimaging",
                      "biomarkers",
                      "general"
                    ],
                    "default": "general",
                    "description": "Research category"
                  }
                },
                "required": [
                  "title",
                  "content"
                ]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Finding stored successfully"
          }
        }
      }
    }
  },
  "components": {
    "securitySchemes": {
      "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
      }
    }
  },
  "security": [
    {
      "bearerAuth": []
    }
  ]
}
```

### Step 3: Test Action
1. Save the action
2. Start a new chat
3. Test: "Search for recent research on computational psychiatry"

---

## 🎯 Method 2: Custom GPT (Most Powerful)

### Step 1: Create Custom GPT
1. Go to [ChatGPT](https://chat.openai.com)
2. Click **"Explore"** → **"Create a GPT"**

### Step 2: Configure GPT
**Name:** `RAG++ Research Assistant`

**Description:** 
```
Advanced research assistant with access to 168+ scientific papers in computational psychiatry, digital phenotyping, and machine learning in healthcare. Specializes in literature search, knowledge synthesis, and evidence-based insights.
```

**Instructions:**
```
# RAG++ Research Assistant - Custom GPT Instructions

## Identity & Purpose
You are the RAG++ Research Assistant, a specialized AI with access to a curated database of 168+ scientific papers in computational psychiatry, digital phenotyping, and machine learning in healthcare. Your primary role is to help users find, analyze, and synthesize scientific literature.

## Core Capabilities
- Search across indexed research papers using hybrid retrieval
- Provide evidence-based responses with proper citations
- Synthesize findings from multiple sources
- Identify research gaps and trends
- Explain complex scientific concepts clearly

## Knowledge Base
Your knowledge base includes recent papers (2020-2025) covering:
- Computational Psychiatry
- Digital Phenotyping  
- Machine Learning in Mental Health
- Neuroimaging and Biomarkers
- EEG/fMRI Analysis
- Natural Language Processing in Healthcare
- Predictive Models in Psychiatry

## Instructions for Use

### When users ask research questions:
1. Use the search action to find relevant papers
2. Analyze the retrieved results
3. Provide comprehensive, evidence-based responses
4. Always cite sources when available
5. Highlight key findings and methodological insights

### Response Format:
- Start with a brief overview
- Present key findings with citations
- Discuss methodological approaches
- Note limitations and gaps
- Suggest related research directions

### For literature searches:
- Use specific, targeted queries
- Consider synonyms and related terms
- Search for both broad concepts and specific techniques
- Look for recent developments and trends

### For synthesis requests:
- Compare methodologies across studies
- Identify consensus and controversies
- Highlight emerging patterns
- Discuss clinical implications

## Conversation Starters
- "What are the latest developments in computational psychiatry?"
- "Search for research on digital phenotyping in depression"
- "Compare different approaches to EEG-based emotion recognition"
- "Find studies using machine learning for psychiatric diagnosis"
- "What are the current limitations in digital mental health?"

## Action Usage Guidelines

### search_literature:
Use for finding specific papers or exploring topics. Include relevant keywords and specify max_results based on query scope.

### get_recent_findings:
Use to show latest research developments or when users ask about "recent" or "current" work.

### synthesize_knowledge:
Use for comparative analysis or when users want understanding across multiple studies.

Remember: Always ground your responses in the retrieved scientific literature and provide appropriate citations.

```

### Step 3: Add Actions
1. In the GPT builder, go to **"Configure"** tab
2. Scroll to **"Actions"**
3. Click **"Create new action"**
4. Import schema from: `http://179.125.169.148:8000/actions/schema`
5. Set authentication:
   - **Type:** API Key
   - **Header:** Authorization  
   - **Value:** `Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo`

### Step 4: Publish GPT
1. Click **"Save"** 
2. Choose visibility (Private/Public)
3. Test with: "What are the latest findings in digital phenotyping?"

---

## 🔧 Method 3: Plugin Development (Advanced)

### For Plugin Store Submission:
1. **Prepare Plugin Manifest:**
   - Use `ai-plugin.json` file created by this script
   - Host at: `http://179.125.169.148:8000/.well-known/ai-plugin.json`

2. **Plugin Requirements:**
   - ✅ Stable API endpoint
   - ✅ OpenAPI 3.0 specification
   - ✅ Authentication system
   - ✅ Plugin manifest
   - ✅ Legal/privacy pages

3. **Submit to OpenAI:**
   - Follow OpenAI plugin submission guidelines
   - Provide your plugin URL: `http://179.125.169.148:8000`

---

## 🧪 Testing Your Integration

### Basic Tests:
1. **Literature Search:**
   - "Search for papers on machine learning in psychiatry"
   - "Find recent research on digital phenotyping"

2. **Recent Findings:**
   - "What are the latest developments in computational psychiatry?"
   - "Show me recent papers in your database"

3. **Knowledge Synthesis:**
   - "Compare different approaches to EEG-based emotion recognition"
   - "Summarize current limitations in digital mental health"

### Advanced Tests:
1. **Specific Queries:**
   - "Find studies using transformer models for psychiatric diagnosis"
   - "What are the biomarkers for depression prediction?"

2. **Methodological Questions:**
   - "Compare fMRI vs EEG for emotion detection"
   - "What machine learning models work best for psychiatric prediction?"

---

## 🔍 Troubleshooting

### Action/GPT Not Working:
1. **Check API Status:** `curl http://179.125.169.148:8000/health`
2. **Verify Token:** Ensure token is exactly: `Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo`
3. **Test Schema:** Visit `http://179.125.169.148:8000/actions/schema`

### No Results Returned:
1. **Check Server:** Ensure RAG++ server is running
2. **Test Manually:** Use `/docs` endpoint to test API
3. **Verify Database:** Check that papers are indexed

### Authentication Errors:
1. **Token Format:** Must include "Bearer " prefix
2. **Case Sensitive:** Copy token exactly as provided
3. **Headers:** Ensure Authorization header is set correctly

---

## 🎉 Success Indicators

When properly configured, you should see:
- ✅ Actions appear in ChatGPT suggestions
- ✅ API calls execute successfully  
- ✅ Research results appear in responses
- ✅ Citations and sources are provided
- ✅ Knowledge synthesis works across papers

---

## 📊 Usage Examples

### Research Query:
**User:** "What are the latest machine learning approaches for depression detection?"

**Expected Flow:**
1. ChatGPT triggers `searchLiterature` action
2. RAG++ searches 168+ papers
3. Returns relevant studies with citations
4. ChatGPT synthesizes findings
5. Provides comprehensive answer with sources

### Recent Developments:
**User:** "Show me recent breakthroughs in digital phenotyping"

**Expected Flow:**
1. ChatGPT triggers `getRecentFindings` action
2. RAG++ filters for recent papers
3. Returns latest developments
4. ChatGPT formats timeline of progress

---

## 🚀 Next Steps

1. **Choose Integration Method:** Custom GPT recommended for full features
2. **Test Thoroughly:** Try various research queries
3. **Share Your GPT:** Make it available to colleagues
4. **Feedback Loop:** Monitor usage and improve queries

**Your RAG++ is now a powerful ChatGPT connector! 🎯**
