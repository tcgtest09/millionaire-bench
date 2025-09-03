#!/usr/bin/env python3
import json
import re
import time
import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Static answer schema - no need to be configurable
ANSWER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "AnswerChoice",
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "enum": ["A", "B", "C", "D"]
        }
    },
    "required": ["answer"],
    "additionalProperties": False
}


def load_config():
    """Load configuration from JSON file - config.json is required"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("Error: config.json not found!")
        print("Please create a config.json file with the required configuration.")
        print("See the repository documentation for the expected format.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: config.json contains invalid JSON: {e}")
        exit(1)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        exit(1)


# Load configuration
CONFIG = load_config()

# Extract configuration values for backward compatibility
SYSTEM_PROMPT = CONFIG["reasoning"]["system_prompt"]
MODEL_NAME = CONFIG["model"]["name"]
LLM_SERVER_URL = CONFIG["model"]["server_url"]
LLM_API_KEY = CONFIG["model"].get("api_key", "None")  # Optional API key support
TEMPERATURE = CONFIG["inference_parameters"]["temperature"]
TOP_K = CONFIG["inference_parameters"]["top_k"]
TOP_P = CONFIG["inference_parameters"]["top_p"]
MIN_P = CONFIG["inference_parameters"]["min_p"]
TOTAL_PARAMETERS = CONFIG["model"]["total_parameters"]
ACTIVE_PARAMETERS = CONFIG["model"]["active_parameters"]
USE_TWO_PHASE_REASONING = CONFIG["reasoning"]["use_two_phase"]
REASONING_SYSTEM_PROMPT = CONFIG["reasoning"]["reasoning_system_prompt"]
ANSWER_SYSTEM_PROMPT = CONFIG["reasoning"]["answer_system_prompt"]
SINGLE_PHASE_TIMEOUT = CONFIG["timeouts"]["single_phase"]
REASONING_PHASE_TIMEOUT = CONFIG["timeouts"]["reasoning_phase"]
CONCURRENCY_LEVEL = CONFIG.get("concurrency_level", 1)  # Number of concurrent game rounds

PRIZE_AMOUNTS = {
    1: "50€",
    2: "100€",
    3: "200€",
    4: "300€",
    5: "500€",
    6: "1.000€",
    7: "2.000€",
    8: "4.000€",
    9: "8.000€",
    10: "16.000€",
    11: "32.000€",
    12: "64.000€",
    13: "125.000€",
    14: "500.000€",
    15: "1.000.000€",
}


def load_questions(filename):
    """Load questions from JSON file"""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def get_user_choice():
    """Ask user which question number to start with"""
    try:
        choice = input(
            "Welche Frage soll als erste gestellt werden? (Standard: 1, 0 fuer alle 45 Fragen): "
        ).strip()
        if choice == "":
            return 1
        return int(choice)
    except ValueError:
        print("Invalid input. Using question #1.")
        return 1


def calculate_average_amount(rounds):
    """Calculate average final amount from rounds"""
    if not rounds:
        return "0€"

    amount_mapping = {
        "0€": 0,
        "50€": 50,
        "100€": 100,
        "200€": 200,
        "300€": 300,
        "500€": 500,
        "1.000€": 1000,
        "2.000€": 2000,
        "4.000€": 4000,
        "8.000€": 8000,
        "16.000€": 16000,
        "32.000€": 32000,
        "64.000€": 64000,
        "125.000€": 125000,
        "500.000€": 500000,
        "1.000.000€": 1000000,
    }

    total = sum(amount_mapping[round_data["final_amount"]] for round_data in rounds)
    average = total / len(rounds)

    if average >= 1000000:
        return f"{average:,.1f}€".replace(",", ".")
    elif average >= 1000:
        return f"{average:,.0f}€".replace(",", ".")
    else:
        return f"{int(average)}€"

def play_single_game(questions, start_question=1, silent=False):
    """Play a single game with one question"""
    current_level = 1
    question_number = start_question
    correct_answers = 0
    
    if not silent:
        print(f"Starte das Spiel mit Frage #{question_number}")
        print("=" * 50)
    while current_level <= 15:
        if str(current_level) not in questions:
            print(f"Error: No questions for level {current_level}")
            break

        level_questions = questions[str(current_level)]

        if question_number > len(level_questions):
            print(
                f"Fehler: Frage #{question_number} existiert nicht im Level {current_level}"
            )
            break

        question_data = level_questions[question_number - 1]
        question_text = question_data[0]
        options = question_data[1:5]
        correct_answer = question_data[5]
        
        if not silent:
            print(f"\nLevel {current_level} - {PRIZE_AMOUNTS[current_level]}")
            print(f"Frage #{question_number}: {question_text}")
            print(f"A: {options[0]}")
            print(f"B: {options[1]}")
            print(f"C: {options[2]}")
            print(f"D: {options[3]}")
        
        prompt = format_question(question_data)
        
        if not silent:
            print("\nWarte auf Antwort des KI-Modells...")
        start_time = time.time()
        llm_answer = get_llm_response(prompt, SYSTEM_PROMPT, MODEL_NAME)
        response_time = time.time() - start_time
        
        if not silent:
            print(f"KI-Modell Antwort: {llm_answer} (in {response_time:.2f} Sekunden)")
        correct_options = options
        try:
            correct_index = correct_options.index(correct_answer)
            correct_letter = ["A", "B", "C", "D"][correct_index]
        except ValueError:
            print(
                f"Fehler: Korrekte Antwort '{correct_answer}' nicht in den Optionen gefunden"
            )
            break

        if not silent:
            print(f"Richtige Antwort: {correct_letter} ({correct_answer})")

        if llm_answer == correct_letter:
            if not silent:
                print("✓ Correct!")
            correct_answers += 1
            current_level += 1
        else:
            if not silent:
                print(f"✗ Wrong! (AI said {llm_answer}, correct was {correct_letter})")
            break
    
    if not silent:
        print("\n" + "=" * 50)
        print("SPIEL BEENDET")
        print("=" * 50)
        print(f"Fragen richtig beantwortet: {correct_answers}/15")
        if correct_answers > 0:
            print(f"Letzte erreichte Preisstufe: {PRIZE_AMOUNTS[correct_answers]}")
        else:
            print("Keine Preisstufe erreicht")
    return {
        "start_question": start_question,
        "correct_answers": correct_answers,
        "final_amount": PRIZE_AMOUNTS[correct_answers] if correct_answers > 0 else "0€",
    }


def play_all_games(questions):
    """Play all 45 questions with configurable concurrency"""
    results = []
    
    if CONCURRENCY_LEVEL > 1:
        print(f"Starte alle 45 Runden mit Parallelität: {CONCURRENCY_LEVEL}")
    else:
        print("Starte alle 45 Fragen nacheinander...")
    print("=" * 50)
    
    if CONCURRENCY_LEVEL == 1:
        # Sequential execution (original behavior)
        for question_num in range(1, 46):
            print(f"\nFRAGE {question_num}/45")
            print("-" * 30)
            
            result = play_single_game(questions, question_num)
            result["question_number"] = question_num
            results.append(result)
            
            print("\n" + "=" * 50)
            print("KONTEXT GELÖSCHT - NEUES SPIEL")
            print("=" * 50)
    else:
        # Concurrent execution using thread pool
        def run_game(q_num):
            res = play_single_game(questions, q_num, silent=True)  # Silent mode for concurrent
            res["question_number"] = q_num
            return res
        
        with ThreadPoolExecutor(max_workers=CONCURRENCY_LEVEL) as executor:
            # Submit all tasks
            futures = {executor.submit(run_game, num): num for num in range(1, 46)}
            
            # Collect results as they complete
            completed_count = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    print(f"[Runde {result['question_number']:2d}/45] Abgeschlossen - Level {result['correct_answers']:2d} - Gewonnen {result['final_amount']:>10s} ({completed_count}/45 fertig)")
                except Exception as e:
                    q_num = futures[future]
                    completed_count += 1
                    print(f"[Runde {q_num:2d}/45] Fehler: {e} ({completed_count}/45 fertig)")
                    results.append({
                        "question_number": q_num,
                        "start_question": q_num,
                        "correct_answers": 0,
                        "final_amount": "0€"
                    })
        
        # Sort results to maintain order
        results.sort(key=lambda x: x["question_number"])
    
    correct_count = sum(1 for r in results if r["correct_answers"] > 0)
    print(f"\nZUSAMMENFASSUNG: {correct_count}/45 Fragen richtig beantwortet")
    return results


def format_question(question_data):
    """Format question and options for LLM"""
    question = question_data[0]
    options = question_data[1:5]
    return f"{question}\nA: {options[0]}\nB: {options[1]}\nC: {options[2]}\nD: {options[3]}"


def parse_model_response(response_text):
    """Parse model response to extract the final answer, prioritizing JSON format."""
    response = response_text.strip()

    # Primary: Parse clean JSON response (most common with structured output)
    try:
        json_data = json.loads(response)
        if isinstance(json_data, dict) and "answer" in json_data:
            answer = json_data["answer"]
            if isinstance(answer, str) and answer.upper() in ["A", "B", "C", "D"]:
                return answer.upper()
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    # Secondary: Extract JSON from mixed content
    json_pattern = r'\{[^{}]*"answer"[^{}]*\}'
    json_matches = re.findall(json_pattern, response, re.IGNORECASE)
    for json_match in json_matches:
        try:
            json_data = json.loads(json_match)
            if isinstance(json_data, dict) and "answer" in json_data:
                answer = json_data["answer"]
                if isinstance(answer, str) and answer.upper() in ["A", "B", "C", "D"]:
                    return answer.upper()
        except json.JSONDecodeError:
            continue

    # Fallback: Direct letter or natural language patterns
    if response.upper() in ["A", "B", "C", "D"]:
        return response.upper()

    # Pattern matching for natural language responses
    answer_patterns = [
        r"(?:answer|antwort)(?:\s*is\s*|\s*:\s*)([A-D])",
        r"(?:therefore|daher|deshalb|somit).*?([A-D])(?:\s|$|\.)",
        r"(?:^|\s)([A-D])(?:\s|$|\.)",
    ]

    for pattern in answer_patterns:
        matches = re.findall(pattern, response, re.IGNORECASE)
        if matches:
            return matches[-1].upper()

    # Last resort: find any valid letter
    valid_letters = [char.upper() for char in response if char.upper() in ["A", "B", "C", "D"]]
    if valid_letters:
        return valid_letters[-1]

    print(f"Warnung: Unerwartetes Antwortformat erhalten: '{response}'")
    return "INVALID"


def get_llm_response(prompt, system_prompt, model_name):
    """Send prompt to LLM and get response"""
    try:
        if USE_TWO_PHASE_REASONING:
            return get_two_phase_response(prompt, model_name)
        else:
            return get_single_phase_response(prompt, system_prompt, model_name)
    except Exception as e:
        print(f"Error in request: {e}")
        return "ERROR"


def get_single_phase_response(prompt, system_prompt, model_name):
    """Single-phase response for regular models"""
    # Prepare headers with API key if provided
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY and LLM_API_KEY != "None" and LLM_API_KEY != "":
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "temperature": TEMPERATURE,
        "top_k": TOP_K,
        "top_p": TOP_P,
        "min_p": MIN_P,
    }

    # Add structured output support
    try:
        data["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "answer_choice", "schema": ANSWER_SCHEMA},
        }
    except:
        pass
    
    try:
        response = requests.post(LLM_SERVER_URL, json=data, headers=headers, timeout=SINGLE_PHASE_TIMEOUT)
        
        if response.status_code == 200:
            response_json = response.json()
            result = response_json["choices"][0]["message"]["content"].strip()
            parsed_answer = parse_model_response(result)
            return parsed_answer
        else:
            print(f"Fehler: Server antwortete mit Status {response.status_code}")
            return "ERROR"
    except requests.exceptions.ConnectTimeout:
        print("Fehler: Verbindung zum Server timeout")
        return "ERROR"
    except requests.exceptions.ConnectionError:
        print("Fehler: Kann nicht zum Server verbinden")
        return "ERROR"
    except Exception as e:
        print(f"Fehler bei der Anfrage: {e}")
        return "ERROR"


def get_two_phase_response(prompt, model_name):
    """Two-phase response for thinking models"""
    # Prepare headers with API key if provided
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY and LLM_API_KEY != "None" and LLM_API_KEY != "":
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    
    print("Phase 1: Denken und Analysieren...")

    reasoning_data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "temperature": TEMPERATURE,
        "top_k": TOP_K,
        "top_p": TOP_P,
        "min_p": MIN_P,
    }

    reasoning_response = requests.post(
        LLM_SERVER_URL, json=reasoning_data, headers=headers, timeout=REASONING_PHASE_TIMEOUT
    )
    if reasoning_response.status_code != 200:
        print(
            f"Fehler in Phase 1: Server antwortete mit Status {reasoning_response.status_code}"
        )
        return "ERROR"

    reasoning_result = reasoning_response.json()["choices"][0]["message"][
        "content"
    ].strip()
    print(f"Phase 1 abgeschlossen ({len(reasoning_result)} Zeichen)")

    print("Phase 2: Strukturierte Antwort...")

    answer_prompt = f"""Basierend auf der folgenden Analyse der Frage:

