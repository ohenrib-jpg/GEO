# 📦 Guide d'Installation - Analyseur RSS avec Analyse Avancée

## Prérequis

- **Python 3.8 ou supérieur** (vérifier avec `python --version`)
- **pip** (gestionnaire de paquets Python)
- **Git** (optionnel, pour cloner le projet)
- **10 GB d'espace disque libre** (recommandé)
- **4 GB de RAM minimum** (8 GB recommandé)

---

## 🚀 Installation Rapide (10 minutes)

### Étape 1 : Télécharger le projet

Si vous avez Git :
```bash
git clone https://github.com/votre-repo/geo-analyzer.git
cd geo-analyzer
```

Sinon, téléchargez et décompressez le ZIP.

### Étape 2 : Créer un environnement virtuel

**Windows** :
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux** :
```bash
python3 -m venv venv
source venv/bin/activate
```

Vous devriez voir `(venv)` dans votre terminal.

### Étape 3 : Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

⏱️ **Temps estimé** : 3-5 minutes

### Étape 4 : Télécharger les données NLTK

```bash
python -c "import nltk; nltk.download('vader_lexicon')"
python -c "import nltk; nltk.download('punkt')"
```

### Étape 5 : Lancer l'application

```bash
python run.py
```

✅ **Succès !** Ouvrez votre navigateur à `http://localhost:5000`

---

## 🔧 Installation Personnalisée

### Option A : Installation minimale (sans ML lourd)

**Avantages** :
- Rapide (~5 minutes)
- Léger (~200 MB)
- Fonctionne sur machines peu puissantes

**Inconvénients** :
- Corroboration moins précise (utilise TF-IDF au lieu de transformers)

```bash
pip install Flask feedparser textblob nltk rapidfuzz scikit-learn
```

### Option B : Installation complète (avec ML avancé)

