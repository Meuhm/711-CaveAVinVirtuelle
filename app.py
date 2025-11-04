import flask_session

import bdd
from bdd import DB, Cave, Utilisateur, Bouteille, Etagere, Emplacement, Region, Anoter
from flask import Flask, render_template, request, redirect, url_for, flash, abort, current_app, session
import jinja2
#import flask-session
import flask_session
#conn = db.conn
from datetime import datetime
import os, shutil
import re

app = Flask(__name__)

app.secret_key = 'my_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'

# Nettoyer au démarrage
if os.path.exists(app.config['SESSION_FILE_DIR']):
    shutil.rmtree(app.config['SESSION_FILE_DIR'], ignore_errors=True)
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

flask_session.Session(app)
db = DB()
conn = db.conn


@app.template_filter()
def affichage_prix(valeur):
    return f"{valeur:.2f}".replace('.', ',')

@app.template_filter()
def affichage_note(valeur):
    if valeur == 0.0 :
        return "Néant"
    elif str(valeur).endswith(".0"):
        avec_virgule = str(valeur).replace('.0', '') + "/20"
        return avec_virgule
    else:
        avec_virgule= str(valeur).replace('.', ',') + "/20"
        return avec_virgule

@app.template_filter()
def affichage_ordre_naturel(valeur):
    if valeur is None:
        return []
    return [int(t) if t.isdigit() else t for t in re.split('([0-9]+)', valeur)]

@app.template_filter()
def nom_image(valeur):
    sans_chemin= os.path.basename(valeur)
    sans_chemin.split(".")[0]
    return sans_chemin.split(".")[0]


####################################
#   GESTION AUTHENTIFICATION       #
####################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Page pour se loguer """
    utilisateur =""
    if request.method == "POST":
        password = request.form.get('mot_de_passe')
        login = request.form.get('login')
        if password and login:
            try :
                if bdd.Utilisateur.check_login(login, password, conn):
                    session['login'] = login
                    u = Utilisateur.chercher_un_utilisateur(login, conn=conn)
                    print(u)
                    print(type(u))
                    session['id'] = u.id
                    flash('Connexion réussie', 'success')
                    current_app.logger.info('Connexion de "' + login + '"')
                    return redirect(url_for('accueil'))
                else:
                    flash('Identifiant ou mot de passe invalide(s)', 'error')
                    current_app.logger.info('Tentative de connexion de "' + login + '"')

            except:
                flash('Identifiant ou mot de passe invalide(s)', 'error')
                current_app.logger.info('Tentative de connexion de "' + login + '"')
            return redirect(url_for('login'))
        elif password or login :
            flash('Veuillez renseigner les 2 champs', 'error')
            return render_template('login.html')
        else :
            return render_template('login.html')
    else:
        return render_template('login.html', utilisateur=utilisateur)


@app.route('/deconnexion', methods=['GET', 'POST'])
def deconnexion():
    """Permet retirer l'utilisateur des utilisateurs identifiés en cas de déconnexion
    et d'afficher la page de connnexion."""
    if 'login' in session:
        session.pop('login')
        #print(f"flask.session login vaut {session['login']}")
        flash("Déconnexion réussie ! A bientôt.", "success")
    else:
        flash("Vous n'étiez pas connecté.", "avertissement")
    return redirect(url_for('login'))


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/accueil', methods=['GET', 'POST'])
def accueil(bouteille_id=None):
    """La page d'accueil, si logué """
    if 'login' in session:
        login= session['login']
        user = Utilisateur.chercher_un_utilisateur(login, conn=conn)
        utilisateur = user.prenom + " " + user.nom
        utilisateur_id = session['id']
        cave_id = Cave.obtenir_cave_par_utilisateur_id(utilisateur_id, conn=conn)
        dico_bouteilles_a_noter ={}
        liste_bouteilles_a_noter = Anoter.obtenir_liste(cave_id, conn=conn)
        dico_bouteilles_non_triees =Emplacement.obtenir_emplacements_avec_bouteilles_ou_vides(cave_id, conn=conn)
        dico_bouteilles = dict(sorted(dico_bouteilles_non_triees.items(), key=lambda item: bdd.tri_etagere_cle(item[0])))
        for bouteille_id in liste_bouteilles_a_noter :
            dico_bouteilles_a_noter[bouteille_id[0]] = Bouteille.obtenir_caracteristiques_bouteille(bouteille_id[0], conn=conn)
        return render_template('accueil.html', utilisateur=utilisateur, dico_bouteilles_a_noter=dico_bouteilles_a_noter, dico_bouteilles=dico_bouteilles)
    else:
        return redirect(url_for('login'))


