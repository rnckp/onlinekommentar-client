"""Optional OAI-PMH XML validation and safe protocol error reporting."""

import re
from xml.etree import ElementTree as ET

_NAMESPACE = "http://www.openarchives.org/OAI/2.0/"
_ERROR_CODES = frozenset(
    {
        "badArgument",
        "badResumptionToken",
        "badVerb",
        "cannotDisseminateFormat",
        "idDoesNotExist",
        "noRecordsMatch",
        "noMetadataFormats",
        "noSetHierarchy",
    }
)


class OAIProtocolError(ValueError):
    """An HTTP-successful OAI-PMH response contains protocol errors.

    Attributes:
        codes: Standard error codes; unrecognized codes are replaced with 'unknown'.
    """

    def __init__(self, codes: tuple[str, ...]) -> None:
        self.codes = tuple(code if code in _ERROR_CODES else "unknown" for code in codes)
        super().__init__(f"OAI-PMH protocol error: {', '.join(self.codes)}")


def parse_oai_response(xml: str) -> ET.Element:
    """Validate an OAI-PMH response and return its XML root.

    Args:
        xml: XML text returned by an OAI method.

    Raises:
        ValueError: XML is malformed, declares a DTD/entity, or has an unexpected root.
        OAIProtocolError: The response contains protocol-level errors.
    """
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", xml, flags=re.IGNORECASE):
        raise ValueError("OAI-PMH XML must not declare DTDs or entities")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as error:
        raise ValueError("Malformed OAI-PMH XML") from error
    if root.tag != f"{{{_NAMESPACE}}}OAI-PMH":
        raise ValueError("Unexpected OAI-PMH XML root")
    errors = root.findall(f"{{{_NAMESPACE}}}error")
    if errors:
        raise OAIProtocolError(tuple(error.get("code", "unknown") for error in errors))
    return root
