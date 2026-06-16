from pydantic import Field

from fgf_service.core.base_schemas import FinnegansBase


class APIVentasCapRaw(FinnegansBase):
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
    kg18: float | None = Field(None, alias="18kg")
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
    no_gravado: float | None = Field(None, alias="no gravado")
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
    ano_mes: str | None = Field(None, alias="ano-mes")
    productorama1: str | None = None
    productorama2: str | None = None
    productorama3: str | None = None
    productoraman: str | None = None
    porcentajeimpositivo: float | None = None
    clasevo: str | None = Field(None, alias="@@clasevo")
    fechaproximopaso: str | None = None
    semanacargadesde: int | str | None = None
    semanacargahasta: int | str | None = None
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
    nc_cantidad: float | None = Field(None, alias="nc-cantidad")
    nc_monsec: float | None = Field(None, alias="nc-monsec")
    tipocambio: float | None = None
    reembolso: float | None = None
    cobradoaplicadomonsec: float | None = None
    familia: str | None = None
    sector: str | None = None

class APIAnalisisFacturacionRaw(FinnegansBase):
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
    no_gravado: float | None = Field(None, alias="no gravado")
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
    ano_mes: str | None = Field(None, alias="ano-mes")
    productorama1: str | None = None
    productorama2: str | None = None
    productorama3: str | None = None
    productoraman: str | None = None
    porcentajeimpositivo: float | None = None
    controlimpositivo3: str | None = None
    gravadoportasaimpositiva: float | None = None
    gravadoportasaimpositivamonedaprincipal: float | None = None
    clasevo: str | None = Field(None, alias="@@clasevo")
    fechaproximopaso: str | None = None
    semanacargadesde: int | str | None = None
    semanacargahasta: int | str | None = None
    provinciadestino: str | None = None
    provinciaorigen: str | None = None
    coordenadas: str | None = None
    corredor: str | None = None
    sucursal: str | None = None
    cai_cae: str | None = Field(None, alias="cai/cae")
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

class APIAnalisisLaboratorioRaw(FinnegansBase):
    """Registro crudo de APIAnalisisLaboratorio."""

    analisisid: int | None = None
    lote: str | None = None
    cod_ana: str | None = None
    cod_finn: str | None = None
    nombre: str | None = None
    valor: str | None = None
    item: str | None = None
    productoid: int | None = None
    productofinn: str | None = None
    familia: str | None = None

class APIStockProdIndustriaRaw(FinnegansBase):
    """Registro crudo de APIStockProdIndustria."""

    producto: str | None = None
    productocodigo: str | None = None
    deposito: str | None = None
    cantidad1: float | None = None
    unidad1: str | None = None
    cantidad2: float | None = None
    unidad2: str | None = None
    lugar: str | None = None
    relacioncantidades: float | None = None
    partida: str | None = None
    partida_alta: str | None = None
    organizacion: str | None = None
    marca: str | None = None
    subfamilia: str | None = None
    familia: str | None = None
    especie: str | None = None
    categoria: str | None = None
    pais: str | None = None
    produccion: str | None = None
    factorexp: float | None = None
    estadocalidad: str | None = None
    estadocomex: str | None = None

class ConsolidacionVentasIndustria(FinnegansBase):
    """Consolida los registros de todas las APIs del reporte ventas industria."""

    # Mercado Externo — APIVentasCap (una sola llamada, sin empresa)
    ventas_cap: list[APIVentasCapRaw]

    # APIAnalisisFacturacion (general sin Dohler + llamada dedicada de Dohler);
    # el mercado se decide por tipo de documento en detalle.py
    facturacion: list[APIAnalisisFacturacionRaw]

    # Laboratorio
    analisis_lab: list[APIAnalisisLaboratorioRaw]

    # Stock
    stock_arg: list[APIStockProdIndustriaRaw]
    stock_ext: list[APIStockProdIndustriaRaw]
    stock_dt: list[APIStockProdIndustriaRaw]
