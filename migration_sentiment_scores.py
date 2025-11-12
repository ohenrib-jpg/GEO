# migration_sentiment_scores.py
def migrate_existing_articles(db_manager, sentiment_analyzer):
    """Migre les articles existants pour ajouter les scores de sentiment"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Récupérer les articles sans score
        cursor.execute("""
            SELECT id, title, content, sentiment_type 
            FROM articles 
            WHERE sentiment_score IS NULL 
            AND sentiment_type IS NOT NULL
            LIMIT 1000  # Limiter pour éviter la surcharge
        """)
        
        articles = cursor.fetchall()
        migrated_count = 0
        
        for article_id, title, content, current_sentiment in articles:
            try:
                # Ré-analyser le sentiment avec scores
                text = f"{title} {content}" if content else title
                sentiment_result = sentiment_analyzer.analyze_sentiment_with_score(text)
                detailed_category, confidence = sentiment_analyzer.get_detailed_sentiment_category(
                    sentiment_result['scores']
                )
                
                # Mettre à jour l'article
                cursor.execute("""
                    UPDATE articles 
                    SET sentiment_score = ?, detailed_sentiment = ?, confidence = ?
                    WHERE id = ?
                """, (sentiment_result['score'], detailed_category, confidence, article_id))
                
                migrated_count += 1
                print(f"✅ Article {article_id} migré: {current_sentiment} -> {detailed_category}")
                
            except Exception as e:
                print(f"❌ Erreur migration article {article_id}: {e}")
                continue
        
        conn.commit()
        print(f"🎉 Migration terminée: {migrated_count} articles migrés")
        
    except Exception as e:
        print(f"❌ Erreur générale migration: {e}")
        conn.rollback()
    finally:
        conn.close()