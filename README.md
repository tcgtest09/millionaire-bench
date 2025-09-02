# "Wer wird Millionär?" LLM Benchmark

This repository contains a script to test local LLMs with German "Who Wants to Be a Millionaire" questions. Results are stored as JSON files.

## Project Structure

```
├── benchmark_llm.py          # Main benchmark script
├── fragen_antworten.json     # Questions in JSON format
├── README.md                 # This file
└── results/                  # Directory containing all benchmark results
    └── result_{MODEL_NAME}.json
```

## Usage

1. Make sure your LLM server (e.g., LM Studio) is running and accessible at `http://localhost:1234`
2. Run the benchmark script:

```bash
python3 benchmark_llm.py
```

3. When prompted, enter which question to start with:
   - Enter a number between 1-45 to start with that question set (level 1-15)
   - Enter "0" to play all 45 rounds sequentially

## Benchmark Results

| Model Name | Total Params | Active Params | Average Winnings | Million Wins | Parameters |
|------------|------------------|-------------------|------------------|--------------|------------|
| *gpt-oss-20b (low) | 21B | 4B | 80.177€ | 3 | T:1, K:0, P:1.0, Min:0.0 |
| mistral-small-3.2 | 24B | 24B | 63.812€ | 2 | T:0.15, K:40, P:0.95, Min:0.05 |
| qwen3-30b-a3b-2507 | 30B | 3B | 52.216€ | 2 | T:0.7, K:20, P:0.8, Min:0.0 |
| meta-llama-3.1-8b-instruct | 8B | 8B | 23.904€ | 1 | T:0.6, K:40, P:0.9, Min:0.05 |
| microsoft-phi-4 | 14B | 14B | 5.884€ | 0 | T:0.6, K:40, P:0.9, Min:0.05 |
| gemma-3-12b | 12B | 12B | 3.648€ | 0 | T:0.8, K:40, P:0.9, Min:0.05 |
| granite-3.2-8b | 8B | 8B | 726€ | 0 | T:0.6, K:50, P:0.9, Min:0.05 |
| qwen3-4b-2507 | 4B | 4B | 540€ | 0 | T:0.7, K:40, P:0.8, Min:0.05 |
| llama-3.2-3b-instruct | 3B | 3B | 256€ | 0 | T:0.6, K:40, P:0.9, Min:0.05 |
| mistral-nemo-instruct-2407 | 12B | 12B | 227€ | 0 | T:0.3, K:-1, P:0.77, Min:0.025 |
| phi-4-mini-instruct | 3B | 3B | 84€ | 0 | T:0.8, K:40, P:0.95, Min:0.05 |
| gemma-3-4b | 4B | 4B | 66€ | 0 | T:1, K:64, P:0.95, Min:0 |

*thinking

### User Submitted Results

| Model Name | Total Params | Active Params | Average Winnings | Million Wins | Parameters |
|------------|------------------|-------------------|------------------|--------------|------------|
| z-ai-glm-4.5-air-FP8 | 106B | 12B | 281.459€ | 12 | T:0.6, K:40, P:0.9, Min:0.1 |
| c4ai-command-a-03-2025 | 111B | 111B | 155.636€ | 6 | T:0.6, K:40, P:0.9, Min:0.1 |
| Behemoth-123B-v1.2 | 123B | 123B | 84.963€ | 3 | T:0.6, K:40, P:0.9, Min:0.1 |

## Rules
- quant Q4_K_M for all models
- 45 unique rounds
- if lost, current winnings are kept
- no jokers

## Resources
Questions: https://github.com/GerritKainz/wer_wird_millionaer

## Thanks to
[/user/FullOf_Bad_Ideas/](https://www.reddit.com/user/FullOf_Bad_Ideas/) for submitting `c4ai-command-a-03-2025`, `Behemoth-123B-v1.2` and `z-ai-glm-4.5-air-FP8`
