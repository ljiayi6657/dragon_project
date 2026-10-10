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


## parameter_map.py

库模块，无 CLI；`from dragon_utils.xml_manager.parameter_map import PARAM_MAP, NODE_MAP`。输入为公开参数名，输出为 XPath 映射；L、DimZ、Zmin/Zmax、能量轴及注入/扩散参数通过 value 属性查询。可移除节点只列在 NODE_MAP。无外部依赖，不生成文件；未登记参数会由 xml_modifier 报错。fullstore/partialstore 和 DimZ_division 属于节点存在性/points 语义，单轮入口直接读取，不伪装为 value 参数。

## xml_modifier.py

推荐导入接口：`from dragon_utils.xml_manager.xml_modifier import load_xml, get_param, modify_xml`；上方列出全部主要函数。依赖 Python 3.10+、lxml，输入是 DRAGON 多顶层 XML（也兼容既有特殊 XML 声明），输出是显式指定的 XML 与可选 diff。它会重新序列化并直接写入目标，因此调用方负责防覆盖和安排 `data/processed/`；同主体 source.param 必须由准备工具复制。只读查询不会改 XML；companion 运行阶段只使用 load_xml/get_param，不调用编辑函数。`calc_dz` 只适用于均匀 z 网格，非均匀 division 不能用该公式。
