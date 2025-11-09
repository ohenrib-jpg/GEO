from Flask.llama_client import get_llama_client

client = get_llama_client()

# Articles de test avec contenu substantiel
articles = [
    {
        'title': 'Escalade des tensions en Méditerranée orientale',
        'content': 'Les relations diplomatiques entre la Turquie et la Grèce se détériorent suite à un incident maritime dans les eaux disputées. Les deux pays mobilisent leurs forces navales.',
        'sentiment': 'negative',
        'source': 'Le Monde'
    },
    {
        'title': 'Accord commercial historique UE-Chine',
        'content': 'Un accord commercial majeur a été signé entre l\'Union européenne et la Chine, portant sur les technologies vertes et les échanges énergétiques pour les 10 prochaines années.',
        'sentiment': 'positive',
        'source': 'Les Échos'
    },
    {
        'title': 'Sommet de l\'OTAN: renforcement de la défense européenne',
        'content': 'Les membres de l\'OTAN s\'accordent pour augmenter leurs budgets de défense de 2% du PIB et renforcer la présence militaire en Europe de l\'Est face aux menaces persistantes.',
        'sentiment': 'neutral',
        'source': 'Reuters'
    }
]

context = {
    'period': '2025-11-01 → 2025-11-08',
    'themes': ['géopolitique', 'défense'],
    'sentiment_positive': 1,
    'sentiment_negative': 1,
    'sentiment_neutral': 1,
    'total_articles': 3
}

print("🧪 Test génération rapport avec nouveau prompt\n")
print("=" * 70)

result = client.generate_analysis('geopolitique', articles, context)

if result['success']:
    print("✅ SUCCÈS\n")
    print(result['analysis'])
else:
    print(f"❌ ÉCHEC: {result.get('error')}\n")
    print(result.get('analysis', 'Pas d\'analyse')[:500])