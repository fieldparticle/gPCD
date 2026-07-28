import math

from gbase.libconf import AttrDict


LEGACY_SCENE_GEOMETRY_KEYS = (
    "Lighting_ball",
    "rectangle_wall_segments",
    "curve_wall_segments",
    "lighting_surface_objects",
)


def _as_vector3(raw_value, errors, context):
    if raw_value is None:
        errors.append(f"{context} is required")
        return None
    try:
        if len(raw_value) != 3:
            errors.append(f"{context} must contain exactly 3 values")
            return None
        values = tuple(float(value) for value in raw_value)
    except (TypeError, ValueError):
        errors.append(f"{context} values must be numeric")
        return None
    if not all(math.isfinite(value) for value in values):
        errors.append(f"{context} values must be finite")
        return None
    return values


def _as_positive_float(raw_value, errors, context):
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        errors.append(f"{context} is required and must be numeric")
        return None
    if not math.isfinite(value):
        errors.append(f"{context} must be finite")
    elif value <= 0.0:
        errors.append(f"{context} must be positive")
    return value


def _as_nonnegative_float(raw_value, errors, context):
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        errors.append(f"{context} is required and must be numeric")
        return None
    if not math.isfinite(value):
        errors.append(f"{context} must be finite")
    elif value < 0.0:
        errors.append(f"{context} must not be negative")
    return value


def _as_float(raw_value, errors, context):
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        errors.append(f"{context} is required and must be numeric")
        return None
    if not math.isfinite(value):
        errors.append(f"{context} must be finite")
        return None
    return value


def _as_positive_int(raw_value, errors, context):
    if type(raw_value) is not int:
        errors.append(f"{context} is required and must be an integer")
        return None
    value = raw_value
    if value <= 0:
        errors.append(f"{context} must be positive")
    return value


def _as_nonnegative_int(raw_value, errors, context):
    if type(raw_value) is not int:
        errors.append(f"{context} is required and must be an integer")
        return None
    value = raw_value
    if value < 0:
        errors.append(f"{context} must not be negative")
    return value


def _as_required_string(raw_value, errors, context):
    if not isinstance(raw_value, str):
        errors.append(f"{context} is required and must be a string")
        return None
    value = raw_value.strip()
    if not value:
        errors.append(f"{context} must not be empty")
        return None
    return value


def _roles(raw_value, errors, context):
    if raw_value is None:
        errors.append(f"{context}.roles is required")
        return set()
    if isinstance(raw_value, (str, bytes)):
        errors.append(f"{context}.roles must be a list of strings")
        return set()
    try:
        values = tuple(raw_value)
    except TypeError:
        errors.append(f"{context}.roles must be a list of strings")
        return set()
    if not values:
        errors.append(f"{context}.roles must not be empty")
        return set()
    roles = set()
    for role_index, raw_role in enumerate(values):
        role_context = f"{context}.roles[{role_index}]"
        role = _as_required_string(raw_role, errors, role_context)
        if role is not None:
            roles.add(role.lower())
    valid_roles = {"collision", "boundary_markers", "lighting_surface"}
    invalid_roles = sorted(roles - valid_roles)
    if invalid_roles:
        errors.append(
            f"{context}.roles contains unknown role(s): "
            + ", ".join(invalid_roles)
        )
    return roles


def _scene_objects(scene_model, errors):
    if scene_model is None:
        return ()
    try:
        objects = scene_model.get("objects")
    except AttributeError:
        errors.append("scene_model must be a key-value object")
        return ()
    if objects is None:
        errors.append("scene_model.objects is required")
        return ()
    if isinstance(objects, (str, bytes)) or hasattr(objects, "items"):
        errors.append("scene_model.objects must be a list")
        return ()
    try:
        return tuple(objects)
    except TypeError:
        errors.append("scene_model.objects must be a list")
        return ()


