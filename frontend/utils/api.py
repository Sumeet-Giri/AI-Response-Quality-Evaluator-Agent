import requests


BASE_URL = "http://127.0.0.1:8000"


# ==================================================
# SINGLE RESPONSE EVALUATION
# ==================================================

def evaluate_response(question, ai_response, reference_answer):

    payload = {
        "question": question,
        "response": ai_response,
        "reference_answer": reference_answer
    }

    try:

        response = requests.post(
            f"{BASE_URL}/evaluate/all",
            json=payload
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        return {"error": str(e)}


# ==================================================
# BENCHMARK VALIDATION APIs
# ==================================================

def validate_relevance():

    try:

        response = requests.get(
            f"{BASE_URL}/validation/relevance"
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        return {"error": str(e)}


def validate_accuracy():

    try:

        response = requests.get(
            f"{BASE_URL}/validation/accuracy"
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        return {"error": str(e)}


def validate_hallucination():

    try:

        response = requests.get(
            f"{BASE_URL}/validation/hallucination"
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        return {"error": str(e)}


def validate_all():

    try:

        response = requests.get(
            f"{BASE_URL}/validation/all"
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        return {"error": str(e)}