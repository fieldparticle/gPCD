from decimal import Decimal
from pathlib import Path

from base.FieldBase import FieldBase
from base.MomBase import MomBase


def data_dir_name_for_dt(dt: float | None) -> str:
    if dt is None:
        return "data"

    dt_decimal = Decimal(str(dt)).normalize()
    dt_text = format(dt_decimal, "f")
    if "." not in dt_text:
        return f"data{dt_text}"

    integer_part, fractional_part = dt_text.split(".", 1)
    fractional_part = fractional_part.rstrip("0")
    if integer_part == "0":
        return f"data{fractional_part or '0'}"
    return f"data{integer_part}{fractional_part}"


def export_path_for_dt(filename: str, dt: float | None, output_dir_name: str | None = None) -> str:
    dir_name = data_dir_name_for_dt(dt) if output_dir_name in (None, "") else output_dir_name
    return str(Path(dir_name) / filename)


def resolve_base_class(base_model: str):
    normalized = base_model.strip().lower()
    if normalized == "field":
        return FieldBase
    if normalized == "mom":
        return MomBase
    raise ValueError(f"Unsupported BASE_MODEL '{base_model}'. Use 'field' or 'mom'.")
