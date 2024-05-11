DOCKER_COMP = docker compose


build: ## Builds the Docker images
	@$(DOCKER_COMP) build --pull --no-cache

up: ## Start the docker hub in detached mode (no logs)
	@$(DOCKER_COMP) up --detach --watch --remove-orphans

watch:
	@$(DOCKER_COMP)  watch

start:

down:
	@$(DOCKER_COMP) down
