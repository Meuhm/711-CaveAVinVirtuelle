import sqlite3
from typing import List, Optional
import bcrypt
import logging.config
LOGGER = logging.getLogger(__name__)
import string
from itertools import product
import os
import re
import statistics
from datetime import datetime




# ================================
# Création de la base de données #
# ================================

class DB:
    def __init__(self, db_name="caves_virtuelles.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.creer_tables()

    def creer_tables(self):
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS bouteilles
                    (id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        domaine
                        TEXT,
                        nom
                        TEXT,
                        type_vin
                        TEXT,
                        annee
                        TEXT,
                        region
                        TEXT,
                        commentaire
                        TEXT,
                        note_personnelle
                        FLOAT,
                        photo_etiquette
                        TEXT,
                        prix
                        FLOAT,
                        cave_id
                        INTEGER,
                        FOREIGN KEY(cave_id) REFERENCES caves(id))""")
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS utilisateurs
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        nom
                        TEXT,
                        prenom
                        TEXT,
                         login
                        TEXT,
                        mot_de_passe
                        TEXT,
                        email
                        TEXT                       
                    )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS caves(id INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        utilisateur_id INTEGER,
                        FOREIGN KEY(utilisateur_id) REFERENCES utilisateurs(id)
                    )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS emplacements(id INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        etagere TEXT, 
                        numero INTEGER, 
                        cave_id INTEGER, 
                        bouteille_id INTEGER,
                        FOREIGN KEY(cave_id) REFERENCES caves(id)
                        FOREIGN KEY(bouteille_id) REFERENCES bouteilles(id)
                    )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS regions(id INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               nom TEXT
                           )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS etageres (id INTEGER
                                               PRIMARY
                                               KEY
                                               AUTOINCREMENT,
                                               nom INTEGER,
                                               nombre_emplacements INTEGER,
                                               cave_id INTEGER,
                                               FOREIGN KEY(cave_id) REFERENCES caves(id)
                                           )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS anoter (id INTEGER
                                       PRIMARY
                                       KEY
                                       AUTOINCREMENT,
                                       bouteille_id INTEGER,
                                       cave_id INTEGER,
                                       date_sortie DATE
                                   )""")
        self.conn.commit()



