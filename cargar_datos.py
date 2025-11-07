import pandas as pd
import glob
import os
import re


def clean_date_format(date_str):
    """Convierte fechas dd/mm/yy o dd/mm/yyyy al formato dd/mm/yyyy"""
    if pd.isna(date_str):
        return None
    date_str = str(date_str).strip()
    # Formato dd/mm/yy → dd/mm/20yy o dd/mm/19yy según contexto
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2})$", date_str)
    if match:
        day, month, year = match.groups()
        year = int(year)
        # Si el año es menor que 30 → asumimos 2000+, si no 1900+
        year = year + 2000 if year < 30 else year + 1900
        return f"{int(day):02d}/{int(month):02d}/{year}"
    # Si ya tiene 4 dígitos de año, dejamos igual
    return date_str

# Carpeta donde están todos los CSV
def cargar_datos(verbose=True, folder_path= "data/temporadas/", save_path= "data/partidos/matches.csv", pickle_path= "data/partidos/matches.pkl"):
    # Cargar todos los CSV
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    dataframes = []
    for file in sorted(csv_files):
        if verbose:
            print(f"Cargando {os.path.basename(file)}...")
        df = pd.read_csv(file)

        # --- Renombrar columnas importantes ---
        rename_map = {
            'FTHG': 'home_goals', 'HG': 'home_goals',
            'FTAG': 'away_goals', 'AG': 'away_goals',
            'FTR': 'result', 'Res': 'result',
            'HomeTeam': 'home_team',
            'AwayTeam': 'away_team',
            'HS': 'home_shots', 'AS': 'away_shots',
            'HST': 'home_shots_on_target', 'AST': 'away_shots_on_target',
            'HC': 'home_corners', 'AC': 'away_corners',
            'HF': 'home_fouls', 'AF': 'away_fouls',
            'HY': 'home_yellow', 'AY': 'away_yellow',
            'HR': 'home_red', 'AR': 'away_red',
            'Div': 'league'
        }
        df = df.rename(columns=rename_map)

        # --- Mantener solo columnas relevantes ---
        cols_to_keep = [c for c in [
            'league', 'home_team', 'away_team', 'home_goals', 'away_goals', 'result',
            'home_shots', 'away_shots', 'home_shots_on_target', 'away_shots_on_target',
            'home_corners', 'away_corners', 'home_fouls', 'away_fouls',
            'home_yellow', 'away_yellow', 'home_red', 'away_red', 'Date'
        ] if c in df.columns]
        df = df[cols_to_keep]

        # --- Normalizar las fechas ---
        if "Date" in df.columns:
            df["Date"] = df["Date"].apply(clean_date_format)
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
            df["year"] = df["Date"].dt.year
        else:
            df["year"] = None

        # --- Crear ID de temporada basado en los años detectados ---
        years = df["year"].dropna().unique()
        if len(years) == 0:
            season_id = "unknown"
        elif len(years) == 1:
            season_id = f"{int(years[0])}"
        else:
            season_id = f"{int(min(years))}_{int(max(years))}"

        df["season_id"] = season_id

        # --- Ordenar los partidos dentro de la temporada ---
        df = df.reset_index(drop=True)
        df["match_order"] = df.index + 1

        dataframes.append(df)

    # Unir todo en un solo DataFrame
    matches = pd.concat(dataframes, ignore_index=True)

    # Opcional: convertir resultado a formato numérico si se usa como target
    result_map = {'H': 1, 'D': 0, 'A': -1}
    matches["result"] = matches["result"].map(result_map)
    if verbose:
        print(f"Datos combinados: {matches.shape[0]} partidos de {len(csv_files)} temporadas")
        print(matches.head())
        print(matches.shape)
    if save_path:
        matches.to_csv(save_path, index=False)
        if verbose:
            print(f"Datos guardados en {save_path}")
    if pickle_path:
        matches.to_pickle(pickle_path)
        if verbose:
            print(f"Datos guardados en {pickle_path}")
    return matches

if __name__ == "__main__":
    cargar_datos()