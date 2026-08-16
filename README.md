\# LungInsight AI



An AI-assisted chest X-ray pneumonia screening system, built as four independent modules — an EfficientNet-B3 classifier with Grad-CAM explainability, a FastAPI backend, a React frontend, and a RAG-powered clinical chat assistant — integrated into a single application.



> \*\*Screening aid, not a diagnostic substitute.\*\* This project supports clinical decision-making; it does not replace clinical judgment. See \[Known Limitations](#known-limitations) below.



\## What it does



1\. Upload a chest X-ray

2\. A trained CNN classifies it as Normal or Pneumonia, with a confidence score

3\. Grad-CAM generates a heatmap showing which regions of the image most influenced the prediction

4\. A retrieval-grounded chat assistant answers follow-up questions, citing real clinical reference sources for every claim



\## Architecture



| Module | Folder | Stack |

|---|---|---|

| AI Model | `LungInsight-AI/` | PyTorch, EfficientNet-B3, Grad-CAM |

| Backend | `LungInsight-Backend/` | FastAPI, SQLAlchemy, PostgreSQL, Alembic |

| Frontend | `LungInsight-Frontend/` | React, TypeScript, Vite, Tailwind CSS |

| RAG Chat | `lunginsight-rag/` | LangGraph, FAISS, sentence-transformers, Groq |



Each module runs as its own process and communicates over HTTP — the backend calls the AI model service and the RAG service as independent microservices rather than importing them in-process, so each module can be developed, tested, and deployed on its own.

## Model performance



Evaluated on a held-out test set (Kaggle chest-xray-pneumonia dataset):



| Metric | Score |

|---|---|

| Accuracy | 90.54% |

| Precision | 87.87% |

| Recall | 98.46% |

| ROC AUC | 0.9619 |



\## Getting started



Each module has its own setup instructions in its respective folder (`LungInsight-AI/README.md`, `LungInsight-Backend/README.md`, etc.), including dependency installation and `.env` configuration.



Once all four modules are set up individually (dependencies installed, `.env` files filled in, PostgreSQL running), start everything at once from the repository root:



```powershell

.\\start-lunginsight.ps1

```



This launches all four services in separate windows and checks that PostgreSQL is running first. Give the AI and RAG service windows 10–20 seconds to finish loading their models before using the app. Then visit `http://localhost:5173`.



\### Requirements



\- Python 3.12+

\- Node.js 20+

\- PostgreSQL 16+

\- A \[Groq API key](https://console.groq.com) (free tier available) for the chat assistant

\- A trained model checkpoint at `LungInsight-AI/checkpoints/best.pt` (see `LungInsight-AI/MODEL.md` — not included in this repository; datasets and trained weights are excluded from version control by design)



\## Known Limitations



\*\*Grad-CAM attention on non-diagnostic regions.\*\* The classifier occasionally attends to regions outside clinically relevant lung tissue — spine/midline structures or image corner markers — rather than the pulmonary fields themselves, suggesting possible shortcut learning during training. Classification accuracy remains consistent with reported evaluation metrics; the Grad-CAM explainability layer should not be treated as a fully reliable indicator of \*why\* a given prediction was made in every case. See `LungInsight-AI/MODEL.md` for detail.



\*\*Model confidence is not a calibrated probability.\*\* Reported confidence scores are consistently high (90%+) across most predictions — a well-documented behavior of neural networks trained with standard cross-entropy loss (Guo et al., \*On Calibration of Modern Neural Networks\*, 2017). Confidence should be treated as a relative signal, not a calibrated statement of diagnostic certainty.



\## Testing



Each module has its own test suite:



```powershell

\# Backend

cd LungInsight-Backend; python -m pytest -q



\# Frontend

cd LungInsight-Frontend; npm test



\# AI model

cd LungInsight-AI; python -m pytest -q



\# RAG

cd lunginsight-rag; python -m pytest -q

```

