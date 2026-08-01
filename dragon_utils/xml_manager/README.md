# XML Manager

## Files

- `baseline.xml`: Default DRAGON template copied from `examples/test3D_vardelta.xml`.
- `parameter_map.py`: Maps public parameter names to XPath expressions. `PARAM_MAP` is used for `value` attributes; `NODE_MAP` identifies optional nodes that may be removed.
- `xml_modifier.py`: Loads the DRAGON template, modifies it through `lxml` and XPath, writes the result, and optionally creates a diff.

## Functions

- `calc_dimz(l_kpc, dz_kpc)`: Calculates the vertical grid size using `round(2L / dz) + 1`.
- `calc_dz(l_kpc, dimz)`: Calculates vertical spacing using `2L / (DimZ - 1)`.
- `format_value(value)`: Formats a numeric XML value without unnecessary trailing `.0`.
- `split_decl(text)`: Separates a leading XML declaration from the document body without regular expressions.
- `load_xml(path)`: Reads a DRAGON template, adds the temporary root, and returns an `XmlDoc`.
- `render_xml(doc)`: Serializes an `XmlDoc` back to the original multi-root DRAGON format.
- `write_xml(doc, path)`: Writes rendered XML and creates the parent directory when needed.
- `find_nodes(doc, xpath)`: Returns all element nodes selected by an XPath and rejects scalar XPath results.
- `find_one(doc, xpath)`: Returns exactly one selected element or raises an error.
- `get_param(doc, name, param_map)`: Reads the `value` attribute for a mapped parameter.
- `set_param(doc, name, value, param_map)`: Replaces the `value` attribute for a mapped parameter.
- `apply_params(doc, params, param_map, strict)`: Applies a dictionary of parameter updates and returns the changed names.
- `remove_nodes(doc, names, node_map, strict)`: Removes mapped optional nodes while preserving surrounding whitespace.
- `make_diff(before, after, source, output)`: Builds a unified text diff between template and output.
- `modify_xml(template, params, output, diff, drops, param_map, strict)`: High-level entry point that loads, updates, removes optional nodes, writes XML, and optionally writes a diff.

## Typical Usage

```python
from dragon_utils.xml_manager.xml_modifier import calc_dimz, modify_xml

l_kpc = 4.0
dz_kpc = 0.2

result = modify_xml(
    template="template path",
    params={
        "L": l_kpc,
        "DimZ": calc_dimz(l_kpc, dz_kpc),
        "D0": 4.8,
        "Delta": 0.45,
    },
    output="output path",
    diff="diff path",
)
```

`result` contains the output path, optional diff path, changed parameter names, and removed-node counts.