# ======================
#     Bouteille        #
# ======================
class Bouteille(DB):
    def __init__(self,  domaine:str, nom: str, type_vin: str, annee: str, region: str, commentaire: str, note_personnelle: float, photo_etiquette:str, prix: float, cave_id:int,  id: Optional[int] = None, conn=None):
        self.id = id
        self.domaine = domaine
        self.nom = nom
        self.type_vin = type_vin
        self.annee = annee
        self.region = region
        self.commentaire =  commentaire
        self.note_personnelle = note_personnelle
        self.photo_etiquette = photo_etiquette
        self.prix = prix
        self.cave_id =cave_id
        self.conn = conn

    def inserer_bouteille(self):
        """Intéger les caractéristiques d'un objet bouteille dans la table bouteilles"""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO bouteilles (domaine, nom, type_vin, annee, region, commentaire, note_personnelle,  "
            "photo_etiquette, prix,  cave_id) VALUES (?, ?, ?, ?, ?,  ?, ?, ?, ?, ?)",
            ( self.domaine, self.nom, self.type_vin, self.annee, self.region, self.commentaire, self.note_personnelle,
              self.photo_etiquette, self.prix,  self.cave_id)
        )
        self.conn.commit()
        self.id_bouteille = cur.lastrowid
        return self.id_bouteille


    @staticmethod
    def supprimer_bouteille(id, conn):
        """Supprimer une bouteille de la base de données sans en conserver une archive."""
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM bouteilles WHERE id = ?", (id,)
        )
        conn.commit()
        return


    def modifier_bouteille(self, domaine, nom, type_vin, annee, region,
                           commentaire, note_personnelle,photo_etiquette, prix):
        """Permet de modifier les caractéristiques (hors id et emplacement) de toutes les bouteilles identiques"""
        cur = self.conn.cursor()
        cur.execute("""
                       SELECT domaine, nom, type_vin, annee, region FROM bouteilles WHERE id = ?
                   """, (self.id,))
        modele = cur.fetchone()
        if modele:
            cur.execute("""UPDATE bouteilles SET domaine = ?, nom = ?, type_vin = ?, annee = ?, 
            region =?, commentaire = ?, note_personnelle = ?, photo_etiquette= ?, prix = ? WHERE domaine = ? AND nom = ?
                     AND type_vin = ? AND annee = ? AND region = ? """, (domaine, nom, type_vin, annee, region, commentaire, note_personnelle, photo_etiquette, prix,  modele["domaine"], modele["nom"], modele["type_vin"], modele["annee"], modele["region"]
            ))
            self.conn.commit()
            return True

    @staticmethod
    def noter(id, note_personnelle, conn):
        """Ajouter une note sur une bouteille et sur toutes celle qui sont identiques et appartiennent à la même cave"""
        cur = conn.cursor()
        cur.execute("""
            SELECT domaine, nom, type_vin, annee, region, cave_id FROM bouteilles
            WHERE id = ?""", (id,))
        modele = cur.fetchone()
        if modele:
            cur.execute("""
                UPDATE bouteilles
                SET note_personnelle = ?
                WHERE cave_id= ? AND domaine = ? AND nom = ? AND type_vin = ? AND annee = ? AND region = ?""",
                        (note_personnelle, modele["cave_id"],
                modele["domaine"], modele["nom"], modele["type_vin"], modele["annee"], modele["region"]
            ))
            conn.commit()
            return


    @staticmethod
    def commenter(id, commentaire, conn):
        """Ajouter un commentaire sur une bouteille et sur toutes celle qui sont identiques et appartiennent à la même cave"""
        cur = conn.cursor()
        cur.execute("""
               SELECT domaine, nom, type_vin, annee, region, cave_id FROM bouteilles WHERE id = ?
           """, (id,))
        modele = cur.fetchone()
        if modele:
            cur.execute("""
                   UPDATE bouteilles SET commentaire = ?
                   WHERE cave_id = ? AND domaine = ? AND nom = ? AND type_vin = ? AND annee = ? AND region = ?
               """, (
                commentaire, modele["cave_id"],
                modele["domaine"], modele["nom"], modele["type_vin"], modele["annee"], modele["region"]
            ))
            conn.commit()


    @staticmethod
    def obtenir(cave_id, conn) -> List["Bouteille"]:
        """Obtenir la liste de toutes les bouteilles présentes dans la cave"""
        cur = conn.cursor()
        cur.execute("SELECT * FROM bouteilles WHERE cave_id = ?", (cave_id,))

        return [Bouteille(row["domaine"],row["nom"], row["type_vin"], row["annee"], row["region"], row["commentaire"],
                          row["note_personnelle"],row["photo_etiquette"], row["prix"],  row["cave_id"],  row["id"] , conn=conn)
                for row in cur.fetchall()]


    @staticmethod
    def obtenir_avec_emplacement(cave_id, conn, domaine:Optional[str] = None, nom:Optional[str] = None, region:Optional[str] = None, type_vin:Optional[str] = None, annee:Optional[str] = None, prix_min:Optional[float] = None,prix_max:Optional[float] = None,note_min:Optional[float] = None,note_max:Optional[float] = None) :
        """Obtenir la liste de toutes les bouteilles présentes dans la cave avec leur emplacement."""
        cur = conn.cursor()
        requete = """ SELECT B.*, E.etagere, E.numero FROM bouteilles AS B INNER JOIN emplacements AS E
                ON B.cave_id = E.cave_id AND B.id = E.bouteille_id WHERE B.cave_id = ?
              AND E.bouteille_id IS NOT NULL
        """
        criteres = [cave_id]
        if domaine:
            requete += " UPPER(B.domaine) LIKE ?"
            criteres.append(domaine)
        if nom:
            requete += " AND UPPER(B.nom) LIKE ? "
            criteres.append(nom)
        if region:
            requete += " AND B.region = ?"
            criteres.append(region)
        if type_vin:
            requete += " AND B.type_vin = ?"
            criteres.append(type_vin)
        if annee :
            requete += " AND B.annee = ?"
            criteres.append(annee)
        if prix_min :
            requete += " AND B.prix > ?"
            criteres.append(prix_min)
        if prix_max:
            requete += " AND B.prix < ?"
            criteres.append(prix_max)
        if note_min:
            requete += " AND B.note_personnelle > ?"
            criteres.append(note_min)
        if note_max:
            requete += " AND B.note_personnelle < ?"
            criteres.append(note_max)
        cur.execute(requete, tuple(criteres))
        dico_bouteilles = {}
        for row in cur.fetchall():
            etagere = row["etagere"]
            if etagere not in dico_bouteilles:
                dico_bouteilles[etagere] = []
            dico_bouteilles[etagere].append({
            "numero": row["numero"],
            "bouteille": Bouteille(row["domaine"],row["nom"], row["type_vin"], row["annee"], row["region"], row["commentaire"],
                      row["note_personnelle"],row["photo_etiquette"], row["prix"],  row["cave_id"], row["id"], conn=conn)
                         })
        print(dico_bouteilles)
        return dico_bouteilles


    @staticmethod
    def obtenir_presentes_sans_emplacement(cave_id, conn, domaine: Optional[str] = None, nom: Optional[str] = None,
                                 region: Optional[str] = None, type_vin: Optional[str] = None,
                                 annee: Optional[str] = None, prix_min: Optional[float] = None,
                                 prix_max: Optional[float] = None, note_min: Optional[float] = None,
                                 note_max: Optional[float] = None):
        """Obtenir la liste de toutes les bouteilles présentes dans la table bouteilles qui ont un emplacement (donc non archivées),
        mais sans retourner l'emplacement."""
        cur = conn.cursor()
        requete = """ SELECT  B.*  FROM bouteilles AS B LEFT JOIN emplacements AS E
                     ON B.cave_id = E.cave_id AND B.id == E.bouteille_id WHERE B.cave_id = ? AND E.bouteille_id IS NOT NULL

             """
        criteres = [cave_id]
        if domaine:
            requete += " AND UPPER(B.domaine) LIKE ?"
            criteres.append(domaine)
        if nom:
            requete += " AND UPPER(B.nom) LIKE ?"
            criteres.append(nom)
        if region:
            requete += " AND B.region = ?"
            criteres.append(region)
        if type_vin:
            requete += " AND B.type_vin = ?"
            criteres.append(type_vin)
        if annee:
            requete += " AND B.annee = ?"
            criteres.append(annee)
        if prix_min:
            requete += " AND B.prix > ?"
            criteres.append(prix_min)
        if prix_max:
            requete += " AND B.prix < ?"
            criteres.append(prix_max)
        if note_min:
            requete += " AND B.note_personnelle > ?"
            criteres.append(note_min)
        if note_max:
            requete += " AND B.note_personnelle < ?"
            criteres.append(note_max)
        cur.execute(requete, tuple(criteres))
        dico_bouteilles = {}
        for row in cur.fetchall():
            cle = (row["domaine"], row["nom"], row["region"], row["type_vin"], row["annee"])
            if cle not in dico_bouteilles.keys():
                dico_bouteilles[cle] = []
            dico_bouteilles[cle].append({
                "bouteille": Bouteille(
                    row["domaine"], row["nom"], row["type_vin"], row["annee"], row["region"],
                    row["commentaire"], row["note_personnelle"], row["photo_etiquette"],
                    row["prix"], row["cave_id"], row["id"], conn=conn
                )
            })
        print(f"ligne 313 de bdd vaut {dico_bouteilles}")
        return dico_bouteilles


    @staticmethod
    def obtenir_sans_emplacement(cave_id, conn, domaine: Optional[str] = None, nom: Optional[str] = None,
                                 region: Optional[str] = None, type_vin: Optional[str] = None,
                                 annee: Optional[str] = None, prix_min: Optional[float] = None,
                                 prix_max: Optional[float] = None, note_min: Optional[float] = None,
                                 note_max: Optional[float] = None):
        """Obtenir la liste de toutes les bouteilles présentes dans la table bouteilles, mais qui n'ont pas d'emplacement.
        Il s'agit des bouteilles archivées."""
        cur = conn.cursor()
        requete = """ SELECT  B.*  FROM bouteilles AS B LEFT JOIN emplacements AS E
                 ON B.cave_id = E.cave_id AND B.id == E.bouteille_id WHERE B.cave_id = ? AND E.bouteille_id IS NULL
               
         """
        criteres = [cave_id]
        if domaine:
            requete += " AND UPPER(B.domaine) LIKE ?"
            criteres.append(domaine)
        if nom:
            requete += " AND UPPER(B.nom) LIKE ?"
            criteres.append(nom)
        if region:
            requete += " AND B.region = ?"
            criteres.append(region)
        if type_vin:
            requete += " AND B.type_vin = ?"
            criteres.append(type_vin)
        if annee:
            requete += " AND B.annee = ?"
            criteres.append(annee)
        if prix_min:
            requete += " AND B.prix > ?"
            criteres.append(prix_min)
        if prix_max:
            requete += " AND B.prix < ?"
            criteres.append(prix_max)
        if note_min:
            requete += " AND B.note_personnelle > ?"
            criteres.append(note_min)
        if note_max:
            requete += " AND B.note_personnelle < ?"
            criteres.append(note_max)
        cur.execute(requete, tuple(criteres))
        dico_bouteilles = {}
        for row in cur.fetchall():
            cle = (row["domaine"], row["nom"], row["region"], row["type_vin"], row["annee"])
            if cle not in dico_bouteilles.keys():
                dico_bouteilles[cle] = []
            dico_bouteilles[cle].append({
                "bouteille": Bouteille(
                    row["domaine"], row["nom"], row["type_vin"], row["annee"], row["region"],
                    row["commentaire"], row["note_personnelle"], row["photo_etiquette"],
                    row["prix"], row["cave_id"], row["id"], conn=conn
                )
            })
        print(f"ligne 313 de bdd vaut {dico_bouteilles}")
        return dico_bouteilles


    @staticmethod
    def obtenir_caracteristiques_bouteille(id, conn):
        """Obtenir les caracteristiques d'une seule bouteille à partir de son id."""
        cur = conn.cursor()
        cur.execute("SELECT * FROM bouteilles WHERE id = ? ", (id,))
        row = cur.fetchone()
        return Bouteille(row["domaine"], row["nom"], row["type_vin"], row["annee"], row["region"], row["commentaire"],
                          row["note_personnelle"], row["photo_etiquette"], row["prix"],  row["cave_id"],
                          row["id"], conn=conn)



    def obtenir_moyenne_de_notes_perso_bouteilles_identiques(self) :
        """Obtenir la moyenne des notes personnelles de tous les utilisateurs ayant une bouteille identique (la note donnée
        par un utilisateur (pour une cave) est comptée une seule fois quel que soit le nombre de bouteilles
         possédé par chacun des utlisateurs """
        cur = self.conn.cursor()
        cur.execute("""WITH modele AS (
        SELECT domaine, nom, type_vin, annee, region
        FROM bouteilles
        WHERE id = ?
        )
        SELECT ROUND(AVG(note_moyenne_par_cave), 1) AS moyenne
        FROM (
        SELECT b.cave_id, AVG(b.note_personnelle) AS note_moyenne_par_cave
        FROM bouteilles AS b
        JOIN modele AS m
          ON UPPER(TRIM(b.domaine)) = UPPER(TRIM(m.domaine))
         AND UPPER(TRIM(b.nom)) = UPPER(TRIM(m.nom))
         AND UPPER(TRIM(b.type_vin)) = UPPER(TRIM(m.type_vin))
         AND b.annee = m.annee
         AND UPPER(TRIM(b.region)) = UPPER(TRIM(m.region))
        WHERE b.note_personnelle IS NOT NULL
          AND b.note_personnelle > 0
        GROUP BY b.cave_id
         )   
        """, (self.id,))
        row = cur.fetchone()
        if row and row[0] is not None:
            moyenne = row[0]
        else:
            moyenne =  None
        return moyenne


    @staticmethod
    def recuperer_liste_images_locales():
        """Récupérer toutes les images d'étiquettes et les retourner dans une liste."""
        images_folder = 'static/images'
        image_extensions = {'.png', '.jpg', '.jpeg', '.jfif','.gif', '.bmp', '.webp'}
        liste_images = []
        for root, dirs, files in os.walk(images_folder):
            for file in files:
                if os.path.splitext(file)[1].lower() in image_extensions:
                    liste_images.append(os.path.join(root, file))
        return liste_images



