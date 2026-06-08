from pydantic import BaseModel, Field


class VentasCapRaw(BaseModel):
    """Registro crudo de APIVentasCap."""

    transaccionsubtipoid: int | None = None
    fecha: str | None = None
    fechacomprobante: str | None = None
    transacciontiponombre: str | None = None
    transacconsubtiponombre: str | None = None
    transaccionid: int | None = None
    docnroint: str | None = None
    comprobante: str | None = None
    comprobanteadicional: str | None = None
    numerocontrato: str | None = None
    dimensionvalor: str | None = None
    totalbruto: float | None = None
    totalconceptos: float | None = None
    total: float | None = None
    cliente: str | None = None
    descripcion: str | None = None
    condicionpago: str | None = None
    moneda: str | None = None
    cotizacion: float | None = None
    listaprecio: str | None = None
    vendedor: str | None = None
    producto: str | None = None
    peso: float | None = None
    envase: float | None = None
    descitem: str | None = None
    cantidad: float | None = None
    cantidadpendiente: float | None = None
    cantidadstock2: float | None = None
    unidadventa: str | None = None
    unidadcompra: str | None = None
    unidadstock: str | None = None
    unidadstock2: str | None = None
    precio: float | None = None
    fob: float | None = None
    totalfob: float | None = None
    corredor: str | None = None
    porcentaje: float | None = Field(None, alias="%")
    comisioncorredor: float | None = None
    flete: float | None = None
    totalflete: float | None = None
    seguro: float | None = None
    aforo: float | None = None
    fobkg: float | None = None
    fob18kg: float | None = None
    kg18: float | None = Field(None, alias="18KG")
    incoterm: str | None = None
    preciomonprincipal: float | None = None
    preciomonsecundaria: float | None = None
    importemonprincipal: float | None = None
    importemonsecundaria: float | None = None
    depositoorigen: str | None = None
    depositodestino: str | None = None
    preciosobre: str | None = None
    importe: float | None = None
    gravado: float | None = None
    no_gravado: float | None = Field(None, alias="NO GRAVADO")
    proveedor: str | None = None
    partida: str | None = None
    estado: str | None = None
    codigoprod: str | None = None
    pendienteorigen: float | None = None
    pendientedestino: float | None = None
    importependienteorigen: float | None = None
    importependientedestino: float | None = None
    organizacion: str | None = None
    codigoalternativo: str | None = None
    cuenta: str | None = None
    empresa: str | None = None
    ano: str | None = None
    ano_mes: str | None = Field(None, alias="ANO-MES")
    productorama1: str | None = None
    productorama2: str | None = None
    productorama3: str | None = None
    productoraman: str | None = None
    porcentajeimpositivo: float | None = None
    clasevo: str | None = Field(None, alias="@@CLASEVO")
    fechaproximopaso: str | None = None
    semanacargadesde: int | None = None
    semanacargahasta: int | None = None
    provinciadestino: str | None = None
    provinciaorigen: str | None = None
    coordenadas: str | None = None
    buque: str | None = None
    cobrado: float | None = None
    aplicado: float | None = None
    nc: float | None = None
    cobradoaplicado: float | None = None
    pendientecobro: float | None = None
    sinaplicar: float | None = None
    especie: str | None = None
    puertodestino: str | None = None
    eta: str | None = None
    cobradoapli18kg: float | None = None
    etd: str | None = None
    pendiente: int | None = None
    fobstd18nc: float | None = None
    paisdestino: str | None = None
    puertoorigen: str | None = None
    fob18kgmonsecundaria: float | None = None
    totalfletemonsec: float | None = None
    cobradomonsec: float | None = None
    semanaeta: str | None = None
    pallets: int | None = None
    nc_cantidad: float | None = Field(None, alias="NC-CANTIDAD")
    nc_monsec: float | None = Field(None, alias="NC-MONSEC")
    tipocambio: float | None = None
    reembolso: float | None = None
    cobradoaplicadomonsec: float | None = None
    familia: str | None = None
    sector: str | None = None

    model_config = {"populate_by_name": True}


