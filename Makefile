.PHONY: generate validate checkpoint test clean freeze

# Core targets
generate:
	@echo "🔧 Generating code from contracts..."
	@python tools/generators/generate.py
	@echo "✅ Generation complete"

validate:
	@echo "🔍 Validating contracts..."
	@npx ajv compile -s 'contracts/**/*.json' --strict=true
	@python tools/validators/validate.py
	@echo "✅ Validation complete"

checkpoint:
	@echo "💾 Creating checkpoint: $(shell date +%Y%m%d-%H%M%S)"
	@git add -A
	@git commit -m "Checkpoint: $(shell date +%Y%m%d-%H%M%S)" || true
	@git tag -a "checkpoint-$(shell date +%Y%m%d-%H%M%S)" -m "Automatic checkpoint"

freeze:
	@echo "🔒 Freezing contracts at v1.0.0"
	@python tools/validators/freeze_contracts.py
	@git tag -a "contracts-v1.0.0" -m "Contracts frozen at v1.0.0"

test:
	@pytest tests/ -v
	@npm run test:contracts

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf .pytest_cache node_modules .venv