def _rectangle_wall_config(name, obj, errors, context):
    origin = _as_vector3(obj.get("origin"), errors, f"{context}.origin")
    normal = _as_vector3(obj.get("normal"), errors, f"{context}.normal")
    u_length = _as_nonnegative_float(
        obj.get("u_length"),
        errors,
        f"{context}.u_length",
    )
    v_length = _as_nonnegative_float(
        obj.get("v_length"),
        errors,
        f"{context}.v_length",
    )
    surface_id = _as_positive_int(obj.get("surface_id"), errors, f"{context}.surface_id")
    material_id = _as_nonnegative_int(
        obj.get("material_id", 0),
        errors,
        f"{context}.material_id",
    )
    u_axis = _as_required_string(obj.get("u_axis"), errors, f"{context}.u_axis")
    v_axis = _as_required_string(obj.get("v_axis"), errors, f"{context}.v_axis")
    u_axis = None if u_axis is None else u_axis.lower()
    v_axis = None if v_axis is None else v_axis.lower()
    if u_axis is not None and u_axis not in {"x", "y", "z"}:
        errors.append(f"{context}.u_axis must be x, y, or z")
    if v_axis is not None and v_axis not in {"x", "y", "z"}:
        errors.append(f"{context}.v_axis must be x, y, or z")
    if u_axis and v_axis and u_axis == v_axis:
        errors.append(f"{context}.u_axis and v_axis must differ")
    if normal is not None and math.sqrt(sum(value * value for value in normal)) <= 1.0e-12:
        errors.append(f"{context}.normal must not be zero")
    if (
        origin is None
        or normal is None
        or u_length is None
        or v_length is None
        or surface_id is None
        or material_id is None
        or u_axis not in {"x", "y", "z"}
        or v_axis not in {"x", "y", "z"}
        or u_axis == v_axis
    ):
        return None
    return AttrDict(
        {
            "origin": origin,
            "u_axis": u_axis,
            "u_length": u_length,
            "v_axis": v_axis,
            "v_length": v_length,
            "normal": normal,
            "wall_flag": surface_id,
            "material_id": material_id,
        }
    )


def _lighting_ball_config(obj, errors, context):
    center = _as_vector3(obj.get("center"), errors, f"{context}.center")
    radius = _as_positive_float(obj.get("radius"), errors, f"{context}.radius")
    surface_id = _as_positive_int(obj.get("surface_id"), errors, f"{context}.surface_id")
    material_id = _as_nonnegative_int(
        obj.get("material_id", 0),
        errors,
        f"{context}.material_id",
    )
    if (
        center is None
        or radius is None
        or surface_id is None
        or material_id is None
    ):
        return None
    return AttrDict(
        {
            "x": center[0],
            "y": center[1],
            "z": center[2],
            "radius": radius,
            "material_id": material_id,
            "wall_flag": surface_id,
        }
    )


def _curve_wall_config(obj, errors, context):
    boundary_kind = _as_required_string(
        obj.get("boundary_kind"),
        errors,
        f"{context}.boundary_kind",
    )
    function = _as_required_string(obj.get("function"), errors, f"{context}.function")
    u_start = _as_nonnegative_float(obj.get("u_start"), errors, f"{context}.u_start")
    u_end = _as_nonnegative_float(obj.get("u_end"), errors, f"{context}.u_end")
    f_start = _as_float(obj.get("f_start"), errors, f"{context}.f_start")
    a1 = _as_float(obj.get("a1"), errors, f"{context}.a1")
    a2 = _as_float(obj.get("a2"), errors, f"{context}.a2")
    a3 = _as_float(obj.get("a3"), errors, f"{context}.a3")
    normal_sign = _as_float(
        obj.get("normal_sign"),
        errors,
        f"{context}.normal_sign",
    )
    surface_id = _as_positive_int(obj.get("surface_id"), errors, f"{context}.surface_id")
    material_id = _as_nonnegative_int(
        obj.get("material_id", 0),
        errors,
        f"{context}.material_id",
    )
    boundary_kind = None if boundary_kind is None else boundary_kind.lower()
    function = None if function is None else function.lower()
    if boundary_kind is not None and boundary_kind not in {"regular", "reservoir"}:
        errors.append(f"{context}.boundary_kind must be regular or reservoir")
    if function is not None and function not in {"y_of_x", "x_of_y"}:
        errors.append(f"{context}.function must be y_of_x or x_of_y")
    if u_start is not None and u_end is not None and abs(u_end - u_start) <= 1.0e-12:
        errors.append(f"{context} has zero length")
    if normal_sign == 0.0:
        errors.append(f"{context}.normal_sign must not be zero")
    if (
        boundary_kind not in {"regular", "reservoir"}
        or function not in {"y_of_x", "x_of_y"}
        or u_start is None
        or u_end is None
        or f_start is None
        or a1 is None
        or a2 is None
        or a3 is None
        or normal_sign is None
        or surface_id is None
        or material_id is None
    ):
        return None
    return AttrDict(
        {
            "boundary_kind": boundary_kind,
            "function": function,
            "u_start": u_start,
            "u_end": u_end,
            "f_start": f_start,
            "a1": a1,
            "a2": a2,
            "a3": a3,
            "normal_sign": normal_sign,
            "wall_flag": surface_id,
            "material_id": material_id,
        }
    )


