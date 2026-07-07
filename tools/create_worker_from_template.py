import argparse
import sys

from template_utils import TemplateCreationError, create_component


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cria um worker a partir do template da CCI."
    )
    parser.add_argument("name", help="Nome do worker em kebab-case")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescreve explicitamente um destino existente.",
    )
    args = parser.parse_args()

    try:
        destination = create_component(
            template_name="python-worker-template",
            destination_group="workers",
            component_name=args.name,
            name_placeholder="{{WORKER_NAME}}",
            force=args.force,
        )
    except TemplateCreationError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Worker criado em: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
