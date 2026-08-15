from agents.relevance_agent import RelevanceJudgeAgent

agent = RelevanceJudgeAgent()

test_cases = [
    {
        "question": "What is the capital of France?",
        "response": "The capital of France is Paris."
    },
    {
        "question": "What are the functions of the CPU?",
        "response": "The CPU processes instructions and performs calculations."
    },
    {
        "question": "What is Machine Learning?",
        "response": "I like watching cricket on weekends."
    },
    {
        "question": "Explain the water cycle.",
        "response": "Water evaporates from the Earth's surface."
    },
    {
        "question": "What is Python programming language?",
        "response": "Python is a large non-venomous snake found in forests."
    },
    {
        "question": "What is HTTP?",
        "response": "HTTP is a protocol used for communication on the web."
    },
    {
        "question": "Explain cloud computing.",
        "response": "Cloud computing is the delivery of computing services such as storage, servers, databases, networking, and software over the internet."
    },
    {
        "question": "What is Artificial Intelligence?",
        "response": "Artificial Intelligence enables machines to simulate human intelligence. It is used in healthcare and finance. Also, the history of computers dates back several decades."
    },
    {
        "question": "What is an Operating System?",
        "response": "It is software that helps computers work properly."
    },
    {
        "question": "What is Photosynthesis?",
        "response": "Cellular respiration is the process by which cells produce energy from glucose."
    }
]


for i, test in enumerate(test_cases, start=1):

    result = agent.evaluate(
        test["question"],
        test["response"]
    )

    print(f"\nTest Case {i}")
    print(f"Question : {test['question']}")
    print(f"Response : {test['response']}")
    print(result)