FRAGE: {prompt}

ANALYSE: {reasoning_result}

Waehle jetzt die finale Antwort."""

    answer_data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": answer_prompt},
        ],
        "stream": False,
        "temperature": 0.1,  # Lower temperature for structured output
        "top_k": TOP_K,
        "top_p": TOP_P,
        "min_p": MIN_P,
    }

    try:
        answer_data["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "answer_choice", "schema": ANSWER_SCHEMA},
        }
    except:
        pass

    answer_response = requests.post(LLM_SERVER_URL, json=answer_data, headers=headers, timeout=SINGLE_PHASE_TIMEOUT)
    if answer_response.status_code != 200:
        print(
            f"Fehler in Phase 2: Server antwortete mit Status {answer_response.status_code}"
        )
        return "ERROR"

    answer_result = answer_response.json()["choices"][0]["message"]["content"].strip()
    print("Phase 2 abgeschlossen")

    parsed_answer = parse_model_response(answer_result)
    return parsed_answer


def load_model_results(model_name):
    """Load existing results for a model"""
    safe_model_name = model_name.replace("/", "-")
    result_filename = f"result_{safe_model_name}.json"

    try:
        with open(result_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "model_parameters" not in data:
                data["model_parameters"] = {
                    "temperature": TEMPERATURE,
                    "top_k": TOP_K,
                    "top_p": TOP_P,
                    "min_p": MIN_P,
                }
            else:
                data["model_parameters"] = {
                    "temperature": TEMPERATURE,
                    "top_k": TOP_K,
                    "top_p": TOP_P,
                    "min_p": MIN_P,
                }
            if "total_parameters" not in data:
                data["total_parameters"] = TOTAL_PARAMETERS
            if "active_parameters" not in data:
                data["active_parameters"] = ACTIVE_PARAMETERS
            return data, result_filename
    except FileNotFoundError:
        initial_data = {
            "model": model_name,
            "model_parameters": {
                "temperature": TEMPERATURE,
                "top_k": TOP_K,
                "top_p": TOP_P,
                "min_p": MIN_P,
            },
            "total_parameters": TOTAL_PARAMETERS,
            "active_parameters": ACTIVE_PARAMETERS,
            "rounds": [],
        }
        return initial_data, result_filename


def save_model_results(results_data, filename):
    """Save model results to file"""
    # Sort rounds by start_question before saving
    if "rounds" in results_data:
        results_data["rounds"].sort(key=lambda x: x["start_question"])

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)


def calculate_average_correctness_percentage(rounds):
    """Calculate average correctness percentage from rounds"""
    if not rounds:
        return 0.0

    total_questions = sum(
        round_data["correct_answers"] + 1 if round_data["correct_answers"] < 15 else 15
        for round_data in rounds
    )
    total_correct = sum(round_data["correct_answers"] for round_data in rounds)

    if total_questions == 0:
        return 0.0

    return round((total_correct / total_questions) * 100, 2)


def play_game(questions, start_question=1):
    """Main game loop - handles both single question and all 45 questions"""
    if start_question == 0:
        # Play all 45 questions
        game_results = play_all_games(questions)
    else:
        # Play single game
        single_result = play_single_game(questions, start_question)
        game_results = [single_result]

    results_data, result_filename = load_model_results(MODEL_NAME)

    if start_question == 0:
        pass
    else:
        results_data["rounds"] = [
            r
            for r in results_data["rounds"]
            if r.get("start_question") != start_question
            or r.get("question_number") is not None
        ]

    for i, result in enumerate(game_results):
        round_data = {
            "start_question": result["start_question"],
            "correct_answers": result["correct_answers"],
            "final_amount": result["final_amount"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        if start_question == 0:
            round_data["question_number"] = result["question_number"]

        results_data["rounds"].append(round_data)

    results_data["rounds"].sort(key=lambda x: x["start_question"])
    
    # Calculate and add average final amount and correctness percentage
    results_data["average_final_amount"] = calculate_average_amount(results_data["rounds"])
    results_data["average_correctness_percentage"] = calculate_average_correctness_percentage(results_data["rounds"])
    
    # Count million wins (questions with 15 correct answers)
    million_wins = sum(1 for r in results_data["rounds"] if r["correct_answers"] == 15)
    
    # Save updated results
    save_model_results(results_data, result_filename)
    
    # Improved summary display
    print(f"Millionärs-Gewinne: {million_wins}")
    print(f"Ergebnis gespeichert in: {result_filename}")
    print(f"Durchschnittlicher Gewinn: {results_data['average_final_amount']}")
    print(f"Durchschnittliche Korrektheit: {results_data['average_correctness_percentage']}%")
    print(f"Parameter: T:{TEMPERATURE}, K:{TOP_K}, P:{TOP_P}, Min:{MIN_P}")
    return game_results


def main():
    """Main function"""
    print("Who Wants to Be a Millionaire - LLM Benchmark")
    print("=" * 50)

    print(f"Modell: {MODEL_NAME}")
    print(f"Server: {LLM_SERVER_URL}")
    print(f"Zwei-Phasen-Reasoning: {USE_TWO_PHASE_REASONING}")
    print(f"Parallelität: {CONCURRENCY_LEVEL}")
    print("-" * 50)
    
    try:
        questions = load_questions("fragen_antworten.json")
        print(f"Fragen geladen: {len(questions)} Level")
    except Exception as e:
        print(f"Fehler beim Laden der Fragen: {e}")
        return

    start_question = get_user_choice()

    result = play_game(questions, start_question)
    
    print("\nDanke fuers Spielen!")


if __name__ == "__main__":
    main()
