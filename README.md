# 🌍 GEOPOL - Analyseur Géopolitique Intelligent
Contact : ohenri.b@gmail.com

CECI EST UNE REFONTE COMPLETE DU PROJETRSS-AGGREGATOR 
(Un grand merci a DeepSeek et a Claude pour leur aide capitale)

Analyse en temps réel des tendances géopolitiques avec double IA (RoBERTa + Mistral 2.7b)

**Système d'analyse avancée des flux RSS/Reseaux sociaux avec IA pour la veille géopolitique**

## 🚀 Fonctionnalités Principales

### 🔍 Analyse Sémantique Avancée
- **RoBERTa** pour l'analyse fine des sentiments et émotions
- **Mistral 2.7b** pour la génération de rapports intelligents
- Classification automatique par thèmes géopolitiques (utiliser llama.cpp avec modele gguf)

### 📊 Tableaux de Bord Interactifs
- Visualisation en temps réel des tendances
- Statistiques détaillées par thème et sentiment
- Évolution temporelle sur 30 jours

### 🌐 Agrégation Multi-Sources
- Flux RSS traditionnels
- Réseaux sociaux (Twitter via Nitter, Reddit)  ==========>MAJ 14/11:OK
- Archives historiques (Archive.org depuis 1945) ===> en dev.

### 🤖 Intelligence Artificielle
- Détection d'anomalies et tendances émergentes ========>MAJ 14/11 :OK
- Corroboration automatique entre sources
- Analyse bayésienne pour la confiance ===========>MAJ 15/11 : Analyse bayesienne par paquets automatiques pour renforcer les resultats de RoBERTa 
- Génération de rapports PDF automatisés =======>MAJ 15/11 : "tokenisation" des reponses plus basse (1500) pour les petites config. (evite le mode degrade)

## ⚙️ Installation

### Prérequis
- Python 3.8+ (!attention aux compatibilites de Python 3.12!)
- llama.cpp
- 6GB RAM minimum (8GB pour IA rec.)=========> 8GO+GPU ou CPU+16GO
- 2GB espace disque (sans compter le modele gguf) /5GB espace disque (avec Mistral+RoBERTa)

### Installation rapide
```bash
git clone https://github.com/ohenrib-jpg/GEO.git
cd GEO
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
python run.py 
# ou
start_windows.bat

NE PAS OUBLIER D'INSTALLER LLAMA.CPP, ET DE METTRE UN MODELE GGUF DANS LE DOSSIER \MODELS 





==================================================
## 🎯 **Prochaines améliorations :**

## 🗺️ Roadmap

- [ ] Intégration des fonctions eco/macroeco ===========> en dev.
- [ ] Intégration du detecteur de signaux faibles ==================> en dev.
- [ ] Support multilingue étendu
- [ ] API REST complète
- [ ] Applications mobiles
- [ ] Analyses prédictives

## 🌈 **Impact potentiel :**
- **Journalistes** et médias
- **Analystes géopolitiques** 
- **Chercheurs** en sciences politiques
- **Entreprises** avec exposition internationale
