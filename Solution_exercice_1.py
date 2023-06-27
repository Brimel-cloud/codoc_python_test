import importlib
import subprocess
import pkg_resources

def install_and_check_version(library_name):
    try:
        # Je vérifie si la librairie est déjà installé
        importlib.import_module(library_name)
        print(f"La bibliothèque '{library_name}' est déjà installée.")
    except ImportError:
        # Installation de la librairie
        print(f"Installation de la bibliothèque '{library_name}'...")
        subprocess.check_call(['python', '-m', 'pip', 'install', library_name])
        print(f"La bibliothèque '{library_name}' a été installée avec succès.")

    # Affichage de la version installée
    version = pkg_resources.get_distribution(library_name).version
    print(f"Version installée de '{library_name}': {version}")

# J'installe les librairies dont j'aurai besoin en appelant la fonction définie ci-dessus
install_and_check_version("pandas")
install_and_check_version("openpyxl")




import pandas as pd
import sqlite3

# Chemin vers le fichier export_patient.xlsx
fichier_excel = "fichiers_source/export_patient.xlsx"

# Connexion à la base de données SQLite
connexion = sqlite3.connect('drwh.db')
curseur = connexion.cursor()

# Lecture du fichier Excel dans un DataFrame
df_patients = pd.read_excel(fichier_excel, sheet_name=0)

# Créer une nouvelle colonne 'PATIENT_NUM' avec des valeurs croissantes
df_patients['PATIENT_NUM'] = range(1, len(df_patients) + 1)

# Réorganiser les colonnes pour avoir 'PATIENT_NUM' en première position
df_patients = df_patients[['PATIENT_NUM'] + list(df_patients.columns[:-1])]


# Renommer les colonnes
df_patients = df_patients.rename(columns=
                                 {'NOM': 'LASTNAME', 
                                  'PRENOM': 'FIRSTNAME', 
                                  'DATE_NAISSANCE': 'BIRTH_DATE',
                                  'SEXE': 'SEX',
                                  'NOM_JEUNE_FILLE': 'MAIDEN_NAME',
                                  'ADRESSE': 'RESIDENCE_ADDRESS',
                                  'CP': 'ZIP_CODE',
                                  'VILLE': 'RESIDENCE_CITY',
                                  'PAYS': 'RESIDENCE_COUNTRY',
                                  'DATE_MORT': 'DEATH_DATE',
                                  'TEL': 'PHONE_NUMBER',
                                  })


df_patients['MAIDEN_NAME'] = df_patients['MAIDEN_NAME'].astype(str)

df_DWH_PATIENT= df_patients.copy()
# Supprimer la colonne 'B' en utilisant la méthode drop()
df_DWH_PATIENT = df_DWH_PATIENT.drop('HOSPITAL_PATIENT_ID', axis=1)
df_DWH_PATIENT = df_DWH_PATIENT[['PATIENT_NUM', 'LASTNAME', 'FIRSTNAME', 'BIRTH_DATE', 'SEX', 'MAIDEN_NAME', 'RESIDENCE_ADDRESS', 'PHONE_NUMBER', 'ZIP_CODE', 'RESIDENCE_CITY', 'DEATH_DATE', 'RESIDENCE_COUNTRY']]

# Afficher le DataFrame avec la colonne déplacée
print(df_DWH_PATIENT)


# Afficher le schéma de la DataFrame
print(df_DWH_PATIENT.dtypes)

# Insertion des données dans la table DWH_PATIENT
for _, row in df_patients.iterrows():

    # Récupération des valeurs de chaque colonne
    patient_num = row['PATIENT_NUM']
    lastname = row['LASTNAME']
    firstname = row['FIRSTNAME']
    birth_date = row['BIRTH_DATE']
    sex = row['SEX']
    maiden_name = row['MAIDEN_NAME']
    residence_address = row['RESIDENCE_ADDRESS']
    phone_number = row['PHONE_NUMBER']
    zip_code = row['ZIP_CODE']
    residence_city = row['RESIDENCE_CITY']
    death_date = row['DEATH_DATE']
    residence_country = row['RESIDENCE_COUNTRY']

    # Vérification si la valeur de patient_num existe déjà dans la base de données
    patient_exists_query = """
        SELECT COUNT(*) FROM DWH_PATIENT WHERE PATIENT_NUM = ?
    """
    curseur.execute(patient_exists_query, (patient_num,))
    patient_exists = curseur.fetchone()[0]

    if patient_exists:
        # Mise à jour de la ligne correspondante
        curseur.execute("""
            UPDATE DWH_PATIENT SET
                LASTNAME = ?,
                FIRSTNAME = ?,
                BIRTH_DATE = ?,
                SEX = ?,
                MAIDEN_NAME = ?,
                RESIDENCE_ADDRESS = ?,
                PHONE_NUMBER = ?,
                ZIP_CODE = ?,
                RESIDENCE_CITY = ?,
                DEATH_DATE = ?,
                RESIDENCE_COUNTRY = ?
            WHERE PATIENT_NUM = ?
        """, (lastname, firstname, birth_date, sex, maiden_name, residence_address, phone_number,
              zip_code, residence_city, death_date, residence_country, patient_num))
    else:
        # Insertion d'une nouvelle ligne avec la prochaine valeur de patient_num
        next_patient_num_query = """
            SELECT COALESCE(MAX(PATIENT_NUM), 0) + 1 FROM DWH_PATIENT
        """
        curseur.execute(next_patient_num_query)
        next_patient_num = curseur.fetchone()[0]

        curseur.execute("""
            INSERT INTO DWH_PATIENT (
                PATIENT_NUM, LASTNAME, FIRSTNAME, BIRTH_DATE, SEX, MAIDEN_NAME, RESIDENCE_ADDRESS,
                PHONE_NUMBER, ZIP_CODE, RESIDENCE_CITY, DEATH_DATE, RESIDENCE_COUNTRY,
                RESIDENCE_LATITUDE, RESIDENCE_LONGITUDE, DEATH_CODE, UPDATE_DATE, BIRTH_COUNTRY,
                BIRTH_CITY, BIRTH_ZIP_CODE, BIRTH_LATITUDE, BIRTH_LONGITUDE, UPLOAD_ID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
        """, (next_patient_num, lastname, firstname, birth_date, sex, maiden_name, residence_address, phone_number,
              zip_code, residence_city, death_date, residence_country))

    # Récupération des valeurs pour la table DWH_PATIENT_IPPHIST
    hospital_patient_id = row['HOSPITAL_PATIENT_ID']

    # Insertion des données dans la table DWH_PATIENT_IPPHIST
    curseur.execute("""
        INSERT INTO DWH_PATIENT_IPPHIST (
            PATIENT_NUM, HOSPITAL_PATIENT_ID, ORIGIN_PATIENT_ID, MASTER_PATIENT_ID, UPLOAD_ID
        ) VALUES (?, ?, NULL, NULL, NULL)
    """, (patient_num, hospital_patient_id))


# Exécution de la requête SELECT pour voir le contenu de la table DWH_PATIENT et voir si les données ont été ajoutées avec succès
curseur.execute("SELECT * FROM DWH_PATIENT")
resultats = curseur.fetchall()

# Affichage des résultats
for ligne in resultats:
    print(ligne)

# Validation des modifications dans la base de données
connexion.commit()

# Fermeture de la connexion
connexion.close()

## copyright Brimel NJINKOUE