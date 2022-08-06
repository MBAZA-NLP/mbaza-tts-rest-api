.PHONY: help
help: ## Show this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: test
test: ## Run the tests against the current version of Python.
	pytest app

.PHONY: dep-sync
dep-sync: ## Sync venv installation with 'requirements.txt' file.
	@pip-sync

.PHONY: dep-lock
dep-lock: ## Freeze deps in 'requirements.txt' file.
	@pip-compile requirements.in -o requirements.txt


.PHONY: run-docker-eng-cpu
run-docker-eng-cpu: ## Run the app in a docker container.
	docker-compose -f docker-compose-eng-cpu.yml up -d

.PHONY: run-docker-eng-gpu
run-docker-eng-gpu: ## Run the app in a docker container with GPU support.
	docker-compose -f docker-compose-eng-gpu.yml up -d

.PHONY: kill-docker-eng-cpu
kill-docker-eng-cpu: ## Stop the running docker container.
	docker-compose -f docker-compose-eng-cpu.yml down

.PHONY: kill-docker-eng-gpu
kill-docker-eng-gpu: ## Stop the running docker container with GPU support.
	docker-compose -f docker-compose-eng-gpu.yml down


.PHONY: run-docker-kin-cpu
run-docker-kin-cpu: ## Run the app in a docker container.
	docker-compose -f docker-compose-kin-cpu.yml up -d

.PHONY: run-docker-kin-gpu
run-docker-kin-gpu: ## Run the app in a docker container with GPU support.
	docker-compose -f docker-compose-kin-gpu.yml up -d

.PHONY: kill-docker-kin-cpu
kill-docker-kin-cpu: ## Stop the running docker container.
	docker-compose -f docker-compose-kin-cpu.yml down

.PHONY: kill-docker-kin-gpu
kill-docker-kin-gpu: ## Stop the running docker container with GPU support.
	docker-compose -f docker-compose-kin-gpu.yml down


.PHONY: run-local
run-local: ## Run the app locally.
	export $(cat .env | xargs) && export APP_LOCAL_RUN=true && cd .. && uvicorn tts.app.main:app --port 6969 --reload