@app.route('/noter', methods=['GET', 'POST'])
def noter():
    if 'login' in session:
        login = session['login']
        user = Utilisateur.chercher_un_utilisateur(login, conn)
        utilisateur = user.prenom + " " + user.nom
        utilisateur_id = session['id']
        cave_id = Cave.obtenir_cave_par_utilisateur_id(utilisateur_id, conn=conn)
        dico_bouteilles = Emplacement.obtenir_emplacements_avec_bouteilles_ou_vides(cave_id, conn=conn)
        dico_bouteilles_a_noter ={}
        liste_bouteilles_a_noter = Anoter.obtenir_liste(cave_id, conn=conn)
        if request.method == 'POST':
            for bouteille in liste_bouteilles_a_noter:
                note = request.form.get(f'note_personnelle_{bouteille[0]}')
                commentaire = request.form.get(f'commentaire_{bouteille[0]}')
                if note :
                    Bouteille.noter(int(bouteille[0]),note, conn=conn)
                    Anoter.retirer_bouteille_de_liste(bouteille[0], conn=conn)
                if commentaire:
                    Bouteille.commenter(int(bouteille[0]),commentaire, conn=conn)

            liste_bouteilles_a_noter = Anoter.obtenir_liste(cave_id, conn=conn)
            for bouteille_id in liste_bouteilles_a_noter:
                dico_bouteilles_a_noter[bouteille_id[0]] = Bouteille.obtenir_caracteristiques_bouteille(bouteille_id[0], conn=conn)
            return render_template('accueil.html', utilisateur=utilisateur, dico_bouteilles_a_noter=dico_bouteilles_a_noter,dico_bouteilles=dico_bouteilles)
    else:
        return redirect(url_for('login'))


@app.route('/creerutilisateur', methods=['GET', 'POST'])
def creer_nouvel_utilisateur():
    """ Page pour créer le cave après la création du compte """
    # mettre ici une fonction qui va chercher le dernier ID bouteille de la cave de l'utilisateur et le met dans la variable ci-après
    utilisateur = ""
    if request.method == "POST":
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        login = request.form.get('login')
        mot_de_passe =request.form.get('mot_de_passe')
        email = request.form.get('email')
        dico_etageres ={}
        if request.form.get(f'nombre_etageres_{1}') and request.form.get(f"bouteilles_max_par_etagere_{ 1 }"):
            try:
                if Utilisateur.chercher_un_utilisateur(login, conn):
                    flash(f'Le login "{login}" est déjà utilisé par un autre membre. Veuillez recommencer', 'error')
                    return render_template('creerutilisateur.html')
                new_user= Utilisateur(nom,prenom,login,mot_de_passe,email, conn=conn)
                utilisateur_id= new_user.ajouter_utilisateur()
                session['login'] = login
                session['id'] = utilisateur_id
                for i in range(1, 11):
                    nombre_etageres = request.form.get(f'nombre_etageres_{i}')
                    bouteilles_max_par_etagere = request.form.get(f"bouteilles_max_par_etagere_{i}")
                    if nombre_etageres and bouteilles_max_par_etagere :
                        dico_etageres[i]=[nombre_etageres, bouteilles_max_par_etagere]
                new_cave = Cave(int(utilisateur_id), conn=conn)
                cave_id = new_cave.ajouter_cave()
                Etagere.creer_plusieurs_etageres(int(cave_id), dico_etageres, conn=conn)
                flash(f"Votre compte utilisateur avec le login {login} a été correctement créé.", "success")
                flash('Félicitations, votre cave virtuelle a été créée !', 'success')
                return redirect(url_for('accueil'))
            except Exception as e:
                print("Erreur:", e)
                session.pop('login', None)
                flash("Une erreur est survenue lors de la création du compte ou de la cave.", 'error')
                return render_template('creerutilisateur.html', utilisateur=utilisateur)
    return render_template('creerutilisateur.html', utilisateur=utilisateur)


