import sys
import os
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres_client import init_pool, get_connection, release_connection
from app.db import queries
from app.ml.predictor import predict_with_confidence


def build_confusion_matrix(conn):
    examples = queries.get_activos_validados(conn)
    if not examples:
        print("No hay ejemplos validados en el dataset.")
        return

    intenciones = sorted(set(row[3] for row in examples))
    matrix = defaultdict(lambda: defaultdict(int))
    total = 0
    correct = 0

    print(f"Evaluando {len(examples)} ejemplos...\n")

    for row in examples:
        id_ej, texto, id_int, intencion_real = row
        predicha, confianza = predict_with_confidence(texto)
        matrix[intencion_real][predicha] += 1
        total += 1
        if intencion_real == predicha:
            correct += 1

    accuracy = correct / total * 100 if total else 0
    print(f"Accuracy global: {accuracy:.1f}% ({correct}/{total})\n")

    header = f"{'Real \\ Predicha':25s}" + "".join(f"{i:20s}" for i in intenciones)
    print(header)
    print("-" * len(header))

    for real in intenciones:
        row = f"{real:25s}"
        for pred in intenciones:
            val = matrix[real][pred]
            if real == pred:
                row += f"{f'[{val}]':>20s}"
            elif val > 0:
                row += f"{str(val):>20s}"
            else:
                row += f"{'.':>20s}"
        print(row)

    print("\n--- Pares conflictivos (mayor confusión) ---")
    confusiones = []
    for real in intenciones:
        for pred in intenciones:
            if real != pred and matrix[real][pred] > 0:
                confusiones.append((matrix[real][pred], real, pred))

    confusiones.sort(reverse=True)
    for count, real, pred in confusiones[:10]:
        pct = count / sum(matrix[real].values()) * 100
        print(f"  {real} → {pred}: {count} ({pct:.0f}%)")

    print("\n--- Ejemplos clasificados con baja confianza (< 0.60) ---")
    bajos = 0
    for row in examples:
        id_ej, texto, id_int, intencion_real = row
        predicha, confianza = predict_with_confidence(texto)
        if confianza < 0.60:
            bajos += 1
            if bajos <= 15:
                print(f"  [{confianza:.2f}] real={intencion_real} "
                      f"pred={predicha}: \"{texto[:60]}...\"")

    print(f"\nTotal con confianza < 0.60: {bajos}/{total}")


def main():
    init_pool()
    conn = get_connection()
    try:
        build_confusion_matrix(conn)
    finally:
        release_connection(conn)


if __name__ == "__main__":
    main()
