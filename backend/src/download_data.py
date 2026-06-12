"""
Los datos se cargan localmente desde backend/data/.
Este módulo ya no descarga nada de GCP.
"""


def download_data(list_files=None):
    raise NotImplementedError(
        "La descarga desde GCP fue eliminada. "
        "Coloca los CSV directamente en backend/data/: "
        "Retail_Transaction_Dataset.csv, USA_Inflation.csv"
    )
