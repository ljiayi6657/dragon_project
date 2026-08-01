from __future__ import annotations

import difflib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

try:
    from .parameter_map import NODE_MAP, PARAM_MAP
except ImportError:
    from parameter_map import NODE_MAP, PARAM_MAP


ROOT_TAG = "DragonConfig"


@dataclass
class XmlDoc:
    root: etree._Element
    declaration: str = ""


def calc_dimz(l_kpc: float, dz_kpc: float) -> int:
    """Calculate vertical grid points for a fixed spacing."""

    if l_kpc <= 0 or dz_kpc <= 0:
        raise ValueError("L and dz must be positive.")
    return int(round((2.0 * float(l_kpc)) / float(dz_kpc))) + 1


def calc_dz(l_kpc: float, dimz: int) -> float:
    """Calculate vertical grid spacing from L and DimZ."""

    if l_kpc <= 0 or dimz <= 1:
        raise ValueError("L must be positive and DimZ must exceed one.")
    return (2.0 * float(l_kpc)) / (int(dimz) - 1)


def format_value(value: float) -> str:
    """Format a numeric value for an XML attribute."""

    if float(value).is_integer():
        return str(int(value))
    return f"{value:.12g}"


def split_decl(text: str) -> tuple[str, str]:
    """Separate a leading XML declaration without regular expressions."""

    stripped = text.lstrip()
    offset = len(text) - len(stripped)
    if not stripped.startswith("<?xml"):
        return "", text

    end = text.find("?>", offset)
    if end < 0:
        raise ValueError("The XML declaration is not closed.")

    end += 2
    declaration = text[offset:end]
    body = text[:offset] + text[end:]
    return declaration, body


def load_xml(path: str | Path) -> XmlDoc:
    """Load a DRAGON multi-root XML file through a temporary root."""

    text = Path(path).read_text(encoding="utf-8")
    declaration, body = split_decl(text)
    wrapped = f"<{ROOT_TAG}>{body}</{ROOT_TAG}>"
    parser = etree.XMLParser(
        remove_blank_text=False,
        remove_comments=False,
        resolve_entities=False,
        strip_cdata=False,
    )
    root = etree.fromstring(wrapped.encode("utf-8"), parser=parser)
    return XmlDoc(root=root, declaration=declaration)


def render_xml(doc: XmlDoc) -> str:
    """Serialize child nodes without the temporary root."""

    body = doc.root.text or ""
    for node in doc.root:
        body += etree.tostring(node, encoding="unicode", with_tail=True)
    return doc.declaration + body


def write_xml(doc: XmlDoc, path: str | Path) -> str:
    """Write one modified DRAGON XML document and return its text."""

    text = render_xml(doc)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return text


def find_nodes(doc: XmlDoc, xpath: str) -> list[etree._Element]:
    """Select element nodes through XPath."""

    result = doc.root.xpath(xpath)
    if any(not isinstance(node, etree._Element) for node in result):
        raise TypeError(f"XPath must select elements: {xpath}")
    return list(result)


def find_one(doc: XmlDoc, xpath: str) -> etree._Element:
    """Select exactly one element through XPath."""

    nodes = find_nodes(doc, xpath)
    if len(nodes) != 1:
        raise ValueError(f"Expected one node for {xpath}, found {len(nodes)}.")
    return nodes[0]


def get_param(
    doc: XmlDoc,
    name: str,
    param_map: Mapping[str, str] = PARAM_MAP,
) -> str:
    """Read one mapped value attribute."""

    xpath = param_map.get(name)
    if xpath is None:
        raise KeyError(f"No XPath is configured for parameter: {name}")
    node = find_one(doc, xpath)
    value = node.get("value")
    if value is None:
        raise ValueError(f"Node has no value attribute: {xpath}")
    return value


def set_param(
    doc: XmlDoc,
    name: str,
    value: object,
    param_map: Mapping[str, str] = PARAM_MAP,
) -> None:
    """Set one mapped value attribute."""

    xpath = param_map.get(name)
    if xpath is None:
        raise KeyError(f"No XPath is configured for parameter: {name}")

    node = find_one(doc, xpath)
    node.set("value", str(value))


def apply_params(
    doc: XmlDoc,
    params: Mapping[str, object],
    param_map: Mapping[str, str] = PARAM_MAP,
    strict: bool = True,
) -> list[str]:
    """Apply mapped parameter values."""

    changed = []
    for name, value in params.items():
        if name not in param_map:
            if strict:
                raise KeyError(f"No XPath is configured for parameter: {name}")
            continue
        set_param(doc, name, value, param_map)
        changed.append(name)
    return changed


def remove_nodes(
    doc: XmlDoc,
    names: Sequence[str],
    node_map: Mapping[str, str] = NODE_MAP,
    strict: bool = True,
) -> dict[str, int]:
    """Remove configured nodes through XPath."""

    removed = {}
    for name in names:
        xpath = node_map.get(name)
        if xpath is None:
            if strict:
                raise KeyError(f"No XPath is configured for node: {name}")
            continue
        nodes = find_nodes(doc, xpath)
        if strict and len(nodes) != 1:
            raise ValueError(f"Expected one node for {xpath}, found {len(nodes)}.")
        removed[name] = len(nodes)
        for node in nodes:
            parent = node.getparent()
            if parent is None:
                raise ValueError(f"Cannot remove a root node: {xpath}")
            tail = node.tail
            previous = node.getprevious()
            parent.remove(node)
            if tail:
                if previous is None:
                    parent.text = (parent.text or "") + tail
                else:
                    previous.tail = (previous.tail or "") + tail
    return removed


def make_diff(
    before: str,
    after: str,
    source: str | Path,
    output: str | Path,
) -> str:
    """Create a unified diff for the generated XML."""

    lines = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=str(source),
        tofile=str(output),
        lineterm="",
    )
    text = "\n".join(lines)
    return text + ("\n" if text else "")


def modify_xml(
    template: str | Path,
    params: Mapping[str, object],
    output: str | Path,
    diff: str | Path | None = None,
    drops: Sequence[str] = (),
    param_map: Mapping[str, str] = PARAM_MAP,
    strict: bool = True,
) -> dict[str, object]:
    """Modify mapped values with XPath while retaining output and diff logic."""

    source = Path(template)
    target = Path(output)
    doc = load_xml(source)
    before = render_xml(doc)
    changed = apply_params(doc, params, param_map, strict)
    removed = remove_nodes(doc, drops, strict=strict) if drops else {}
    after = write_xml(doc, target)

    diff_path = None
    if diff is not None:
        diff_path = Path(diff)
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        diff_path.write_text(
            make_diff(before, after, source, target),
            encoding="utf-8",
        )

    return {
        "output": target,
        "diff": diff_path,
        "changed": changed,
        "removed": removed,
    }
