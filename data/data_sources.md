# Data Sources — #23 Guardrails & Prompt Injection Defense

## Primary
| # | Source | URL | Use | License |
|---|--------|-----|-----|---------|
| 1 | Synthetic prompt generator | `src/prompt_guard/data.py` | 30,000 prompts incl. 5,000 injections | MIT |
| 2 | Synthetic output generator | `src/prompt_guard/data.py` | 5,000 outputs for leakage classifier | MIT |

## Secondary / reference
| Source | URL | Use |
|---|---|---|
| OWASP LLM Top-10 | https://owasp.org/www-project-top-10-for-large-language-model-applications/ | Taxonomy alignment |
| Greshake et al. (2023) | https://arxiv.org/abs/2302.12173 | Indirect injection patterns |
| Perez & Ribeiro (2022) | https://arxiv.org/abs/2211.09527 | Override-style attack patterns |

## How to download
Nothing to download — run:
```bash
python -m prompt_guard.data
```
This writes:
- `data/processed/prompts.parquet` (30,000)
- `data/processed/redteam.parquet` (5,000)
- `data/processed/outputs.parquet` (5,000)

## Attribution
If you publish results using this pipeline, please cite the project repo.
