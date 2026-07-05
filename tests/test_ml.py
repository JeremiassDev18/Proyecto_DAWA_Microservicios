import sys
import os
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))


def _make_mock_model(preds=None, probas=None):
    m = MagicMock(return_value=preds or ["SIN_INTENCION"])
    m.predict_proba = MagicMock(return_value=probas or [[0.5, 0.5]])
    m.save_pretrained = MagicMock()
    return m


def test_clean_text():
    from app.ml.text_cleaner import clean_text
    result = clean_text("  Hola, ?Como Estas?   ")
    assert result == "hola como estas"


def test_clean_text_special_chars():
    from app.ml.text_cleaner import clean_text
    result = clean_text("Prueba!@# con $%^ &*() caracteres")
    assert result == "prueba con caracteres"


def test_clean_corpus():
    from app.ml.text_cleaner import clean_corpus
    result = clean_corpus(["Texto Uno", "Texto Dos"])
    assert result == ["texto uno", "texto dos"]


def test_models_exist_sin_directorio():
    import app.ml.setfit_trainer as st
    original = st.MODEL_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            st.MODEL_DIR = os.path.join(tmp, "nonexistent")
            assert st.models_exist() is False
    finally:
        st.MODEL_DIR = original


def test_models_exist_con_directorio():
    import app.ml.setfit_trainer as st
    original = st.MODEL_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            st.MODEL_DIR = tmp
            with open(os.path.join(tmp, "config.json"), "w") as f:
                f.write("{}")
            assert st.models_exist() is True
    finally:
        st.MODEL_DIR = original


def test_load_model_raise_sin_modelo():
    import app.ml.setfit_trainer as st
    original = st.MODEL_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            st.MODEL_DIR = os.path.join(tmp, "missing")
            try:
                st.load_model()
                assert False, "Debio lanzar FileNotFoundError"
            except FileNotFoundError:
                pass
    finally:
        st.MODEL_DIR = original


def test_train_model():
    import app.ml.setfit_trainer as st
    mock_model = _make_mock_model(preds=["A", "B"])

    original = st.MODEL_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            st.MODEL_DIR = tmp
            st._import_setfit = MagicMock(return_value=(MagicMock(), MagicMock()))
            mock_setfit, _mock_ds = st._import_setfit()
            mock_setfit.SetFitModel.from_pretrained.return_value = mock_model
            mock_setfit.TrainingArguments = MagicMock(return_value=MagicMock())
            mock_setfit.Trainer = MagicMock(return_value=MagicMock())

            metrics = st.train_model(["hola", "adios"], ["A", "B"])
            assert "accuracy" in metrics
            assert "precision" in metrics
            assert "recall" in metrics
            assert "f1_score" in metrics
            mock_model.save_pretrained.assert_called_once_with(tmp)
    finally:
        st.MODEL_DIR = original


def test_predictor_sin_modelo():
    import app.ml.predictor as pred
    import app.ml.setfit_trainer as st
    pred.clear_cache()
    original = st.MODEL_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            st.MODEL_DIR = os.path.join(tmp, "missing")
            assert pred.predict_intent("hola") == "SIN_INTENCION"
            intent, conf = pred.predict_with_confidence("hola")
            assert intent == "SIN_INTENCION"
            assert conf == 0.0
    finally:
        st.MODEL_DIR = original


def test_predictor_con_modelo():
    import app.ml.predictor as pred
    import app.ml.setfit_trainer as st
    pred.clear_cache()

    mock_model = _make_mock_model(
        preds=["SALUDO"],
        probas=[[0.05, 0.90, 0.05]],
    )
    st.load_model = MagicMock(return_value=mock_model)

    original = st.MODEL_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            st.MODEL_DIR = tmp
            with open(os.path.join(tmp, "config.json"), "w") as f:
                f.write("{}")
            intent = pred.predict_intent("hola")
            assert intent == "SALUDO"
            intent2, conf = pred.predict_with_confidence("hola")
            assert intent2 == "SALUDO"
            assert conf == 0.9
    finally:
        st.MODEL_DIR = original
        st.load_model = None


def test_evaluate_model():
    import app.ml.setfit_trainer as st
    mock_model = _make_mock_model(preds=["A", "B", "A", "B", "A"])
    st.load_model = MagicMock(return_value=mock_model)

    original = st.MODEL_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            st.MODEL_DIR = tmp
            with open(os.path.join(tmp, "config.json"), "w") as f:
                f.write("{}")
            metrics = st.evaluate_model(
                ["t1", "t2", "t3", "t4", "t5"],
                ["A", "B", "A", "B", "A"],
            )
            assert "accuracy" in metrics
    finally:
        st.MODEL_DIR = original
        st.load_model = None
