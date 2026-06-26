# Makefile para comandos rápidos

.PHONY: help build up down restart logs shell install-kernel update-kernel clean

help:
	@echo "Comandos disponibles:"
	@echo "  make build          - Reconstruir la imagen Docker"
	@echo "  make up             - Iniciar los servicios"
	@echo "  make down           - Detener los servicios"
	@echo "  make restart        - Reiniciar Jupyter Lab"
	@echo "  make logs           - Ver logs de Jupyter"
	@echo "  make shell          - Entrar al contenedor"
	@echo "  make install-kernel - Instalar el kernel Scala"
	@echo "  make update-kernel  - Actualizar la configuración del kernel"
	@echo "  make clean          - Limpiar todo"

build:
	docker compose build --no-cache

up:
	docker compose up -d
	@echo "✅ Servicios iniciados en http://localhost:8888"

down:
	docker compose down

restart:
	docker compose restart spark-scala-notebook
	@echo "✅ Jupyter reiniciado"

logs:
	docker compose logs -f spark-scala-notebook

shell:
	docker exec -it spark-scala-practicas /bin/bash

install-kernel:
	./scripts/install_kernel.sh

update-kernel:
	./scripts/update_kernel.sh

clean:
	docker compose down -v
	docker system prune -f
	@echo "✅ Limpieza completada"