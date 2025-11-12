#!/usr/bin/env python3
"""
Script pour identifier les jsonify() problématiques dans routes.py
"""

import re
import os

def analyze_routes_file():
    """Analyse routes.py pour trouver les problèmes"""
    
    routes_path = 'Flask/routes.py'
    
    if not os.path.exists(routes_path):
        print(f"❌ Fichier introuvable: {routes_path}")
        return
    
    print("🔍 Analyse de routes.py...\n")
    
    with open(routes_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Variables de suivi
    in_function = False
    current_function = None
    function_indent = 0
    problems = []
    
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        
        # Détecter les définitions de fonctions
        if stripped.startswith('def '):
            in_function = True
            function_indent = indent
            current_function = stripped.split('(')[0].replace('def ', '')
        
        # Sortir de la fonction si l'indentation diminue
        elif in_function and stripped and indent <= function_indent:
            in_function = False
            current_function = None
        
        # Détecter jsonify()
        if 'jsonify(' in line or 'return jsonify' in line:
            if not in_function:
                problems.append({
                    'line': i,
                    'content': line.strip(),
                    'context': 'EN DEHORS DE TOUTE FONCTION'
                })
            else:
                # Vérifier si c'est dans une route (avec @app.route)
                is_route = False
                for j in range(max(0, i-5), i):
                    if '@app.route' in lines[j]:
                        is_route = True
                        break
                
                if not is_route:
                    problems.append({
                        'line': i,
                        'content': line.strip(),
                        'context': f'Dans fonction {current_function} (pas une route)'
                    })
    
    # Afficher les résultats
    if problems:
        print(f"❌ {len(problems)} problème(s) trouvé(s):\n")
        for p in problems:
            print(f"Ligne {p['line']}: {p['context']}")
            print(f"  Code: {p['content']}")
            print()
    else:
        print("✅ Aucun problème détecté avec jsonify()")
    
    # Vérifier la ligne 280 spécifiquement
    print(f"\n🔍 Inspection de la ligne 280:")
    if len(lines) >= 280:
        print(f"  {lines[279].strip()}")
        
        # Context (lignes autour)
        print("\n📝 Contexte (lignes 275-285):")
        for i in range(max(0, 274), min(len(lines), 285)):
            marker = ">>> " if i == 279 else "    "
            print(f"{marker}{i+1}: {lines[i].rstrip()}")
    else:
        print(f"  ⚠️ Le fichier a seulement {len(lines)} lignes")

if __name__ == "__main__":
    analyze_routes_file()