**Avantages** :
- Meilleure précision (~15% d'amélioration)
- Analyse sémantique profonde

**Inconvénients** :
- Plus long (~15 minutes)
- Plus lourd (~1.5 GB)
- Nécessite 8 GB RAM

```bash
pip install -r requirements.txt
pip install sentence-transformers
```

---

## 📊 Vérification de l'installation

### Test 1 : Serveur démarre

```bash
python run.py
```

**Attendu** :
```
🚀 Démarrage de l'Analyseur RSS Intelligent
==================================================
✅ Flask
✅ feedparser
✅ TextBlob
✅ NLTK
🌐 Application disponible sur: http://localhost:5000
```

### Test 2 : Base de données initialisée

Vérifiez que `rss_analyzer.db` existe dans le dossier principal.

```bash
ls -lh rss_analyzer.db  # macOS/Linux
dir rss_analyzer.db     # Windows
```

**Attendu** : Fichier de ~100 KB

### Test 3 : Migrations appliquées

Ouvrez `http://localhost:5000` dans votre navigateur.

Dans les logs (terminal), vous devriez voir :
```
🔄 Démarrage des migrations...
▶️  Exécution migration: 01_add_bayesian_columns
✅ Migration 01_add_bayesian_columns terminée
▶️  Exécution migration: 02_create_corroboration_table
✅ Migration 02_create_corroboration_table terminée
✅ Toutes les migrations terminées
```

### Test 4 : Interface fonctionnelle

Dans votre navigateur :

1. ✅ La page d'accueil s'affiche
2. ✅ Le menu latéral contient "Analyse avancée"
3. ✅ Cliquer sur "Tableau de bord" affiche les graphiques

---

## 🐛 Résolution de problèmes courants

### Erreur : "ModuleNotFoundError: No module named 'Flask'"

**Cause** : L'environnement virtuel n'est pas activé

**Solution** :
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Erreur : "sqlite3.OperationalError: no such table"

**Cause** : Base de données non initialisée

**Solution** :
```bash
# Supprimer l'ancienne base
rm rss_analyzer.db  # macOS/Linux
del rss_analyzer.db  # Windows

# Relancer l'application
python run.py
```

### Erreur : "Address already in use" (port 5000)

**Cause** : Un autre processus utilise le port 5000

**Solution 1** : Trouver et tuer le processus
```bash
# macOS/Linux
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Solution 2** : Changer le port
Dans `run.py`, ligne 63 :
```python
port = find_free_port(8000)  # Au lieu de 5000
```

### Erreur : "Memory Error" lors de l'installation

**Cause** : RAM insuffisante pour sentence-transformers

**Solution** : Utilisez l'installation minimale (Option A)

### Erreur : Analyses très lentes

**Causes possibles** :
1. Trop d'articles en base (> 10,000)
2. Machine peu puissante
3. sentence-transformers installé sur machine faible

**Solutions** :
```python
# Dans corroboration_engine.py, ligne 295
# Réduire le nombre de candidats
cursor.execute("""...""", 50)  # Au lieu de 200
```

---

## 🔒 Configuration de sécurité (production)

### 1. Générer une clé secrète

```python
# Dans Flask/config.py
SECRET_KEY = 'votre-clé-super-secrète-ici'
```

### 2. Désactiver le mode debug

```python
# Dans app.py
app.run(debug=False, host='0.0.0.0', port=5000)
```

### 3. Utiliser un serveur WSGI (production)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📁 Structure des fichiers après installation

```
GEO/
├── venv/                      # Environnement virtuel
├── rss_analyzer.db            # Base de données SQLite
├── app.py                     # Point d'entrée
├── run.py                     # Script de démarrage
├── requirements.txt           # Dépendances
├── templates/                 # Pages HTML
│   ├── base.html
│   ├── index.html
│   └── dashboard.html
├── static/
│   └── js/
│       ├── app.js
│       ├── advanced-analysis.js  # ← NOUVEAU
│       └── ...
└── Flask/
    ├── database.py
    ├── bayesian_analyzer.py      # ← NOUVEAU
    ├── corroboration_engine.py   # ← NOUVEAU
    ├── database_migrations.py    # ← NOUVEAU
    ├── routes_advanced.py        # ← NOUVEAU
    └── ...
```

---

## 📚 Dépendances expliquées

| Package | Taille | Rôle | Optionnel ? |
|---------|--------|------|-------------|
| **Flask** | ~2 MB | Serveur web | ❌ Obligatoire |
| **feedparser** | ~1 MB | Parse les flux RSS | ❌ Obligatoire |
| **textblob** | ~5 MB | Analyse de sentiment basique | ❌ Obligatoire |
| **nltk** | ~20 MB | VADER sentiment | ❌ Obligatoire |
| **rapidfuzz** | ~3 MB | Similarité textuelle rapide | ✅ Optionnel |
| **scikit-learn** | ~40 MB | TF-IDF pour corroboration | ✅ Optionnel |
| **sentence-transformers** | ~500 MB | Embeddings sémantiques | ✅ Optionnel (recommandé) |

---

## 🎓 Premiers pas après installation

### 1. Créer vos premiers thèmes

1. Allez sur la page d'accueil
2. Cliquez sur "Gérer les thèmes"
3. Créez 2-3 thèmes (ex: "Économie", "Technologie")

### 2. Importer des flux RSS

1. Page d'accueil → Section "Analyse des Flux RSS"
2. Collez ces URLs (une par ligne) :
```
https://feeds.bbci.co.uk/news/rss.xml
https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml
https://feeds.lemonde.fr/c/205/f/3050/index.rss
```
3. Cliquez sur "Lancer l'analyse"
4. Attendez ~2 minutes pour 50 articles

### 3. Lancer votre première analyse avancée

1. Menu latéral → "Analyse avancée"
2. Cliquez sur "Corroboration batch"
3. Attendez ~30 secondes
4. Cliquez sur "Analyse bayésienne batch"
5. Consultez le tableau de bord pour voir les résultats !

---

## 🔄 Mise à jour

Pour mettre à jour vers une nouvelle version :

```bash
# Activer l'environnement
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Récupérer les dernières modifications
git pull

# Mettre à jour les dépendances
pip install --upgrade -r requirements.txt

# Relancer l'application
python run.py
```

Les migrations de base de données s'exécutent automatiquement au démarrage.

---

## 🆘 Besoin d'aide ?

### Consultez les logs

Les logs sont affichés dans le terminal. En cas d'erreur, copiez le message complet.

### Vérifiez votre configuration

```bash
python -c "import sys; print(sys.version)"
pip list
```

### Réinitialisez tout

En dernier recours :

```bash
# Désactiver l'environnement
deactivate

# Supprimer tout
rm -rf venv rss_analyzer.db  # macOS/Linux
rmdir /s venv && del rss_analyzer.db  # Windows

# Recommencer l'installation depuis l'étape 2
```

---

## ✅ Check-list d'installation réussie

- [ ] Python 3.8+ installé
- [ ] Environnement virtuel créé et activé
- [ ] Toutes les dépendances installées
- [ ] NLTK data téléchargée
- [ ] Application démarre sans erreur
- [ ] Base de données créée (rss_analyzer.db)
- [ ] Interface accessible à http://localhost:5000
- [ ] Menu "Analyse avancée" visible
- [ ] Première analyse de flux réussie

**Félicitations !** Votre analyseur RSS est opérationnel. 🎉

Consultez maintenant le [GUIDE_ANALYSE_AVANCEE.md](GUIDE_ANALYSE_AVANCEE.md) pour apprendre à utiliser les fonctionnalités avancées.
