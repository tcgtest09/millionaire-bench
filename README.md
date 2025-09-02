# "Wer wird Millionär?" LLM Benchmark

 i have created a benchmark for german "who wants to be millionaire" questions. there are 45x15 questions, all 45 rounds go from easy to hard and all tested models ran through all 45 rounds and got kicked out of a round if the answer was wrong, keeping the current winnings. no jokers.

i am a bit limited with the selection of llm's since i run them on my framework laptop 13 (amd ryzen 5 7640u with 32 gb ram), so i mainly used smaller llm's. also, qwen3's thinking went on for way to long for each question so i just tested non-thinking models except for gpt-oss-20b (low). but in my initial testing for qwen3-4b-thinking-2507, it seemed to worsen the quality of answers at least for the first questions.

the first few questions are often word-play and idioms questions needing great understanding of the german language. these proved to be very hard for most llm's but are easily solvable by the average german. once the first few questions were solved the models had an easier time answering.

i tried to use optimal model settings and included them in the table, let me know if they could be improved. all models are quant Q4_K_M.

i have close to no python coding ability so the main script was created with qwen3-coder. the project (with detailed results for each model, and the queationaire) is open souce and available on github.

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
|------------|---------------|--------------|------------------|--------------|------------|
| *gpt-oss-20b (low) | 21B | 4B | 80.177€ | 3 | T:1, K:0, P:1.0, Min:0.0 |
| mistral-small-3.2 | 24B | 24B | 63.812€ | 2 | T:0.15, K:40, P:0.95, Min:0.05 |
| qwen3-30b-a3b-2507 | 30B | 3B | 52.216€ | 2 | T:0.7, K:20, P:0.8, Min:0.0 |
| meta-llama-3.1-8b-instruct | 8B | 8B | 23.904€ | 1 | T:0.6, K:40, P:0.9, Min:0.05 |
| microsoft-phi-4 | 14B | 14B | 5.884€ | 0 | T:0.6, K:40, P:0.9, Min:0.05 |
| gemma-3-12b | 12B | 12B | 3.648€ | 0 | T:0.8, K:40, P:0.9, Min:0.05 |
| granite-3.2-8b | 8B | 8B | 726€ | 0 | T:0.6, K:50, P:0.9, Min:0.05 |
| qwen3-4b-2507 | 4B | 4B | 643€ | 0 | T:0.7, K:40, P:0.8, Min:0.05 |
| mistral-nemo-instruct-2407 | 12B | 12B | 227€ | 0 | T:0.3, K:-1, P:0.77, Min:0.025 |
| llama-3.2-3b-instruct | 3B | 3B | 104€ | 0 | T:0.6, K:40, P:0.9, Min:0.05 |
| gemma-3-4b | 4B | 4B | 103€ | 0 | T:1, K:64, P:0.95, Min:0 |
| phi-4-mini-instruct | 3B | 3B | 84€ | 0 | T:0.8, K:40, P:0.95, Min:0.05 |

*thinking

### Different quant tests
| Model Name | Q4_K_M | Q8_0 | Difference |
|------------|--------|------|------------|
| qwen3-4b-instruct-2507 | 643€ | 4.457€ | +593% |
| gemma-3-4b | 103€ | 141€ | +36% |
| llama-3.2-3b-instruct | 104€ | 78€ | -25% |

ran every test 3 times and picked the median. results are very inconsistent for small models (±40%)

### User Submitted Results

| Model Name | Total Params | Active Params | Average Winnings | Million Wins | Parameters |
|------------|--------------|---------------|------------------|--------------|------------|
| z-ai/glm-4.5-FP8 | 355B | 32B | 410.813€ | 17 | T:0.6, K:40, P:0.9, Min:0.1 |
| z-ai-glm-4.5-air-FP8 | 106B | 12B | 281.459€ | 12 | T:0.6, K:40, P:0.9, Min:0.1 |
| c4ai-command-a-03-2025 | 111B | 111B | 155.636€ | 6 | T:0.6, K:40, P:0.9, Min:0.1 |
| Behemoth-123B-v1.2 | 123B | 123B | 84.963€ | 3 | T:0.6, K:40, P:0.9, Min:0.1 |

## Rules
- 45 unique rounds
- if lost, current winnings are kept
- no jokers

## Resources
Questions: https://github.com/GerritKainz/wer_wird_millionaer

## Thanks to
[/user/FullOf_Bad_Ideas/](https://www.reddit.com/user/FullOf_Bad_Ideas/) for submitting `c4ai-command-a-03-2025`, `Behemoth-123B-v1.2` and `z-ai-glm-4.5-air-FP8`