@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter_bouteille():
    if 'login' in session:
        login = session['login']
        user = Utilisateur.chercher_un_utilisateur(login, conn=conn)
        utilisateur = user.prenom + " " + user.nom
        utilisateur_id = session['id']
        cave_id =Cave.obtenir_cave_par_utilisateur_id(utilisateur_id, conn)
        cave = Cave.obtenir_proprietes_cave_par_id(int(cave_id), conn)
        photos = Bouteille.recuperer_liste_images_locales()
        dico_bouteilles_non_triees = Emplacement.obtenir_emplacements_avec_bouteilles_ou_vides(cave_id, conn=conn)
        dico_bouteilles = dict(sorted(dico_bouteilles_non_triees.items(), key=lambda item: bdd.tri_etagere_cle(item[0])))
        regions = Region.toutes_les_regions(conn)
        if request.method == "POST":
            domaine = request.form.get('domaine')
            nom = request.form.get('nom')
            annee = request.form.get('annee')
            region = request.form.get('region')
            commentaire = request.form.get('commentaire', '')
            if commentaire=='':
                commentaire = "Néant"
            if request.form.get('note_personnelle',"") != "":
                note_personnelle = float(request.form.get('note_personnelle',"").replace(',', '.'))
            if request.form.get('note_personnelle',"") == "":
                note_personnelle = 0.0

            photo = request.form.get('photo_etiquette', "")
            if photo== "":
                photo_etiquette = "Néant"
            else:
                photo_etiquette = photo
            if request.form.get('prix') !="":
                prix = float(request.form.get('prix').replace(',', '.'))
            if request.form.get('prix') == "":
                prix = 0.0
            type = request.form['type']
            cave_id = Cave.obtenir_cave_par_utilisateur_id(utilisateur_id, conn)
            liste_places_html = request.form.getlist("place")
            liste_places = [p.split(",") for p in liste_places_html]
            if domaine and nom and annee and region and type :
                j=1
                try:
                    for empl in liste_places:
                        new_bouteille = Bouteille(domaine, nom, type, annee,region,commentaire,note_personnelle,photo_etiquette,prix, cave_id, conn=conn )
                        bouteille_id = new_bouteille.inserer_bouteille()
                        emplacement_pris = Emplacement.obtenir_un_emplacement(cave_id=cave_id, conn=conn,etagere=empl[0],numero=int(empl[1]))
                        emplacement_pris.setter_bouteille_id(bouteille_id)
                    if len(liste_places) == 1 :
                        flash(f"La bouteille de {new_bouteille.nom} a été ajoutée à votre cave",'success' )
                    else:
                        flash(f"Les {len(liste_places)} bouteilles de {new_bouteille.nom} ont été ajoutées à votre cave", 'success')
                    return redirect(url_for('accueil'))
                except :
                    if len(liste_places)== 1 :
                        flash(f"La bouteille n'a pas pu être créée, veuillez recommencer.", "error")
                    else:
                        flash(f"Les bouteilles n'ont pas pu être créées, veuillez recommencer.", "error")
                    return redirect(url_for('ajouter_bouteille'))
            else:
                if len(liste_places) == 1 :
                    flash(f"La bouteille n'a pas pu être créée, il manque des éléments veuillez recommencer.", "error")
                else:
                    flash(f"Les bouteilles n'ont pas pu être créées, il manque des éléments veuillez recommencer.", "error")
                return redirect(url_for('ajouter_bouteille'))
        return render_template('ajouter.html', utilisateur=utilisateur, photos=photos, regions =regions, dico_bouteilles=dico_bouteilles,  cave =cave)
    else :
        return redirect(url_for('login'))


@app.route('/modifier', methods=['GET', 'POST'])
def modifier_bouteille():
    if "login" in session:
        login = session['login']
        user = Utilisateur.chercher_un_utilisateur(login, conn)
        utilisateur = user.prenom + " " + user.nom
        notre_bouteille_id = session['bouteille_id']
        notre_bouteille =Bouteille.obtenir_caracteristiques_bouteille(notre_bouteille_id, conn)
        photos = Bouteille.recuperer_liste_images_locales()
        print(f"notre bouteille {notre_bouteille.nom}")
        liste_regions = Region.toutes_les_regions(conn)
        if request.method == "POST":
            try:
                domaine = request.form.get('domaine')
                nom = request.form.get('nom')
                print(f"nom vaut {nom}")
                annee = request.form.get('annee')
                region = request.form.get('region')
                commentaire = request.form.get('commentaire', '')
                print(f"commentaire vaut {commentaire}")
                if commentaire == '':
                    commentaire = "Néant"
                if request.form.get('note_personnelle', "") != "":
                    note_personnelle = float(request.form.get('note_personnelle', "").replace(',', '.'))
                if request.form.get('note_personnelle', "") == "":
                    note_personnelle = 0.0
                photo = request.form.get('photo_etiquette', "")
                print(f"photo_etiquette: {photo}")
                if photo == "":
                    photo_etiquette = "Néant"
                else:
                    photo_etiquette = photo
                if request.form.get('prix') != "":
                    prix = float(request.form.get('prix').replace(',', '.'))
                if request.form.get('prix') == "":
                    prix = 0.0
                type_vin = request.form['type_vin']
                notre_bouteille.modifier_bouteille(domaine, nom, type_vin, annee, region, commentaire, note_personnelle, photo_etiquette, prix)
                flash(
                    f"La ou les bouteilles de {notre_bouteille.nom}  année {notre_bouteille.annee} a(ont) été modifiée(s). ",
                    'success')
                return redirect(url_for('accueil'))
            except:
                flash(
                    f"La ou les bouteilles de {notre_bouteille.nom}  année {notre_bouteille.annee}  n'a(ont) pas pu être modifiée(s). ",
                    'error')
        return render_template('modifier.html', utilisateur=utilisateur, liste_regions=liste_regions, notre_bouteille=notre_bouteille, photos=photos)
    else :
        return redirect(url_for('login'))



