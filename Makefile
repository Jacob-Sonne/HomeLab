# Homelab Makefile

network:
	@docker netowrk inspect $(NETWORK) >/dev/null 2>&1 || \
	docker netowrk create $(NETWORK)
	@echo "Network $(NETWORK) ready"