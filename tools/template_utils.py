import re
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALID_COMPONENT_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TemplateCreationError(RuntimeError):
    pass


def _validate_name(name: str) -> None:
    if not VALID_COMPONENT_NAME.fullmatch(name):
        raise TemplateCreationError(
            "Use um nome em kebab-case contendo apenas letras minúsculas, números e hífens."
        )


def _prepare_destination(destination: Path, force: bool) -> None:
    if not destination.exists():
        return

    if destination.is_file():
        if not force:
            raise TemplateCreationError(f"O destino já existe: {destination}")
        destination.unlink()
        return

    if any(destination.iterdir()) and not force:
        raise TemplateCreationError(
            f"O destino existe e não está vazio: {destination}. Use --force explicitamente para sobrescrever."
        )

    if force:
        shutil.rmtree(destination)
    else:
        destination.rmdir()


def _replace_placeholders(destination: Path, replacements: dict[str, str]) -> None:
    for path in destination.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        updated = content
        for placeholder, value in replacements.items():
            updated = updated.replace(placeholder, value)

        if updated != content:
            path.write_text(updated, encoding="utf-8", newline="\n")


def create_component(
    *,
    template_name: str,
    destination_group: str,
    component_name: str,
    name_placeholder: str,
    force: bool = False,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    _validate_name(component_name)

    source = project_root / "templates" / template_name
    destination_root = project_root / destination_group
    destination = destination_root / component_name

    if not source.is_dir():
        raise TemplateCreationError(f"Template não encontrado: {source}")

    destination_root.mkdir(parents=True, exist_ok=True)
    _prepare_destination(destination, force)
    shutil.copytree(source, destination)
    _replace_placeholders(
        destination,
        {
            name_placeholder: component_name,
            "{{APP_ENV}}": "development",
        },
    )
    return destination
