from lxml import etree


def validate_xml(xml_string: str, xsd_path: str) -> tuple[bool, list | None]:
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        doc = etree.fromstring(xml_string.encode("utf-8"), parser)
    except Exception as e:
        return False, [f"XML parse error: {e}"]

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

    return False, [str(e) for e in schema.error_log]