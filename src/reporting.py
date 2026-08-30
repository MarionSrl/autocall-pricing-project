"""Écriture des résultats numériques (CSV + Markdown) produits par les scripts
de figure, pour recopie directe dans le mémoire."""


def dataframe_vers_markdown(df, float_format="{:.2f}"):
    """Table Markdown simple (sans dépendance à `tabulate`)."""
    colonnes = list(df.columns)
    lignes = ["| " + " | ".join(colonnes) + " |",
              "|" + "|".join(["---"] * len(colonnes)) + "|"]
    for _, ligne in df.iterrows():
        cellules = []
        for val in ligne:
            if isinstance(val, float):
                cellules.append(float_format.format(val))
            else:
                cellules.append(str(val))
        lignes.append("| " + " | ".join(cellules) + " |")
    return "\n".join(lignes)


def ecrire_csv_et_md(df, chemin_base, float_format="{:.4f}"):
    """Écrit df en <chemin_base>.csv et <chemin_base>.md."""
    df.to_csv(f"{chemin_base}.csv", index=False, float_format="%.6f")
    with open(f"{chemin_base}.md", "w") as f:
        f.write(dataframe_vers_markdown(df, float_format=float_format))
        f.write("\n")
