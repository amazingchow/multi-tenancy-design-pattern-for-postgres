include .env
export

VERSION  := v0.1.0
GIT_HASH := $(shell git rev-parse --short HEAD)
SRC      := $(shell find . -type f -name '*.py' -not -path "./venv/*" -not -path "./.venv/*" -not -path "./migrations*/versions/*")
CURR_DIR := $(shell pwd)

.PHONY: help
help: ### Display this help screen.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: lint
lint: ### Improve your code style. (pyflakes, pycodestyle, isort)
	@echo "-> Running import sort..."
	@isort --atomic --multi-line=VERTICAL_HANGING_INDENT ${SRC}
	@echo "-> Running static code analysis..."
	@pyflakes ${SRC}
	@echo "-> Running code style check..."
	@pycodestyle ${SRC} --ignore=E101,E121,E125,E126,E128,E131,E203,E265,E266,E402,E501,E702,E712,E722,W191,W293,W503

.PHONY: local_run
local_run: lint ### Run the application locally.
	@uvicorn \
		--app-dir=. \
		--host="0.0.0.0" \
		--port=17891 \
		--workers=1 \
		--loop="uvloop" \
		--http="httptools" \
		--interface="asgi3" \
		--limit-concurrency=1024 \
		--timeout-keep-alive=300 \
		--timeout-graceful-shutdown=2 \
		app:app

.PHONY: test
test: ### Run the tests. (pytest, pytest-asyncio)
	@(export PYTHONPATH=${PYTHONPATH}:${CURR_DIR} && poetry run pytest -vv || true)

.PHONY: run_infra
run_infra: ## Run infra
	@(docker-compose -f "${CURR_DIR}/infra.yml" up -d)

.PHONY: shutdown_infra
shutdown_infra: ## Shutdown infra
	@(docker-compose -f "${CURR_DIR}/infra.yml" down)