# ======================
#     Etagere          #
# ======================
class Etagere(DB):
    def __init__(self,  nom : str, nombre_emplacements:int, cave_id: int,  id: Optional[int] = None, conn=None):
        self.nom = nom
        self.nombre_emplacements = nombre_emplacements
        #self.vide = vide
        self.cave_id = cave_id
        self.id = id
        self.conn = conn

    def creer_etagere(self):
        """Ajout des caractéristiques de l'objet etagere dans la table etageres"""
        cur = self.conn.cursor()
        cur.execute('''
                       INSERT INTO etageres (nom, nombre_emplacements, cave_id)
                       VALUES (?, ?, ?)
                       ''', (self.nom, self.nombre_emplacements, self.cave_id,))
        self.conn.commit()
        self.id = cur.lastrowid
        return self.id


    @staticmethod
    def creation_id_etageres():
        """créer une liste de 500 noms d'étageres à partir de l'alphabet"""
        alphabet = list(string.ascii_uppercase)
        liste_nom_etageres = []
        liste_nom_etageres.extend(alphabet)
        length = 2
        while len(liste_nom_etageres) < 500:
            for combo in product(alphabet, repeat=length):
                liste_nom_etageres.append(''.join(combo))
                if len(liste_nom_etageres) == 500:
                    break
            length += 1
        return liste_nom_etageres


    @staticmethod
    def trouver_derniere_etagere(cave_id, conn):
        """Trouver le nom de la dernière étagère pour une cave donnée (à partir de l'identifiant de cette dernière)."""
        cur = conn.cursor()
        cur.execute("SELECT nom FROM etageres WHERE cave_id = ? ORDER BY id DESC LIMIT 1 ", (cave_id,))
        row = cur.fetchone()
        print(f"ligne 458 {row['nom']}")
        return row["nom"]


    @staticmethod
    def nouvelle_etagere(cave_id:int, nombre_emplacements:int, conn):
        """Création d'un seul nouvel objet étagère et de tous les objets emplacements correspondant."""
        liste_noms_etageres = Etagere.creation_id_etageres()
        try:
            derniere_etagere = Etagere.trouver_derniere_etagere(cave_id, conn)
            print(f"derniere_etagere {derniere_etagere}")
            ancien_index = liste_noms_etageres.index(derniere_etagere)
            print(f"ancien_index: {ancien_index}")
            nom = liste_noms_etageres[ancien_index+1]
            print(f"nom ligne 472 {nom}")
        except:
            nom = "A"
        #print(f"etagere: {nom}")
        new_etagere = Etagere(nom, nombre_emplacements, cave_id, conn=conn)
        new_etagere.creer_etagere()
        for i in range(nombre_emplacements):
            numero = i+1
            new_emplacement = Emplacement(nom, int(numero), int(cave_id), None, conn=conn)
            new_emplacement.creer_emplacement()
        return nom


    @staticmethod
    def creer_plusieurs_etageres(cave_id, dico_etageres, conn):
        """Créer plusieurs etagères et les emplacements correspondants à partir d'un dictionnaire
        dont la clé est le nom de l'étagère et la valeur le nombre d'emplacements de cette étagère."""
        for key in dico_etageres.keys():
            print(f"{key}: {dico_etageres[key]}")
            for i in range(int(dico_etageres[key][0])):
                Etagere.nouvelle_etagere(int(cave_id), int(dico_etageres[key][1]), conn)
        return


    @staticmethod
    def lister_etageres(cave_id, conn):
        """Obtenir la liste de toutes les étagères d'une cave donnée."""
        cur = conn.execute(
            "SELECT DISTINCT nom FROM etageres WHERE cave_id =?",
            (cave_id,))
        liste_etageres = []
        for row in cur.fetchall():
            liste_etageres.append(row["nom"])
        return liste_etageres


    @staticmethod
    def nombre_total_emplacements(cave_id, conn):
        """Obtenir le nombre total d'emplacements d'une cave."""
        cur = conn.execute(
            "SELECT SUM(nombre_emplacements) as total FROM etageres WHERE cave_id =?",
            (cave_id,))
        return cur.fetchone()["total"]


