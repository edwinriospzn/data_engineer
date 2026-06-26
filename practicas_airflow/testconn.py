"""
Test connection to Pagila database
Run this script to verify the connection to your postgres-dev container
"""
import psycopg2

def test_connection():
    """Test connection to pagila database"""
    try:
        # Use localhost when running locally (not inside Docker)
        conn = psycopg2.connect(
            host='localhost',  # Changed from host.docker.internal
            port=5432,
            user='admin',
            password='admin123',
            database='pagila'
        )
        cur = conn.cursor()
        
        # Test queries
        cur.execute('SELECT COUNT(*) FROM actor;')
        actor_count = cur.fetchone()[0]
        print(f'✅ Connection successful! Total actors in pagila DB: {actor_count}')
        
        cur.execute('SELECT COUNT(*) FROM film;')
        film_count = cur.fetchone()[0]
        print(f'✅ Total films in pagila DB: {film_count}')
        
        # Get some sample data
        cur.execute('''
            SELECT first_name, last_name 
            FROM actor 
            LIMIT 5;
        ''')
        actors = cur.fetchall()
        print('\n📋 Sample actors:')
        for first_name, last_name in actors:
            print(f'  - {first_name} {last_name}')
        
        conn.close()
        print('\n✅ All tests passed! Connection is working correctly.')
        return True
        
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return False

if __name__ == "__main__":
    test_connection()