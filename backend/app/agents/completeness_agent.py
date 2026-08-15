from app.schemas.completeness import CompletenessResult


class CompletenessJudge:
    """
    Rule-based completeness scorer: purely keyword/pattern matching, no
    embedding model. (A prior version eagerly loaded an unused
    SentenceTransformer in __init__ -- removed; it cost a full model load
    on every single request and was never referenced anywhere in this
    class. If semantic aspect-coverage checking is added later, load the
    model the same way app/services/embedder.py does -- once, as a shared
    module-level singleton -- not per-instance.)
    """

    def __init__(self):

        self.aspect_patterns = {

            "advantages": "Advantages",
            "disadvantages": "Disadvantages",
            "types": "Types",
            "applications": "Applications",
            "features": "Features",
            "components": "Components",
            "working": "Working",
            "architecture": "Architecture",
            "steps": "Steps",
            "limitations": "Limitations",
            "benefits": "Benefits",
            "uses": "Uses",
            "phases": "Phases"

        }

    # ----------------------------------------------------
    # Aspect Extraction
    # ----------------------------------------------------

    def extract_aspects(self, question):

        question_lower = question.lower()

        aspects = []

        # Definition type question
        if "what is" in question_lower:
            aspects.append("Definition")

        # Compare question
        if "compare" in question_lower:
            aspects.append("Comparison")

        # Common patterns
        for keyword, aspect in self.aspect_patterns.items():

            if keyword in question_lower:
                aspects.append(aspect)

        # Fallback
        if not aspects:
            aspects.append("Explanation")

        return list(dict.fromkeys(aspects))

    # ----------------------------------------------------
    # Aspect Coverage Rules
    # ----------------------------------------------------

    def is_definition_present(self, response):

        keywords = [
            " is ",
            "refers to",
            "defined as",
            "can be defined as",
            "stands for",
            "means",
            "known as"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_types_present(self, response):

        keywords = [
            "types",
            "includes",
            "supervised",
            "unsupervised",
            "categories",
            "different kinds"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_applications_present(self, response):

        keywords = [
            "used in",
            "used for",
            "applications",
            "can be used",
            "utilized"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_advantages_present(self, response):

        keywords = [

            "advantages",
            "benefits",
            "provides",
            "offers",
            "improves",
            "efficient",
            "scalable",
            "flexible",
            "cost saving",
            "cost savings",
            "faster",
            "better"

        ]

        return any(
            keyword in response.lower()
            for keyword in keywords
        )

    def is_disadvantages_present(self, response):

        keywords = [

            "disadvantages",
            "limitations",
            "drawbacks",
            "cons",
            "expensive",
            "security issues",
            "complex",
            "slow",
            "problem",
            "risk"

        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_features_present(self, response):

        keywords = [
            "features",
            "characteristics",
            "easy",
            "readable",
            "flexible"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_components_present(self, response):

        keywords = [
            "components",
            "parts",
            "consists of",
            "includes",
            "contains"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_working_present(self, response):

        keywords = [
            "works by",
            "converts",
            "processes",
            "operates",
            "performs"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_architecture_present(self, response):

        keywords = [
            "architecture",
            "structure",
            "layers"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_steps_present(self, response):

        keywords = [
            "steps",
            "process",
            "procedure"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_limitations_present(self, response):

        keywords = [
            "limitations",
            "drawbacks",
            "issues"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_benefits_present(self, response):

        keywords = [
            "benefits",
            "advantages"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_uses_present(self, response):

        keywords = [
            "used for",
            "used in",
            "applications"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_phases_present(self, response):

        keywords = [
            "phases",
            "stages"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_comparison_present(self, response):

        keywords = [
            "whereas",
            "while",
            "difference",
            "unlike",
            "however"
        ]

        return any(keyword in response.lower()
                   for keyword in keywords)

    def is_explanation_present(self, response):

        return len(response.strip().split()) >= 5

    # ----------------------------------------------------
    # Coverage Detection
    # ----------------------------------------------------

    def detect_coverage(self, aspects, response):

        covered = []
        missing = []

        coverage_functions = {

            "Definition": self.is_definition_present,
            "Types": self.is_types_present,
            "Applications": self.is_applications_present,
            "Advantages": self.is_advantages_present,
            "Disadvantages": self.is_disadvantages_present,
            "Features": self.is_features_present,
            "Components": self.is_components_present,
            "Working": self.is_working_present,
            "Architecture": self.is_architecture_present,
            "Steps": self.is_steps_present,
            "Limitations": self.is_limitations_present,
            "Benefits": self.is_benefits_present,
            "Uses": self.is_uses_present,
            "Phases": self.is_phases_present,
            "Comparison": self.is_comparison_present,
            "Explanation": self.is_explanation_present

        }

        for aspect in aspects:

            checker = coverage_functions.get(aspect)

            if checker and checker(response):
                covered.append(aspect)
            else:
                missing.append(aspect)

        return covered, missing

    # ----------------------------------------------------
    # Coverage Percentage
    # ----------------------------------------------------

    def calculate_coverage(self, covered, total):

        if total == 0:
            return 0.0

        return round((covered / total) * 100, 2)

    # ----------------------------------------------------
    # Score Calculation
    # ----------------------------------------------------

    def calculate_score(self, coverage):

        if coverage >= 90:
            return 10
        elif coverage >= 80:
            return 9
        elif coverage >= 70:
            return 8
        elif coverage >= 60:
            return 7
        elif coverage >= 50:
            return 6
        elif coverage >= 40:
            return 5
        elif coverage >= 30:
            return 4
        elif coverage >= 20:
            return 3
        elif coverage >= 10:
            return 2
        elif coverage > 0:
            return 1

        return 0

    # ----------------------------------------------------
    # Reasoning Generation
    # ----------------------------------------------------

    

    def generate_reasoning(self, score, missing):

        if score >= 8:

            reasoning = (
                "The response covers almost all required aspects."
            )

        elif score >= 5:

            reasoning = (
                "The response partially addresses the question."
            )

        else:

            reasoning = (
                "The response is incomplete."
            )

        if missing:

            reasoning += (
                "\nMissing aspects: "
                + ", ".join(missing)
            )

        return reasoning

    # ----------------------------------------------------
    # Main Evaluation Function
    # ----------------------------------------------------

    def evaluate(self, question, response):

        extracted_aspects = self.extract_aspects(question)

        covered, missing = self.detect_coverage(
            extracted_aspects,
            response
        )

        coverage_percentage = self.calculate_coverage(
            len(covered),
            len(extracted_aspects)
        )

        score = self.calculate_score(
            coverage_percentage
        )

        reasoning = self.generate_reasoning(
            score,
            missing
        )

        return CompletenessResult(

            completeness_score=score,
            coverage_percentage=coverage_percentage,
            total_aspects=len(extracted_aspects),

            extracted_aspects=extracted_aspects,
            covered_aspects=covered,
            missing_aspects=missing,

            reasoning=reasoning

        )