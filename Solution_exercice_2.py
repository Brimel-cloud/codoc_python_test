import importlib
import subprocess
import pkg_resources

#Dans un premier temps j'écris la fonction qui permets d'installer les librairies que je vais utiliser, cela c'est pour au cas où la librairie n'existe pas 
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
install_and_check_version("docx")
install_and_check_version("PyPDF2")



import os
import re
import glob
import sqlite3
from docx import Document
from PyPDF2 import PdfReader
import dateutil.parser
from datetime import datetime

# Connexion à la base de données
connexion = sqlite3.connect('drwh.db')
curseur = connexion.cursor()

# Fonction pour extraire le contenu texte d'un fichier DOCX avec les dates et l'auteur
def extraire_contenu_docx(chemin_fichier):
    document = Document(chemin_fichier)
    contenu = []
    dates = []
    auteurs = []
    for paragraphe in document.paragraphs:
        texte = paragraphe.text
        contenu.append(texte)
        date = extraire_date(texte)
        if date:
            dates.append(date)
        auteur = extraire_auteur(texte)
        if auteur:
            auteurs.append(auteur)
    return '\n'.join(contenu), dates, auteurs

# Fonction pour extraire le contenu texte d'un fichier PDF avec les dates et l'auteur
def extraire_contenu_pdf(chemin_fichier):
    with open(chemin_fichier, 'rb') as fichier:
        pdf = PdfReader(fichier)
        contenu = []
        dates = []
        auteurs = []
        for page in pdf.pages:
            texte = page.extract_text()
            contenu.append(texte)
            date = extraire_date(texte)
            if date:
                dates.append(date)
            auteur = extraire_auteur(texte)
            if auteur:
                auteurs.append(auteur)
        return '\n'.join(contenu), dates, auteurs

# Fonction pour extraire la date d'un texte
def extraire_date(texte):
    # J'utilise ici des expressions régulières pour extraire la date au format souhaité
    date = None
    # Exemple : extraire une date au format "dd/mm/yyyy"
    match = re.search(r'(\d{2}/\d{2}/\d{4})', texte)
    if match:
        date = dateutil.parser.parse(match.group(1), dayfirst=True).date()
    return date

# Fonction pour extraire l'auteur d'un texte
def extraire_auteur(texte):
    # De même j'utilise ici des expressions régulières pour extraire l'auteur en faisant une recherche par Dr ou Dr.
    auteur = None
    auteur_regex = r"Dr\.?\s+(.+)"

    # Recherche de l'auteur à la fin du texte
    match = re.search(auteur_regex, texte)
    if match:
        auteur = match.group(1)
        return 'Dr. '+auteur
    else:
        return auteur


# Chemin du répertoire contenant les fichiers de comptes rendus
repertoire_script = os.path.dirname(os.path.abspath(__file__))
repertoire_comptes_rendus = os.path.join(repertoire_script, 'fichiers_source')

# Récupération des fichiers de comptes rendus dans le répertoire de fichiers
fichiers = glob.glob(os.path.join(repertoire_comptes_rendus, '*.pdf')) + \
           glob.glob(os.path.join(repertoire_comptes_rendus, '*.docx'))


for fichier in fichiers:
    
    nom_fichier = os.path.basename(fichier)
    match = re.match(r'(\d+)_(\d+)\.(pdf|docx)', nom_fichier)
    
    if match:
        ipp = match.group(1)
        id_document = match.group(2)
        extension = match.group(3)
        
        # Extraction du contenu texte du fichier, des dates et auteurs
        if extension == 'pdf':
            contenu, dates, auteurs = extraire_contenu_pdf(fichier)
            source_document = 'DOSSIER_PATIENT'
        elif extension == 'docx':
            contenu, dates, auteurs = extraire_contenu_docx(fichier)
            source_document = 'RADIOLOGIE_SOFTWARE'
        
    print('contenu: ', contenu)
    print('dates: ', dates)
    print('auteurs: ', auteurs)

    # Récupération de la dernière valeur de la liste dates
    # Car cette dernière valeur correspond à la date du compte rendu (DOCUMENT_DATE)
    if dates:
        good_date = dates[-1]
    else:
        good_date = None
    

    # Récupération de la dernière valeur de la liste auteurs
    # De même l'auteur est la dernière valeur de cette liste car il se trouve à la fin du compte rendu
    if auteurs:
        autor = auteurs[-1]
    else:
        autor = None
    
    # On transforme ensuite le type des données ou variables pour faciliter l'insertion dans la base de données
    good_date = good_date.strftime("%d/%m/%Y")
    autor = str(autor)
    ipp = int(ipp)
    id_document = int(id_document)

    print(good_date)
    
    #Etant donné que le champ document_num est unique on verifie d'abord si elle existe dans la base de donnée
    #Si oui on fait un update de la ligne et sinon on ajoute cette nouvelle ligne dans la base de données
    
    # Vérification de l'existence de la valeur de document_num dans la table DWH_DOCUMENT
    curseur.execute("SELECT COUNT(*) FROM DWH_DOCUMENT WHERE DOCUMENT_NUM = ?", (id_document,))
    result = curseur.fetchone()

    if result[0] > 0:
        # La valeur existe déjà, on remplace la ligne correspondante
        curseur.execute("""
            UPDATE DWH_DOCUMENT
            SET PATIENT_NUM = (SELECT PATIENT_NUM FROM DWH_PATIENT_IPPHIST WHERE HOSPITAL_PATIENT_ID = ?),
                DOCUMENT_ORIGIN_CODE = ?,
                DOCUMENT_DATE = ?,
                ID_DOC_SOURCE = ?,
                DISPLAYED_TEXT = ?,
                AUTHOR = ?
            WHERE DOCUMENT_NUM = ?
        """, (ipp, source_document, good_date, id_document, contenu, autor, id_document))
    else:
        # La valeur n'existe pas, on ajoute une nouvelle ligne
        curseur.execute("""
            INSERT INTO DWH_DOCUMENT (
                DOCUMENT_NUM, PATIENT_NUM, ENCOUNTER_NUM, TITLE, DOCUMENT_ORIGIN_CODE,
                DOCUMENT_DATE, ID_DOC_SOURCE, DOCUMENT_TYPE, DISPLAYED_TEXT, AUTHOR,
                UNIT_CODE, UNIT_NUM, DEPARTMENT_NUM, EXTRACTCONTEXT_DONE_FLAG,
                EXTRACTCONCEPT_DONE_FLAG, ENRGENE_DONE_FLAG, ENRICHTEXT_DONE_FLAG,
                UPDATE_DATE, UPLOAD_ID
            ) VALUES (?, (SELECT PATIENT_NUM FROM DWH_PATIENT_IPPHIST WHERE HOSPITAL_PATIENT_ID = ?),
            NULL, NULL, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
        """, (id_document, ipp, source_document, good_date, id_document, 'Compte Rendu', contenu, autor))

    
    

# Exécution de la requête SELECT pour voir le contenu de la table DWH_DOCUMENT et voir si les données ont été ajoutées avec succès
curseur.execute("SELECT * FROM DWH_DOCUMENT")
resultats = curseur.fetchall()

# Affichage des résultats
for ligne in resultats:
    print(ligne)


print("***************fin******************")
print("Les documents ont été ajoutéS avec succès")
print("************************************")
# Validation des modifications dans la base de données
connexion.commit()

# Fermeture de la connexion à la base de données
connexion.close()


## copyright Brimel NJINKOUE