def _lighting_surface_object(name, object_type, surface_id, material_id):
    return AttrDict(
        {
            "name": name,
            "source": "scene_model",
            "surface_type": object_type.upper(),
            "surface_id": surface_id,
            "material_id": material_id,
        }
    )


def apply_scene_model(config):
    """Derive legacy runtime geometry config from authored scene_model."""
    scene_model = config.get("scene_model")
    if scene_model is None:
        return
    if config.get("_scene_model_derived", False):
        return

    legacy_keys = [key for key in LEGACY_SCENE_GEOMETRY_KEYS if key in config]
    if legacy_keys:
        raise ValueError(
            "scene_model replaces authored geometry keys; remove "
            + ", ".join(legacy_keys)
        )

    errors = []
    objects = _scene_objects(scene_model, errors)
    lighting_ball = None
    rectangle_segments = AttrDict()
    curve_segments = AttrDict()
    lighting_surface_objects = []

    names = set()
    surface_ids = set()
    for index, obj in enumerate(objects):
        context = f"scene_model.objects[{index}]"
        if not hasattr(obj, "get"):
            errors.append(f"{context} must be a key-value object")
            continue
        name = _as_required_string(obj.get("name"), errors, f"{context}.name")
        if name is None:
            continue
        if name in names:
            errors.append(f"{context}.name duplicates {name}")
        names.add(name)

        object_type = _as_required_string(obj.get("type"), errors, f"{context}.type")
        object_type = None if object_type is None else object_type.lower()
        roles = _roles(obj.get("roles"), errors, context)
        surface_id = obj.get("surface_id")
        if type(surface_id) is int:
            if surface_id in surface_ids:
                errors.append(f"{context}.surface_id duplicates {surface_id}")
            surface_ids.add(surface_id)

        if object_type == "sphere":
            sphere_config = _lighting_ball_config(obj, errors, context)
            if sphere_config is None:
                continue
            if "collision" in roles or "boundary_markers" in roles:
                if lighting_ball is not None:
                    errors.append("scene_model supports one Lighting_ball sphere for now")
                lighting_ball = sphere_config
            if "lighting_surface" in roles:
                lighting_surface_objects.append(
                    _lighting_surface_object(
                        name,
                        "sphere",
                        int(sphere_config["wall_flag"]),
                        int(sphere_config["material_id"]),
                    )
                )
        elif object_type == "rectangle":
            rectangle_config = _rectangle_wall_config(name, obj, errors, context)
            if rectangle_config is None:
                continue
            if "collision" in roles or "boundary_markers" in roles:
                rectangle_segments[name] = rectangle_config
            if "lighting_surface" in roles:
                lighting_surface_objects.append(
                    _lighting_surface_object(
                        name,
                        "rectangle_wall",
                        int(rectangle_config["wall_flag"]),
                        int(rectangle_config["material_id"]),
                    )
                )
        elif object_type == "curve":
            curve_config = _curve_wall_config(obj, errors, context)
            if curve_config is None:
                continue
            if "collision" in roles or "boundary_markers" in roles:
                curve_segments[name] = curve_config
            if "lighting_surface" in roles:
                lighting_surface_objects.append(
                    _lighting_surface_object(
                        name,
                        "curve_wall",
                        int(curve_config["wall_flag"]),
                        int(curve_config["material_id"]),
                    )
                )
        else:
            errors.append(f"{context}.type must be sphere, rectangle, or curve")

    if errors:
        raise ValueError(
            "scene_model configuration error(s):\n  - " + "\n  - ".join(errors)
        )

    if lighting_ball is not None:
        config["Lighting_ball"] = lighting_ball
    config["rectangle_wall_segments"] = rectangle_segments
    config["curve_wall_segments"] = curve_segments
    config["lighting_surface_objects"] = tuple(lighting_surface_objects)
    config["_scene_model_derived"] = True