@app.route('/supprimer', methods=['GET', 'POST'])
def supprimer_bouteille():
    if "login" in session:
        #user = Utilisateur.chercher_un_utilisateur(login, conn)
        #utilisateur = user.prenom + " " + user.nom
        # liste_bouteilles = []
        # dico_bouteilles = {}
        # emplacements=[]
        # emplacement = {}
        # regions = Region.toutes_les_regions(conn)
        utilisateur_id = session['id']
        cave_id = bdd.Cave.obtenir_cave_par_utilisateur_id(utilisateur_id, conn)
        # moyennes = []
        if request.method == "POST":
            bouteille_a_modifier = request.form.get('bouteille_a_modifier')
            bouteille_a_retirer = request.form.get('bouteille_a_retirer')
            bouteille_a_supprimer = request.form.get('bouteille_a_supprimer')
            print(f"bouteille à modifier = {bouteille_a_modifier}")
            if bouteille_a_modifier:
                try:
                    session['bouteille_id']= bouteille_a_modifier
                    return redirect(url_for('modifier_bouteille'))
                except Exception as e:
                    print(f"Erreur : {e}")
                    return redirect(url_for('rechercher'))

            if bouteille_a_retirer:
                try:
                    notre_bouteille = Bouteille.obtenir_caracteristiques_bouteille(bouteille_a_retirer, conn)
                    Emplacement.vider_un_emplacements(bouteille_a_retirer, conn)
                    date_sortie = datetime.now()
                    bouteille_a_noter = Anoter(int(bouteille_a_retirer), cave_id, date_sortie, conn=conn)
                    print(datetime.now().isoformat())
                    print(f"bouteille_a_noter {bouteille_a_noter}")
                    bouteille_a_noter.inserer_dans_liste()
                    flash(
                        f"La bouteille de {notre_bouteille.nom} a été retirée de votre cave. Bonne dégustation ! N'oubliez pas de la noter ensuite.",
                        'success')
                except:
                    flash(
                        f"La bouteille de {notre_bouteille.nom} n'a pas été retirée de votre cave.",
                        'error')

                return redirect(url_for('rechercher'))

            if bouteille_a_supprimer:
                try:
                    notre_bouteille = Bouteille.obtenir_caracteristiques_bouteille(bouteille_a_supprimer, conn)
                    Emplacement.vider_un_emplacements(bouteille_a_retirer, conn)
                    #date_sortie = datetime.now()
                    Bouteille.supprimer_bouteille(notre_bouteille.id, conn)
                    #### ajouter à la liste des bouteilles à noter
                    flash(
                        f"La bouteille de {notre_bouteille.nom} a été supprimée complètement de votre cave.",
                        'success')
                except:
                    flash(
                        f"La bouteille de {notre_bouteille.nom} n'a pas été supprimée de votre cave.",
                        'error')

                return redirect(url_for('rechercher'))
        else:
            return redirect(url_for('login'))


