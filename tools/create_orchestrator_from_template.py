import argparse
import sys

from template_utils import TemplateCreationError, create_component


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cria um serviço orquestrador a partir do template da CCI."
    )
    parser.add_argument("name", help="Nome do orquestrador em kebab-case")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescreve explicitamente um destino existente.",
    )
    args = parser.parse_args()

    try:
        destination = create_component(
            template_name="fastapi-orchestrator-service-template",
            destination_group="services",
            component_name=args.name,
            name_placeholder="{{SERVICE_NAME}}",
            force=args.force,
        )
    except TemplateCreationError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Orquestrador criado em: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