# ======================
#     Emplacement      #
# ======================
class Emplacement(DB):
    def __init__(self,  etagere: str, numero:int, cave_id: int, bouteille_id = None,  id: Optional[int] = None, conn=None):
        self.etagere = etagere
        self.numero = numero
        #self.vide = vide
        self.cave_id = cave_id
        self.bouteille_id = bouteille_id
        self.id = id
        self.conn = conn

    def creer_emplacement(self):
        """Ajout des caractéristiques de l'objet emplacement dans la table emplacements"""
        cur = self.conn.cursor()
        cur.execute('''
                    INSERT INTO emplacements (etagere, numero, cave_id, bouteille_id)
                    VALUES (?, ?, ?, ?)
                    ''', (self.etagere, self.numero, self.cave_id, self.bouteille_id))
        self.conn.commit()
        self.id = cur.lastrowid
        return self.id

    def setter_bouteille_id(self, bouteille_id):
        """Ajouter l'identifiant d'une bouteille dans un emplacement donné."""
        self.bouteille_id = bouteille_id
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE emplacements SET bouteille_id = ? WHERE id = ? ", (self.bouteille_id, self.id, )
        )
        self.conn.commit()


    def obtenir(cave_id, conn, vide:Optional)-> List["Emplacement"]:
        """Obtenir une liste des emplacements vides présents dans la table emplacements et seulement des emplacements
        vide si la variable "vide" est ajoutée dans les paramètres."""
        cur = conn.cursor()
        requete = "SELECT * FROM emplacements WHERE cave_id = ?"
        criteres=[cave_id]
        if vide == "vide":
            requete += " AND bouteille_id IS NULL"
        cur.execute(requete, tuple(criteres))
        res= [Emplacement( row['etagere'], row['numero'], row['bouteille_id'], id=row['id'], conn=conn) for row in cur.fetchall()]
        print(f"emplacements vides valent {res}")
        return res


    @staticmethod
    def obtenir_un_emplacement(cave_id, conn, id:Optional=None, etagere:Optional=None, numero:Optional=None ):
        """Retourne tous les emplacements d'une cave avec des critères optionnels tels que l'identifiant de
        l'emplacement, le nom de l'étagère, et le numéro de l'emplacement."""
        cur = conn.cursor()
        requete = ("SELECT * FROM emplacements WHERE cave_id = ?")
        criteres=[cave_id]
        # Ajout des filtres optionnels
        if  id:
            requete += " AND id = ?"
            criteres.append(id)
        if etagere:
            requete += " AND etagere = ?"
            criteres.append(etagere)
        if numero:
            requete += " AND numero = ?"
            criteres.append(numero)
        cur.execute(requete, tuple(criteres))
        row= cur.fetchone()
        return Emplacement(row['etagere'], row['numero'], row['cave_id'], row['bouteille_id'], id=row['id'], conn=conn)



    @staticmethod
    def obtenir_emplacements_avec_bouteilles_ou_vides(cave_id, conn):
        """Retourne tous les emplacements d'une cave dans un dictionnaire dont la clé est le
        nom de l'étagère, et les valeurs une liste de dictionnaires composés de cléss numero et bouteilles."""
        cur = conn.cursor()
        cur.execute ("""SELECT E.etagere as etagere, E.numero as numero, B.id as bouteille_id, B.nom as nom, 
        B.domaine as domaine, B.photo_etiquette as photo_etiquette FROM 
                emplacements AS E LEFT JOIN bouteilles AS B ON E.bouteille_id=B.id WHERE E.cave_id = ?
             """, (cave_id,))
        dico_bouteilles={}
        for row in cur.fetchall():
            etagere = row["etagere"]
            if etagere not in dico_bouteilles:
                dico_bouteilles[etagere] = []
            dico_bouteilles[etagere].append({
                "numero": row["numero"],
                "bouteille": {
                    "bouteille": row["bouteille_id"],
                    "nom": row["nom"],
                    "domaine": row["domaine"],
                    "photo_etiquette": row["photo_etiquette"]
                } if row["bouteille_id"] is not None else None
            })
        return dico_bouteilles


    @staticmethod
    def supprimer_emplacements(cave_id, etagere, conn):
        """Suppression de tous les emplacements d'une cave donnée et d'une étagère donnée dans la table emplacements."""
        cur = conn.cursor()
        try:
            cur.execute('''
                        DELETE  FROM emplacements WHERE cave_id=? AND etagere=? 
                        ''', (cave_id, etagere,))
            conn.commit()
            return
        except:
            print(f"L'étagère {etagere} n'existait pas.")


    @staticmethod
    def lister_etageres_vides(cave_id, conn):
        """Retourner une liste de liste comprenant le nom de l'etagere vide et le le nombre d'emplacements vides."""
        cur= conn.execute(
            "SELECT etagere , COUNT(numero) as nombre FROM emplacements WHERE cave_id =?  GROUP BY etagere HAVING COUNT (bouteille_id)=0 ORDER BY etagere",
            (cave_id, ))
        liste_etageres_vides =[]
        for row in cur.fetchall():
            liste_etageres_vides.append([row["etagere"], row["nombre"]])
        return liste_etageres_vides


    @staticmethod
    def vider_un_emplacements(bouteille_id, conn):
        """Supprimer l'identifiant d'une bouteille d'un emplacement."""
        cur = conn.cursor()
        cur.execute('''
                    UPDATE emplacements SET bouteille_id = NULL  WHERE bouteille_id=? 
                    ''', (bouteille_id,))
        conn.commit()
        return


