DOCKER_COMP = docker compose


build: ## Builds the Docker images
	@$(DOCKER_COMP) build --no-cache

up: ## Start the docker hub in detached mode (no logs)
	@$(DOCKER_COMP) up --watch --remove-orphans

start:

down:
	@$(DOCKER_COMP) down
