from lxml import etree
import warnings

# Ignorar avisos de SHA1 durante validação XSD
warnings.filterwarnings("ignore", message=".*SHA1.*")


def validate_xml(xml_string: str, xsd_path: str) -> tuple[bool, list | None]:
    # Configurar parser para não validar a assinatura
    parser = etree.XMLParser(
        remove_blank_text=True, 
        resolve_entities=False, 
        no_network=True,
        huge_tree=False
    )
    try:
        doc = etree.fromstring(xml_string.encode("utf-8"), parser)
    except Exception as e:
        return False, [f"XML parse error: {e}"]

    # Remover assinatura antes da validação XSD para evitar erro de SHA1
    signature_nodes = doc.xpath('//*[local-name()="Signature"]')
    for sig in signature_nodes:
        parent = sig.getparent()
        if parent is not None:
            parent.remove(sig)

    try:
        with open(xsd_path, "rb") as f:
            schema_doc = etree.parse(f)
    except Exception as e:
        return False, [f"XSD load error: {e}"]

    try:
        schema = etree.XMLSchema(schema_doc)
    except Exception as e:
        return False, [f"XSD compile error: {e}"]

    is_valid = schema.validate(doc)
    if is_valid:
        return True, None

    # Filtrar erros relacionados à falta de assinatura (esperado antes da assinatura)
    errors = []
    for error in schema.error_log:
        error_msg = str(error)
        # Ignorar erro de falta de elemento Signature (será adicionado na assinatura)
        if "Signature" in error_msg and "Missing child element" in error_msg:
            continue
        errors.append(error_msg)
    
    if not errors:
        # Se o único erro for falta de assinatura, considerar válido
        return True, None
    
    return False, errors