@app.route('/gereretageres', methods=['GET', 'POST'])
def gerer_etageres():
    if "login" in session:
        login = session['login']
        user = Utilisateur.chercher_un_utilisateur(login, conn)
        utilisateur = user.prenom + " " + user.nom
        utilisateur_id = session['id']
        cave_id =int(Cave.obtenir_cave_par_utilisateur_id(utilisateur_id, conn))
        liste_etageres = Etagere.lister_etageres(cave_id, conn)
        liste_etageres_vides = Emplacement.lister_etageres_vides(cave_id, conn)
        total_emplacements =Etagere.nombre_total_emplacements(cave_id, conn)
        liste_bouteilles =[]
        liste_emplacements_pris =[]
        dico_bouteilles = Bouteille.obtenir_avec_emplacement(cave_id, conn=conn)
        dico_etageres = {}
        for etagere in dico_bouteilles.keys():
            for i in range(len(dico_bouteilles[etagere])):
                dico_places = dico_bouteilles[etagere][i]
                bouteille = dico_places['bouteille']
                liste_bouteilles.append(bouteille)
                liste_emplacements_pris.append(
                    {"bouteille_id": bouteille.id, "emplacement": [etagere , str(dico_places['numero'])]})
        liste_emplacements_vides = Emplacement.obtenir(cave_id, conn=conn, vide="vide")
        if request.method == "POST":
            if 'deplacer' in request.form :
                bouteille_id = request.form.get('bouteille_id')
                Emplacement.vider_un_emplacements(bouteille_id, conn=conn)
                emplacement_id = request.form.get('emplacement_id')
                emplacement = Emplacement.obtenir_un_emplacement(cave_id, conn=conn, id=emplacement_id)
                emplacement.setter_bouteille_id(bouteille_id)
                flash(f"La bouteille a été déplacée.", 'success')
            if 'ajouter' in request.form :
                new_nombre_etageres = 0
                try:
                    for i in range(1, 3):
                        nombre_etageres = request.form.get(f'nombre_etageres_{i}')
                        bouteilles_max_par_etagere = request.form.get(f"bouteilles_max_par_etagere_{i}")
                        if nombre_etageres and bouteilles_max_par_etagere:
                            dico_etageres[i] = [nombre_etageres, bouteilles_max_par_etagere]
                            new_nombre_etageres += int(nombre_etageres)
                    Etagere.creer_plusieurs_etageres(int(cave_id), dico_etageres, conn=conn)

                    if new_nombre_etageres == 1 :
                        flash(f"L'étagère a été ajoutée à votre cave.", 'success')
                    else :
                        flash(f"Les {new_nombre_etageres} ont été ajoutées à votre cave.", 'success')
                    return redirect(url_for('accueil'))
                except:
                    flash(f"Aucune étagère n'a été éjoutée.", 'error')
            if "supprimer" in request.form :
                try:
                    etagere = request.form.get('etagere')
                    Emplacement.supprimer_emplacements(cave_id, etagere, conn=conn)
                    flash(f"L'étagère {etagere} a été supprimée.", 'success')
                    return redirect(url_for('accueil'))
                except:
                    flash(f"L'étagère {etagere} n'a pas pu être supprimée.", 'error')
            return redirect(url_for('accueil'))
        return render_template('gereretageres.html', utilisateur=utilisateur, total_emplacements=total_emplacements, liste_etageres=liste_etageres, liste_etageres_vides=liste_etageres_vides, liste_bouteilles=liste_bouteilles, liste_emplacements_pris=liste_emplacements_pris, liste_emplacements_vides=liste_emplacements_vides)
    else:
        return redirect(url_for('login'))


@app.errorhandler(404)
def page_not_found(e):
    login = session['login']
    user = Utilisateur.chercher_un_utilisateur(login, conn)
    utilisateur = user.prenom + " " + user.nom
    return render_template('404.html', utilisateur=utilisateur), 404