# ======================
#     Anoter            #
# ======================

class Anoter(DB):

    def __init__(self, bouteille_id: int, cave_id, date_sortie, id: Optional[int] = None, conn=None):
        self.bouteille_id = bouteille_id
        self.cave_id = cave_id
        self.date_sortie = date_sortie
        self.id = id
        self.conn = conn


    def inserer_dans_liste(self):
        """Insérer dans la table anoter les caractéristiques d'un objet Anoter."""
        cur = self.conn.cursor()
        cur.execute("""INSERT INTO anoter (bouteille_id, cave_id, date_sortie)
                       VALUES (?, ?, ?)""", (self.bouteille_id, self.cave_id, self.date_sortie))
        self.conn.commit()
        self.id = cur.lastrowid
        return self.id


    @staticmethod
    def retirer_bouteille_de_liste(bouteille_id, conn):
        """Supprimer toutes les caractéristiques d'un objet Anoter de la table anoter."""
        cur = conn.cursor()
        cur.execute("""DELETE  FROM anoter WHERE bouteille_id =?""", (bouteille_id,))
        conn.commit()
        return


    @staticmethod
    def obtenir_liste(cave_id, conn):
        """"Retourner la liste de tous les identifiants de bouteille contenus dans la table anoter."""
        cur = conn.cursor()
        cur.execute("SELECT bouteille_id, date_sortie FROM anoter WHERE cave_id=? ", (cave_id,))
        return [[row['bouteille_id'], row['date_sortie']] for row in cur.fetchall()]


