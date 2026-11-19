def dump(model, **kw):
    """Kompatibel Pydantic v1 (.dict) dan v2 (.model_dump)."""
    return model.model_dump(**kw) if hasattr(model, "model_dump") else model.dict(**kw)