class FacturacionRaw(BaseModel):
    """Registro crudo de APIAnalisisFacturacion."""

    transaccionsubtipoid: int | None = None
    fecha: str | None = None
    fechacomprobante: str | None = None
    transacciontiponombre: str | None = None
    transacconsubtiponombre: str | None = None
    transaccionid: int | None = None
    docnroint: str | None = None
    comprobante: str | None = None
    comprobanteadicional: str | None = None
    numerocontrato: str | None = None
    dimensionvalor: str | None = None
    totalbruto: float | None = None
    totalconceptos: float | None = None
    total: float | None = None
    cliente: str | None = None
    descripcion: str | None = None
    condicionpago: str | None = None
    moneda: str | None = None
    cotizacion: float | None = None
    listaprecio: str | None = None
    vendedor: str | None = None
    producto: str | None = None
    marca: str | None = None
    descitem: str | None = None
    cantidad: float | None = None
    cantidadstock2: float | None = None
    unidadventa: str | None = None
    unidadcompra: str | None = None
    unidadstock: str | None = None
    unidadstock2: str | None = None
    precio: float | None = None
    preciomonprincipal: float | None = None
    preciomonsecundaria: float | None = None
    importemonprincipal: float | None = None
    importemonsecundaria: float | None = None
    depositoorigen: str | None = None
    depositodestino: str | None = None
    preciosobre: str | None = None
    importe: float | None = None
    gravado: float | None = None
    no_gravado: float | None = Field(None, alias="NO GRAVADO")
    proveedor: str | None = None
    partida: str | None = None
    estado: str | None = None
    codigoprod: str | None = None
    pendienteorigen: float | None = None
    pendientedestino: float | None = None
    importependienteorigen: float | None = None
    importependientedestino: float | None = None
    organizacion: str | None = None
    codigoalternativo: str | None = None
    cuenta: str | None = None
    empresa: str | None = None
    ano: str | None = None
    ano_mes: str | None = Field(None, alias="ANO-MES")
    productorama1: str | None = None
    productorama2: str | None = None
    productorama3: str | None = None
    productoraman: str | None = None
    porcentajeimpositivo: float | None = None
    controlimpositivo3: str | None = None
    gravadoportasaimpositiva: float | None = None
    gravadoportasaimpositivamonedaprincipal: float | None = None
    clasevo: str | None = Field(None, alias="@@CLASEVO")
    fechaproximopaso: str | None = None
    semanacargadesde: int | None = None
    semanacargahasta: int | None = None
    provinciadestino: str | None = None
    provinciaorigen: str | None = None
    coordenadas: str | None = None
    corredor: str | None = None
    sucursal: str | None = None
    cai_cae: str | None = Field(None, alias="CAI/CAE")
    nivel1dimension: str | None = None
    nivel2dimension: str | None = None
    nivel1cliente: str | None = None
    nivel2cliente: str | None = None
    provinciadestinoitem: str | None = None
    percepciones: float | None = None
    subfamilia: str | None = None
    familia: str | None = None
    rubro: str | None = None
    actividadiva: str | None = None
    workflow: str | None = None
    identificacionexterna: str | None = None
    fob: float | None = None
    fobtotal: float | None = None
    incoterm: str | None = None
    pe: str | None = None
    cotizacionpe: float | None = None
    posicionarancelaria: str | None = None
    pais: str | None = None
    puertoorigen: str | None = None
    cuit: str | None = None
    usuario: str | None = None
    pedidopor: str | None = None
    fob18kg: float | None = None
    cuentacompras: str | None = None
    especie: str | None = None

    model_config = {"populate_by_name": True}


class ConsolidacionVentasIndustria(BaseModel):
    """Consolida los registros de ambas APIs."""

    ventas_cap: list[VentasCapRaw]
    analisis_fac: list[FacturacionRaw]
