# 🌍 GEOPOL Analytics - Plateforme d'Analyse Géopolitique IA
Contact : ohenri.b@gmail.com

GEOPOL représente la convergence entre l'intelligence artificielle et l'analyse géopolitique, offrant aux décideurs une compréhension profonde des dynamiques mondiales à travers l'analyse automatisée des flux d'informations.

Merci a Claude et a DeepSeek ;-)

Analyse en temps réel des tendances géopolitiques avec double IA (RoBERTa + Llama 3.2)
Architecture modulaire Flask + analyse sémantique avancée
Système de corroboration et analyse bayésienne
Agrégation multi-sources (RSS + réseaux sociaux + archives historiques)


## 🚀 Fonctionnalités
- 📊 Analyse de sentiment en temps réel => Comparaison médias traditionnels vs réseaux sociaux
- 🤖 Double IA: RoBERTa (sentiment) + Llama (contexte) ==>MAJ 12/11: RoBERTa est pleinement integrees ==>veillez a na pas lui donner 150 flux a analyser par passe, a moins d'avoir un GROS serveur
- 📈 Détection d'anomalies et tendances émergentes
- 🕰️ Analyse historique comparative depuis 1945 via Archive.org (MAJ 10/11=>les bugs ont etes releves et sont en cours de corrections/ Ils n'affectent en rien le reste du log.)
- 📄 Génération automatique de rapports PDF
- 🤖 MAJ 12/11 ==> Debut d'integration de l'ecran des indicateurs faibles (conseils aux voyageurs + donnees macroeco + comptage et moyenne des emissions radios SDR) -
  Le parsser de flux rss traite a present les paquets par 3 (avec compteur) pour laisser le temps a RoBERTa de ponderer le score - L'analyse TextBlob reste operationnelle pour les flux non-emotionnels - Les articles affichent a present les images

## 🛠️ Installation
```bash
pip install -r requirements.txt
llama.cpp + modele gguf
CMD => python run.py ou => start_windows.bat depuis la racine du dossier d'installation 


## 🎯 **Prochaines améliorations possibles :**

### **Court terme :**
- [ ] Dashboard en temps réel
- [ ] Alertes par email
- [ ] Plus de sources de données

### **Moyen terme :**
- [ ] Application mobile
- [ ] Analyse d'images
- [ ] Prédictions de tendances

### **Long terme :**
- [ ] API publique
- [ ] Plugins communautaires
- [ ] Analyse multi-langues

## 🌈 **Impact potentiel :**
- **Journalistes** et médias
- **Analystes géopolitiques** 
- **Chercheurs** en sciences politiques
- **Entreprises** avec exposition internationale
