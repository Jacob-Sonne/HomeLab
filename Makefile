# Homelab Makefile
NETWORK=homelab
network:
	@docker network inspect $(NETWORK) >/dev/null 2>&1 || \
	docker network create $(NETWORK)
	@echo "Network $(NETWORK) ready"

clean:
	docker system prune -f