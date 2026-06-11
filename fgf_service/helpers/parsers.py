from pydantic import BaseModel


def parse_finnegans(items: list[dict], schema: type[BaseModel]) -> list[BaseModel]:
    """Convierte una lista de dicts de Finnegans (UPPERCASE) a objetos Pydantic."""
    return [schema.model_validate({k.lower(): v for k, v in item.items()}) for item in items]
