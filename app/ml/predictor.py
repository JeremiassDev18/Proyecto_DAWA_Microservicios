_cached_model = None


def set_cached_model(model):
    global _cached_model
    _cached_model = model


def clear_cache():
    global _cached_model
    _cached_model = None


def _get_model():
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    from app.ml.setfit_trainer import models_exist, load_model
    if not models_exist():
        return None
    _cached_model = load_model()
    return _cached_model


def predict_intent(text: str) -> str:
    model = _get_model()
    if model is None:
        return "SIN_INTENCION"
    return model([text])[0]


def predict_with_confidence(text: str) -> tuple[str, float]:
    model = _get_model()
    if model is None:
        return "SIN_INTENCION", 0.0
    pred = model([text])[0]
    probas = model.predict_proba([text])[0]
    confidence = float(max(probas))
    return pred, round(confidence, 4)