@app.route('/rechercher', methods=['GET', 'POST'])
def rechercher():
    if "login" in session:
        login = session['login']
        user = Utilisateur.chercher_un_utilisateur(login, conn)
        utilisateur = user.prenom + " " + user.nom
        dico_bouteilles = {}
        regions = Region.toutes_les_regions(conn)
        utilisateur_id = session['id']
        cave_id = bdd.Cave.obtenir_cave_par_utilisateur_id(utilisateur_id, conn)
        moyennes = []
        emplacement=""
        emplacements = []
        liste_bouteilles = []
        if request.method == "POST":
            if request.form.get('nom'):
                nom = (request.form.get('nom').upper())+"%"
            else:
                nom = ""
            #print(f"nom vaut {nom}")
            if request.form.get('domaine') :
               domaine= (request.form.get('domaine').upper())+"%"
            else:
               domaine =""
            region = request.form.get('region','')
            annee = request.form.get('annee', '')
            type_vin = request.form.get('type_vin','').lower()
            prix_min = bdd.to_float(request.form.get('prix_min'))
            prix_max = bdd.to_float(request.form.get('prix_max'))
            note_min = bdd.to_float(request.form.get('note_min'))
            note_max = bdd.to_float(request.form.get('note_max'))
            emplacement= request.form.get('emplacement', '')
            if 'emplacement' in request.form :
                emplacement = "non"
                emplacements = {}
                dico_bouteilles = Bouteille.obtenir_presentes_sans_emplacement(cave_id, conn=conn, domaine=domaine, nom=nom,
                                                                     region=region, type_vin=type_vin, annee=annee,
                                                                     prix_min=prix_min, prix_max=prix_max,
                                                                     note_min=note_min, note_max=note_max)
                for etagere in dico_bouteilles.keys():
                    for i in range(len(dico_bouteilles[etagere])):
                        dico_places = dico_bouteilles[etagere][i]
                        bouteille = dico_places['bouteille']
                        moyenne = bouteille.obtenir_moyenne_de_notes_perso_bouteilles_identiques()
                        moyennes.append({bouteille.id: moyenne})
            else :
                dico_bouteilles = Bouteille.obtenir_avec_emplacement(cave_id, conn=conn, domaine=domaine, nom=nom, region=region, type_vin=type_vin, annee=annee, prix_min=prix_min, prix_max=prix_max, note_min=note_min, note_max=note_max)
                for etagere in dico_bouteilles.keys():
                    for i in range (len(dico_bouteilles[etagere])) :
                        dico_places = dico_bouteilles[etagere][i]
                        bouteille = dico_places['bouteille']
                        liste_bouteilles.append(bouteille)
                        moyenne = bouteille.obtenir_moyenne_de_notes_perso_bouteilles_identiques()
                        emplacements.append({"bouteille_id":bouteille.id, "emplacement":(etagere+str(dico_places['numero']))})
                        moyennes.append({bouteille.id: moyenne})
                dico_bouteilles ={}
                #return render_template('rechercher.html', utilisateur=utilisateur, liste_bouteilles=liste_bouteilles,dico_bouteilles=dico_bouteilles, emplacements=emplacements, regions=regions, moyennes=moyennes, emplacement=emplacement)

        return render_template('rechercher.html', utilisateur=utilisateur, liste_bouteilles=liste_bouteilles,dico_bouteilles=dico_bouteilles,emplacements=emplacements, regions=regions, moyennes=moyennes, emplacement=emplacement)
    else:
        return redirect(url_for('login'))


@app.route('/visualiserarchives', methods=['GET', 'POST'])
def visualiser_les_archives():
    if "login" in session:
        login = session['login']
        user = Utilisateur.chercher_un_utilisateur(login, conn)
        utilisateur = user.prenom + " " + user.nom
        dico_bouteilles = {}
        regions = Region.toutes_les_regions(conn)
        utilisateur_id = session['id']
        cave_id = bdd.Cave.obtenir_cave_par_utilisateur_id(utilisateur_id, conn)
        moyennes = []
        if request.method == "POST":
            nom = request.form.get('nom', '').lower()
            domaine = request.form.get('domaine','').lower()
            region = request.form.get('region','')
            annee = request.form.get('annee', '')
            type_vin = request.form.get('type_vin','').lower()
            prix_min = bdd.to_float(request.form.get('prix_min'))
            prix_max = bdd.to_float(request.form.get('prix_max'))
            note_min = bdd.to_float(request.form.get('note_min'))
            note_max = bdd.to_float(request.form.get('note_max'))
            dico_bouteilles = Bouteille.obtenir_sans_emplacement(cave_id, conn=conn, domaine=domaine, nom=nom, region=region, type_vin=type_vin, annee=annee, prix_min=prix_min, prix_max=prix_max, note_min=note_min, note_max=note_max)
            for etagere in dico_bouteilles.keys():
                for i in range (len(dico_bouteilles[etagere])) :
                    dico_places = dico_bouteilles[etagere][i]
                    bouteille = dico_places['bouteille']
                    moyenne = bouteille.obtenir_moyenne_de_notes_perso_bouteilles_identiques()
                    moyennes.append({bouteille.id: moyenne})
            #return render_template('visualiserarchives.html', utilisateur=utilisateur, dico_bouteilles=dico_bouteilles, regions=regions, moyennes=moyennes)
        return render_template('visualiserarchives.html', utilisateur=utilisateur, dico_bouteilles=dico_bouteilles, regions=regions, moyennes=moyennes)
    else:
        return redirect(url_for('login'))



if __name__ == "__main__":
    app.run(debug=True)
