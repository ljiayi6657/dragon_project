from __future__ import annotations


# Source: /home/ljiayi/Script/analysis/optimization/optim_copy.py
OPTIMIZATION_PARAMS = {
    'param_regex': {
        'halo_L': r'(<L\b[^>]*?\bvalue\s*=\s*["\'])([^"\']*)(["\'][^>]*?>)',
        # 'D0_param': '(<D0_1e28\s+value=")[^"]*(".*/>)'
    }
}


def modify_xml(template_path, params, regex_map, output_path):
    """
    Modify XML file based on given parameters and regex map.
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        for param_name, param_value in params.items():
            regex_pattern = regex_map.get(param_name)
            if not regex_pattern:
                print(f"Warning: No regex pattern found for parameter '{param_name}'. Skipping.")
                continue
            pattern = re.compile(regex_pattern, flags=re.DOTALL)
            replacement_string = rf"\g<1>{param_value}\g<3>"

            new_content, count = pattern.subn(replacement_string, file_content)
            if count == 0:
                print(f"Warning: '{param_name}' not found in XML. No changes made.")
            else:
                print(f"Modified '{param_name}' -> {param_value} (hits={count})")
            file_content = new_content

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return True

    except FileNotFoundError:
        print(f"Error: Template XML file '{template_path}' not found.")
        return False
    except Exception as e:
        print(f"Error modifying XML: {e}")
        return False


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_rz_const_validation.py
def generate_xml():
    XML_DIR.mkdir(parents=True, exist_ok=True)
    xml_path = XML_DIR / f"{RUN_STEM}.xml"
    xml_path.write_text(BASELINE_XML.read_text(encoding="utf-8"), encoding="utf-8")
    log(f"Generated constant-delta XML: {xml_path}")
    return xml_path


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_l_scan.py
def dimz_for_l(l_kpc):
    """Compute DimZ from the fixed dz rule."""

    return int(round((2.0 * float(l_kpc)) / DZ_KPC)) + 1


def replace_unique_tag(text, tag_name, value):
    """Replace the first XML-like self-closing tag value."""

    pattern = rf"(<{tag_name}\s+value\s*=\s*[\"'])[^\"']+([\"']\s*/>)"
    replaced, count = re.subn(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError(f"Expected to replace exactly one <{tag_name} value=.../> tag.")
    return replaced


def generate_xml(l_kpc):
    """Create one scan XML from the baseline file."""

    dimz = dimz_for_l(l_kpc)
    text = BASELINE_XML.read_text(encoding="utf-8")
    text = replace_unique_tag(text, "L", str(l_kpc))
    text = replace_unique_tag(text, "DimZ", str(dimz))

    xml_path = XML_DIR / f"test3D_const_L{l_kpc:02d}.xml"
    xml_path.write_text(text, encoding="utf-8")
    log(f"Generated XML: {xml_path} (L={l_kpc}, DimZ={dimz}, dz={DZ_KPC} kpc)")
    return xml_path, dimz


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_l_scan_supplement_lowL.py
def replace_unique_tag(text, tag_name, value):
    pattern = rf"(<{tag_name}\s+value\s*=\s*[\"'])[^\"']+([\"']\s*/>)"
    replaced, count = re.subn(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError(f"Expected one <{tag_name} value=.../> replacement.")
    return replaced


def generate_xml(case):
    text = BASELINE_XML.read_text(encoding="utf-8")
    text = replace_unique_tag(text, "L", f"{case['L']:g}")
    text = replace_unique_tag(text, "DimZ", str(case["DimZ"]))
    xml_path = XML_DIR / f"test3D_const_{case['tag']}.xml"
    xml_path.write_text(text, encoding="utf-8")
    dz = 2.0 * case["L"] / (case["DimZ"] - 1)
    log(
        "Generated supplemental XML: "
        f"{xml_path} (L={case['L']:g}, DimZ={case['DimZ']}, dz={dz:.6g} kpc)"
    )
    return xml_path


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_rz_zdep_validation.py
def replace_tag_value(text, tag_name, value):
    pattern = rf"(<{tag_name}\s+value\s*=\s*[\"'])[^\"']+([\"']\s*/>)"
    replaced, count = re.subn(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    if count == 1:
        return replaced
    return None


def ensure_delta_z(text):
    replaced = replace_tag_value(text, "deltaZ", f"{DELTA_Z:g}")
    if replaced is not None:
        return replaced

    pattern = r"(<deltaB\s+value\s*=\s*[\"'][^\"']+[\"']\s*/>)"
    replaced, count = re.subn(pattern, rf'\1\n    <deltaZ value = "{DELTA_Z:g}"/>', text, count=1)
    if count != 1:
        raise RuntimeError("Could not find <deltaB .../> to insert <deltaZ .../>.")
    return replaced


def generate_xml():
    XML_DIR.mkdir(parents=True, exist_ok=True)
    text = BASELINE_XML.read_text(encoding="utf-8")
    text = ensure_delta_z(text)
    xml_path = XML_DIR / f"{RUN_STEM}.xml"
    xml_path.write_text(text, encoding="utf-8")
    log(f"Generated XML: {xml_path}")
    return xml_path


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_phe_zdep_controlled.py
def format_float_for_xml(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.12g}"


def replace_tag_value(text: str, tag_name: str, value: str) -> str:
    pattern = rf"(<{tag_name}\s+value\s*=\s*[\"'])[^\"']+([\"']\s*/>)"
    replaced, count = re.subn(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace XML tag <{tag_name} value=.../>.")
    return replaced


def read_tag_value(text: str, tag_name: str) -> str:
    pattern = rf"<{tag_name}\s+value\s*=\s*[\"']([^\"']+)[\"']\s*/>"
    match = re.search(pattern, text)
    if not match:
        raise RuntimeError(f"Could not read XML tag <{tag_name} value=.../>.")
    return match.group(1)


def assert_new_path(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")


def generate_xml(model: ModelSpec) -> tuple[Path, Path, Path]:
    baseline_text = BASELINE_XML.read_text(encoding="utf-8")
    delta_value = float(read_tag_value(baseline_text, "Delta"))
    if not math.isclose(delta_value, DELTA):
        raise RuntimeError(f"Expected baseline Delta={DELTA}, got {delta_value}.")

    text = baseline_text
    text = replace_tag_value(text, "VariableDelta", "1")
    text = replace_tag_value(text, "Delta", format_float_for_xml(DELTA))
    text = replace_tag_value(text, "deltaA", format_float_for_xml(DELTA_A))
    text = replace_tag_value(text, "deltaB", format_float_for_xml(DELTA))
    text = replace_tag_value(text, "deltaZ", format_float_for_xml(model.delta_z))
    text = replace_tag_value(text, "vA_kms", "0")

    xml_path = XML_DIR / f"{model.run_stem}.xml"
    source_param_path = XML_DIR / f"{model.run_stem}.source.param"
    diff_path = DIFF_DIR / f"{model.run_stem}_vs_test3D_vardelta.diff"

    for path in [xml_path, source_param_path, diff_path]:
        assert_new_path(path)

    xml_path.write_text(text, encoding="utf-8")
    shutil.copy2(SOURCE_PARAM_TEMPLATE, source_param_path)

    diff = difflib.unified_diff(
        baseline_text.splitlines(),
        text.splitlines(),
        fromfile=os.fspath(BASELINE_XML),
        tofile=os.fspath(xml_path),
        lineterm="",
    )
    diff_path.write_text("\n".join(diff) + "\n", encoding="utf-8")

    log(f"Generated XML: {xml_path}")
    log(f"Copied source param: {source_param_path}")
    log(f"Wrote XML diff: {diff_path}")
    return xml_path, source_param_path, diff_path


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_phe_variable_delta_mechanism.py
def new(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing artifact: {path}")


def replace_value(text: str, tag: str, value: str) -> str:
    pattern = rf"(<{tag}\s+value\s*=\s*[\"'])[^\"']+([\"']\s*/>)"
    result, count = re.subn(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace XML tag {tag}")
    return result


def generate_inputs(model: Model) -> tuple[Path, Path, Path]:
    base = BASELINE.read_text(encoding="utf-8")
    text = base
    for tag, value in [("VariableDelta", "1"), ("Delta", "0.5"), ("deltaA", "0"),
                       ("deltaB", "0.5"), ("deltaZ", f"{model.delta_z:g}"), ("vA_kms", "0")]:
        text = replace_value(text, tag, value)
    xml = XML_DIR / f"{model.stem}.xml"
    source = XML_DIR / f"{model.stem}.source.param"
    diff = DIFF_DIR / f"{model.stem}_vs_test3D_vardelta.diff"
    for path in (xml, source, diff):
        new(path)
    xml.write_text(text, encoding="utf-8")
    shutil.copy2(SOURCE_TEMPLATE, source)
    delta = difflib.unified_diff(base.splitlines(), text.splitlines(), fromfile=os.fspath(BASELINE),
                                 tofile=os.fspath(xml), lineterm="")
    diff.write_text("\n".join(delta) + "\n", encoding="utf-8")
    log(f"Generated inputs: {xml}; {source}; {diff}")
    return xml, source, diff


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_phe_variable_delta_exposure.py
def replace_value(text: str, tag: str, value: str) -> str:
    pattern = rf"(<{tag}\s+value\s*=\s*[\"'])[^\"']+([\"']\s*/>)"
    result, count = re.subn(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace XML tag {tag}")
    return result


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def generate_inputs(model: Model) -> tuple[Path, Path, Path]:
    base = BASELINE.read_text(encoding="utf-8")
    text = base
    for tag, value in [
        ("VariableDelta", "1"),
        ("Delta", "0.5"),
        ("deltaA", "0"),
        ("deltaB", "0.5"),
        ("deltaZ", f"{model.delta_z:g}"),
        ("vA_kms", "0"),
    ]:
        text = replace_value(text, tag, value)
    xml = write_text(XML_DIR / f"{model.stem}.xml", text)
    source = XML_DIR / f"{model.stem}.source.param"
    source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_TEMPLATE, source)
    diff_text = "\n".join(
        difflib.unified_diff(
            base.splitlines(),
            text.splitlines(),
            fromfile=os.fspath(BASELINE),
            tofile=os.fspath(xml),
            lineterm="",
        )
    ) + "\n"
    diff = write_text(DIFF_DIR / f"{model.stem}_vs_test3D_vardelta.diff", diff_text)
    return xml, source, diff


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_phe_fresh_deltaZ_scan_20260715.py
def replace_value(text: str, tag: str, value: str) -> str:
    pattern = rf"(<{tag}\s+value\s*=\s*[\"'])[^\"']+([\"']\s*/>)"
    out, count = re.subn(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError(f"Expected exactly one XML <{tag}> value")
    return out


def prepare() -> None:
    for required in (BASELINE, SOURCE_TEMPLATE, DRAGON):
        if not required.exists():
            raise FileNotFoundError(required)
    for d in (XML_DIR, OUT, CORE, SUPP, TABLES, SPECTRA, DIFFS, AUDIT, LOG_DIR, NOTES.parent):
        d.mkdir(parents=True, exist_ok=True)
    for p in (MASTER_LOG, BUILD_LOG, STATE, NOTES):
        refuse(p)
    for m in MODELS:
        for p in (m.xml, m.source, m.diff, m.run_log, m.full, m.partial, m.txt):
            refuse(p)
    MASTER_LOG.write_text("", encoding="utf-8")
    started_ns = datetime.now().timestamp_ns() if hasattr(datetime.now(), "timestamp_ns") else int(datetime.now().timestamp() * 1e9)
    state = {"task_start": now(), "task_start_ns": started_ns, "repo": repo_state(),
             "build_command": ["make", "clean"], "build_command_2": ["make", f"-j{os.cpu_count() or 1}"],
             "baseline": str(BASELINE), "models": {}}
    base = BASELINE.read_text(encoding="utf-8")
    for m in MODELS:
        text = base
        controlled = {"VariableDelta": "1", "Delta": "0.5", "deltaA": "0",
                      "deltaB": "0.5", "deltaZ": f"{m.delta_z:g}", "vA_kms": "0"}
        for tag, value in controlled.items():
            text = replace_value(text, tag, value)
        m.xml.write_text(text, encoding="utf-8")
        shutil.copy2(SOURCE_TEMPLATE, m.source)
        diff = difflib.unified_diff(base.splitlines(), text.splitlines(),
                                    fromfile=str(BASELINE), tofile=str(m.xml), lineterm="")
        m.diff.write_text("\n".join(diff) + "\n", encoding="utf-8")
        state["models"][m.label] = {"deltaZ": m.delta_z, "stem": m.stem,
                                    "xml": str(m.xml), "xml_sha256": sha256(m.xml),
                                    "source": str(m.source), "source_sha256": sha256(m.source),
                                    "full": str(m.full), "partial": str(m.partial), "txt": str(m.txt)}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_log(f"PREPARED fresh task; commit={state['repo']['head']}; baseline_sha256={state['repo']['baseline_sha256']}")


# Source: /home/ljiayi/Script/analysis/dragon_flux_package/run_phe_gamma_deltaZ_scan_20260716.py
def replace_value(text: str, tag: str, value: str) -> str:
    pattern = rf"(<{tag}\s+value\s*=\s*[\"'])[^\"']+([\"']\s*/>)"
    out, count = re.subn(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError(f"Expected exactly one XML <{tag}> value")
    return out


def prepare() -> None:
    for required in (BASELINE, SOURCE_TEMPLATE, DRAGON, PROMPT):
        if not required.exists():
            raise FileNotFoundError(required)
    for d in (XML_DIR, OUT, CORE, SUPP, TABLES, SPECTRA, DIFFS, AUDIT, LOG_DIR, NOTES.parent):
        d.mkdir(parents=True, exist_ok=True)
    for p in (MASTER_LOG, BUILD_LOG, STATE, NOTES):
        refuse(p)
    for m in MODELS:
        for p in (m.xml, m.source, m.diff, m.run_log, m.stderr_log, m.full, m.partial, m.txt):
            refuse(p)
    MASTER_LOG.write_text("", encoding="utf-8")
    started_ns = datetime.now().timestamp_ns() if hasattr(datetime.now(), "timestamp_ns") else int(datetime.now().timestamp() * 1e9)
    state = {"task_start": now(), "task_start_ns": started_ns, "repo": repo_state(),
             "prompt": str(PROMPT), "prompt_sha256": sha256(PROMPT),
             "build_command": ["make", "clean"], "build_command_2": ["make", f"-j{os.cpu_count() or 1}"],
             "baseline": str(BASELINE), "models": {}}
    base = BASELINE.read_text(encoding="utf-8")
    for m in MODELS:
        text = base
        controlled = {
            "VariableDelta": "1",
            "Delta": "0.5",
            "deltaA": "0",
            "deltaB": "0.5",
            "deltaZ": f"{m.delta_z:g}",
            "vA_kms": "0",
            "Zmin": "1",
            "Zmax": "2",
            "alpha_0": "2.30",
            "alpha_1": "2.30",
            "alpha_2": "2.30",
            "alpha_3": "2.30",
        }
        for tag, value in controlled.items():
            text = replace_value(text, tag, value)
        text, lepton_count = re.subn(r"\s*<PropLepton\s*/>", "", text, count=1)
        text, extra_count = re.subn(r"\s*<PropExtraComponent\s*/>", "", text, count=1)
        if lepton_count != 1 or extra_count != 1:
            raise RuntimeError("Expected PropLepton and PropExtraComponent in baseline XML")
        m.xml.write_text(text, encoding="utf-8")
        shutil.copy2(SOURCE_TEMPLATE, m.source)
        diff = difflib.unified_diff(base.splitlines(), text.splitlines(),
                                    fromfile=str(BASELINE), tofile=str(m.xml), lineterm="")
        m.diff.write_text("\n".join(diff) + "\n", encoding="utf-8")
        state["models"][m.label] = {"deltaZ": m.delta_z, "stem": m.stem,
                                    "xml": str(m.xml), "xml_sha256": sha256(m.xml),
                                    "source": str(m.source), "source_sha256": sha256(m.source),
                                    "full": str(m.full), "partial": str(m.partial), "txt": str(m.txt)}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_log(f"PREPARED fresh task; commit={state['repo']['head']}; baseline_sha256={state['repo']['baseline_sha256']}")