# ======================
#     Cave             #
# ======================
class Cave(DB):
    def __init__(self,  utilisateur_id:int,  id: Optional[int] = None, conn=None):
        self.utilisateur_id = utilisateur_id
        self.id = id
        self.conn = conn


    def ajouter_cave(self):
        """Ajout des caractéristiques de l'objet cave dans la table caves"""
        cur = self.conn.cursor()
        cur.execute('''
                       INSERT INTO caves (utilisateur_id) VALUES (?)
                       ''', ( self.utilisateur_id, ))
        self.conn.commit()
        self.id = cur.lastrowid
        return self.id

        
    def obtenir(conn)-> List["Cave"]:
        """Obtenir une liste des caves présentes dans la table"""
        cur = conn.cursor()
        cur.execute("SELECT * FROM caves ")
        return [Cave(row['utilisateur_id'], id=row['id'], conn=conn) for row in cur.fetchall()]


    @staticmethod
    def obtenir_proprietes_cave_par_id (id, conn):
        """Obtenir toutes les caractéristiques d'une cave grace à son id"""
        cur = conn.cursor()
        cur.execute("SELECT * FROM caves WHERE id = ?", (id,))
        row = cur.fetchone()
        if row:
            return Cave(row['utilisateur_id'], id=row['id'],
                        conn=conn)
        return None


    @staticmethod
    def obtenir_cave_par_utilisateur_id (utilisateur_id, conn ):
        """Obtenir la cave_id d'un utilisateur"""
        cur = conn.cursor()
        cur.execute("SELECT * FROM caves WHERE utilisateur_id = ?", (utilisateur_id,))
        row = cur.fetchone()
        return row['id']



