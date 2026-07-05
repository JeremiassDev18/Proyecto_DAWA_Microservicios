import os

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from app.core.config import settings

MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "setfit_model",
)


def _import_setfit():
    import setfit
    import datasets
    return setfit, datasets


def models_exist() -> bool:
    return os.path.isdir(MODEL_DIR) and os.path.exists(
        os.path.join(MODEL_DIR, "config.json")
    )


def train_model(texts: list[str], labels: list[str]) -> dict:
    setfit, datasets = _import_setfit()

    model = setfit.SetFitModel.from_pretrained(settings.MODEL_NAME)
    train_dataset = datasets.Dataset.from_dict({"text": texts, "label": labels})

    args = setfit.TrainingArguments(
        num_epochs=5,
        batch_size=16,
    )
    trainer = setfit.Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        column_mapping={"text": "text", "label": "label"},
    )
    trainer.train()

    model.save_pretrained(MODEL_DIR)

    preds: list[str] = model(texts)
    accuracy = float(accuracy_score(labels, preds))
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted", zero_division=0,
    )

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
    }


def load_model():
    if not models_exist():
        raise FileNotFoundError(
            "Modelo SetFit no encontrado. Ejecuta scripts/train_setfit.py primero."
        )
    setfit, _ = _import_setfit()
    return setfit.SetFitModel.from_pretrained(MODEL_DIR)


def evaluate_model(texts: list[str], labels: list[str]) -> dict:
    model = load_model()
    preds: list[str] = model(texts)
    accuracy = float(accuracy_score(labels, preds))
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted", zero_division=0,
    )
    return {
        "accuracy": round(accuracy, 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
    }
