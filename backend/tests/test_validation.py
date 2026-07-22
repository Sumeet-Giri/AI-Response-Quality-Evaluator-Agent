from validation.validator import BenchmarkValidator


validator = BenchmarkValidator()


results = validator.validate_all()


print(results)