# ======================
#     Utilisateur      #
# ======================
class Utilisateur(DB):
    def __init__(self, nom:str, prenom:str, login:str,  mot_de_passe, email:str,  id: Optional[int] = None,conn=None):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.login= login
        self.mot_de_passe = mot_de_passe
        self.email = email
        self.conn = conn


    def hash_mot_de_passe(self, mot_de_passe):
        """cryptage du mot de passe"""
        return bcrypt.hashpw(mot_de_passe.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")


    def ajouter_utilisateur(self):
        """Ajout des caractéristiques de l'objet utilisateur dans la table utilisateurs"""
        hashed_mot_de_passe = self.hash_mot_de_passe(self.mot_de_passe)
        cur = self.conn.cursor()
        cur.execute('''
                       INSERT INTO utilisateurs ( nom, prenom, login, mot_de_passe, email)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (self.nom, self.prenom, self.login, hashed_mot_de_passe, self.email))
        self.conn.commit()
        self.id = cur.lastrowid
        return self.id


    @staticmethod
    def chercher_un_utilisateur(login, conn):
        """Retourne un objet utilisateur trouvé grâce à son login ou none si rien n'est trouvé. """
        cur = conn.cursor()
        cur.execute("SELECT * FROM utilisateurs WHERE login = ?", (login,))
        row = cur.fetchone()
        if row:
            return Utilisateur(row['nom'], row['prenom'], row['login'], row['mot_de_passe'], row['email'], id=row['id'], conn=conn)
        return None


    @staticmethod
    def verifier_mot_de_passe(mot_de_passe, hash):
        """comparaison du mot de passe fournit lors de la connexion avec le hash contenu dans la table utilisateurs."""
        if isinstance(hash, memoryview):
            hash = bytes(hash)
        elif isinstance(hash, str):
            hash = hash.encode('utf-8')
        return bcrypt.checkpw(mot_de_passe.encode('utf-8'), hash)


    @staticmethod
    def check_login(login, mot_de_passe, conn):
        """vérification si le mot de passe fourni lors de la connexion correspond au login fourni au même moment"""
        user = Utilisateur.chercher_un_utilisateur(login, conn)
        if user and user.mot_de_passe:
            return Utilisateur.verifier_mot_de_passe(mot_de_passe, user.mot_de_passe)
        return False


# ======================
#        Region        #
# ======================
class Region(DB):
    def __init__(self, nom:str,id: Optional[int] = None,conn=None):
        self.id = id
        self.nom = nom
        self.conn = conn

    def ajouter_region(self):
        """ajouter une région dans la table régions des régions viticoles"""
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM regions WHERE nom = ?", (self.nom,))
        row = cur.fetchone()
        if row:
            self.id = row['id']
        else:
            cur.execute("INSERT INTO regions (nom) VALUES (?)", (self.nom,))
            self.conn.commit()
            self.id = cur.lastrowid
        return self.id

    @staticmethod
    def toutes_les_regions(conn):
        """Obtenir une liste de toutes les régions présentes dans la table du même nom."""
        cur = conn.cursor()
        cur.execute("SELECT * FROM regions ")
        return cur.fetchall()


# ======================
#        Divers        #
# ======================

def to_float(value):
    if value is None or value.strip() == '':
        return None
    return float(value.replace(',', '.'))


def lettres_en_base26(lettres):
    """Convertir une chaîne de lettres en un entier type base 26 : A=1, B=2, ..., Z=26, AA=27, AB=28, etc."""
    lettres = lettres.upper()
    total = 0
    for i, c in enumerate(reversed(lettres)):
        if 'A' <= c <= 'Z':
            total += (ord(c) - ord('A') + 1) * (26 ** i)
        else:
            return None
    return total

def tri_etagere_cle(valeur):
    """    Renvoie une clé pour trier les étagères : lettres d'abord (base26), puis nombre si présent."""
    if valeur is None:
        return (0, 0)
    match = re.match(r'^([A-Z]+)([0-9]*)$', valeur.upper())
    if not match:
        return (float('inf'), float('inf'))
    lettres, chiffres = match.groups()
    lettres_val = lettres_en_base26(lettres)
    chiffres_val = int(chiffres) if chiffres else 0
    return (lettres_val, chiffres_val)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, encoding="utf-8")
    db = DB()
    #DB.creer_tables(db)
    #new_user =Utilisateur( "TOMATE", "Cerise", "cerise ","cerise", conn=db.conn)
    #new_user.ajouter_utilisateur()

    #print(new_cave)
    #new_cave.ajouter_cave()

    # new_bouteilles = Bouteille("Rayne", "Châteaneuf du Pape","rouge",2012,"Côte du Rhône","", 0, "static/images/ChateauNeuf.jfif", 0,1,True, 3,  conn=db.conn)
    # for new_bouteille in new_bouteilles:
    #     Bouteille.inserer_bouteille(new_bouteille)
    #
    liste =['Bordeaux', 'Loire','Bourgogne','Côte-du-Rhône', "Beaujolais",'Alsace', 'Jura', 'Savoie', 'Auvergne', "Sud-Ouest",'Sud-Ouest', 'Languedoc-Roussillon','Corse', 'Champagne', 'Vins du Monde | Italie', 'Vins du Monde | Argentine', 'Vins du Monde | Ecosse' ]
    for nom_region in liste :
         new_region =Region(nom_region, conn=db.conn)
         new_region.ajouter_region()

    # print(Emplacement.compter_emplacements_vides_par_etagere(18, "A", db.conn))
    # print(Emplacement.chercher_premier_emplacement_vide_etagere(18, "A", db.conn))
    # print(Emplacement.lister_etageres(18, db.conn))
    # ici_cave = Cave.obtenir_proprietes_cave_par_id(18, db.conn)
    # print(Emplacement.creer_nouvelle_etagere(ici_cave, db.conn))
    #Emplacement.vider_un_emplacements(8, db.conn)
    #print(datetime.now())
    #bouteille_a_noter = Anoter(9, datetime.now(), conn=db.conn)
    #bouteille_a_noter.inserer_dans_liste()
    #Bouteille.noter(9, 25, db.conn)
    #print(Emplacement.lister_etageres_vides(18,db.conn))
