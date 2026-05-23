# Homelab Makefile

# Make all lines in recipes be passed to a single shell.
.ONESHELL:

# PHONY: recipes added as "PHONY" will always execute even if there is a file with the same name.
.PHONY: network clean jellyfin

# ----------------
# Variables / loading variables
# ----------------
NETWORK=homelab

# ----------------
# Recipes
# ----------------

# Create docker network if it doesn't exist.
network:
	docker network inspect $(NETWORK) >/dev/null 2>&1 || docker network create $(NETWORK)
	echo "Network $(NETWORK) ready"

# Clean up unused docker files.
clean:
	docker system prune -f

# Start the jellyfin service
jellyfin:
	docker compose -f ./docker/nginx/compose.yaml up -d
	docker compose -f ./docker/jellyfin/compose.yaml up -d

# Start the kavita service
kavita:
	docker compose -f ./docker/nginx/compose.yaml up -d
	docker compose -f ./docker/kavita/compose.yaml up -d

# Start the suwayomi service
suwayomi:
	docker compose -f ./docker/nginx/compose.yaml up -d
	docker compose -f ./docker/suwayomi/compose.yaml up -d