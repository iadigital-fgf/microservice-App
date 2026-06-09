from pydantic import BaseModel, ConfigDict


class FinnegansBase(BaseModel):
    """
    Clase base para todos los schemas Raw de Finnegans.

    Convenciones:
    - Los campos del JSON de Finnegans vienen en MAYÚSCULA.
    - En el service siempre normalizar con: {k.lower(): v for k, v in item.items()}
    - Campos con caracteres especiales (ANO-MES, @@CLASEVO, etc.)
      se declaran con Field(alias="nombre-en-minuscula")
    - Campos con tipos inconsistentes se declaran como int | str | None
    """

    model_config = ConfigDict(populate_by_name=True)
