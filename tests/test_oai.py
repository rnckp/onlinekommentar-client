"""Validate optional OAI parsing without exposing upstream error text."""

import pytest

from onlinekommentar import OAIProtocolError, parse_oai_response


def test_parser_returns_successful_namespaced_response() -> None:
    root = parse_oai_response(
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><Identify /></OAI-PMH>'
    )
    assert root.tag == "{http://www.openarchives.org/OAI/2.0/}OAI-PMH"


def test_protocol_error_reports_codes_without_server_text() -> None:
    with pytest.raises(OAIProtocolError) as error:
        parse_oai_response(
            '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
            '<error code="badResumptionToken">sensitive server text</error>'
            '<error code="private-value">more sensitive text</error></OAI-PMH>'
        )
    assert error.value.codes == ("badResumptionToken", "unknown")
    assert "sensitive" not in str(error.value)
    assert "private-value" not in str(error.value)


@pytest.mark.parametrize(
    "xml",
    [
        "not XML",
        "<html />",
        "<OAI-PMH />",
        '<!DOCTYPE OAI-PMH [<!ENTITY x "expanded">]>'
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">&x;</OAI-PMH>',
    ],
)
def test_parser_rejects_invalid_or_unsafe_xml(xml: str) -> None:
    with pytest.raises(ValueError):
        parse_oai_response(xml)
