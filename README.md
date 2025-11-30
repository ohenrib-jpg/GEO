!!!!!!!!!!V.0.6PP/Avant-der branche avant version de test totale!!!!!!!!!!!

# 🌍 GEOPOL - Analyseur Géopolitique Intelligent
Contact : ohenri.b@gmail.com / olivier.bellanza@ac-toulouse.fr
(Un grand merci a DeepSeek et a Claude pour leur aide capitale).
**Système d'analyse avancée des flux médiatiques/sociaux, d'indicateurs géopolitiques avec IA pour la veille géopolitique**.
**Tableau de bord ETR pour la veille stratégique**.
Analyse en temps réel des tendances géopolitiques avec IA intégrées (RoBERTa + Llama 3.2).
Intégration de SpaCy pour NER (Named Entity Recognition)

Seul outil pédagogique géopolitique open-source en français
- Concurrents : GDELT (anglais, complexe), MediaCloud (archivé)

- Approche Multi-Échelles:
Du local (cartographie narrative) au global (rapports synthétiques)
Correspond aux programmes scolaires (géopolitique en Term ES/L/S/sup.)




## 🚀 Fonctionnalités Principales

### 🔍 Analyse Sémantique Avancée
- **RoBERTa** pour l'analyse fine des sentiments et émotions
- **Llama 3.2** pour la génération de rapports intelligents
- MAJ 27/11 ==> Le modele IA est egalement integre comme "assistant geopolitique" dans l'interface via fenetre flottante
- Classification automatique par thèmes géopolitiques configurables (utiliser llama.cpp avec modele gguf)
- **Spacy** pour le NER (recherche et construction des réseaux d'influences=> pays, villes, organisations, personnalités
   ((entities = nlp(article_text).ents))
  
### 📊 Tableaux de Bord Interactifs
- Visualisation en temps réel des tendances
- Statistiques détaillées par thème et sentiment
- Évolution temporelle sur 30 jours
- Indicateurs macroéconomiques (français pour la version V.06pp, source Eurostat et scrap leger INSEE)   **"mode scolaire"**
- Veille Economique en temps reel, et comparaison avec les pays de la zone Euros (utilise sources Eurostats, yFinance) **"Mode etendu Recherche"**
**MAJ3011=> Integration en cours Surveillance des indicateurs clés (VIX (indice de peur des marchés),Pétrole Brent (baromètre géopolitique),Or (valeur refuge),taux des bonds (sentiment risque),Devises refuges (A definir)), Corrélations géopolitiques (detec. de patterns exemple :"tensions_russes": ["RTSI", "Gazprom", "Rosneft"],"crise_moyen_orient": ["pétrole", "or", "VIX"])**



  
### 🌐 Agrégation Multi-Sources
- Flux RSS traditionnels
- Réseaux sociaux (Twitter via Nitter, Reddit)
- Archives historiques (Archive.org depuis 1945)

### 🤖 Intelligence Artificielle
- Détection d'anomalies et tendances émergentes
- Corroboration automatique entre sources (automatisée dans la V.0.6)
- Analyse bayésienne pour la confiance (automatisée dans la V.0.6)
- Génération de rapports d'analyses en PDF automatisés
- Affinage des résultats automatiques (-> Deeplearning) 

## ⚙️ Installation

### Prérequis
- Python 3.8+
- llama.cpp
- 6GB RAM minimum (8GB pour IA rec. MINIMUM ====>Mistral 3.2 3b (Q4) 3/4 Go, RoBERTa 1/1,5 Go, Spacy 1/2 Go, serveur logiciel 2/2,5 Go)
- 7GB espace disque (sans compter le modèle gguf et les donnees de vos traitements. Compter 15 Go d'espace disque pour un mois d'analyses sur 200/300 sources)

### Installation rapide
```bash
git clone https://github.com/ohenrib-jpg/GEO/blob/GEOPOL-V.0.6-preprod.git
cd GEO
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
python run.py 
# ou
GEOPOL.bat
# ou
GEOPOLCMD.bat =>mode debug

**NE PAS OUBLIER D'INSTALLER LLAMA.CPP, ET DE METTRE UN MODÈLE GGUF DANS LE DOSSIER \MODELS**

POUR INSTALLER LLAMA.CPP :
Indispensable :
- CMake >= 3.14
- C++17 compiler (GCC, Clang, MSVC)
- C11 compiler

Puis, depuis le prompt de votre environnement virtuel : pip install llama.cpp




**VOUS POUVEZ OBTENIR UN MODÈLE GGUF EN CRÉANT UN COMPTE GRATUIT SUR HUGGINGFACE.COM**
CHOISISSEZ UN MODÈLE JUSTEMENT QUANTIFIE POUR LA PUISSANCE DE VOTRE ORDINATEUR

**CE LOGICIEL EST TOTALEMENT (et le restera toujours) GRATUIT POUR L'ENSEIGNEMENT (Ed. Nat.) ET LA RECHERCHE. PAS POUR LA spéculation OU L'UTILISATION COMMERCIALE, EN DEHORS DES TERMES D'ACCORDS AVEC LE CONCEPTEUR**





==================================================
## 🎯 **Prochaines améliorations :**

## 🗺️ Roadmap

- [X] Intégration des fonctions eco/macroeco
- [X] Intégration du detecteur de signaux faibles
MAJ 22/11/2025 => Modification de la roadmap : integration des API ONU, BRICS,...pour les analyses internationales
- [X] cartographie leaflet.js **MAJ3011=>integree, html fait, mais pas les routes....A suivre**
- [ ] Integration de l'IA legere (la derniere, promis) en arriere plan pour le 'fine tuning' metier (LORA)
- [ ] Support multilingue étendu
- [ ] API REST complète
- [ ] Applications mobiles
- [ ] Analyses prédictives
- [ ] Plugin Zotero pour export bibliographique

- [ ] Equilibrage /Mise en conformité aux normes de recherche  

## 🌈 **Impacts potentiels :**
Scolaires :
- **Term. HGGSP
- **Term. Eco et soc.

Formations/Chercheurs :
- **Journalistes** et médias
- **Analystes géopolitiques** 
- **Chercheurs** en sciences politiques
- **Entreprises** avec exposition internationale
