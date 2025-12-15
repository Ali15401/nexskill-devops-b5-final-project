from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import psycopg2
import hashlib
import requests
from config import Config

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = psycopg2.connect(
        host=Config.DATABASE_HOST,
        port=Config.DATABASE_PORT,
        database=Config.DATABASE_NAME,
        user=Config.DATABASE_USER,
        password=Config.DATABASE_PASSWORD
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id SERIAL PRIMARY KEY,
            original_url TEXT NOT NULL,
            short_code VARCHAR(10) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def generate_short_code(url):
    return hashlib.md5(url.encode()).hexdigest()[:6]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    data = request.json
    original_url = data.get('url')
    
    if not original_url:
        return jsonify({'error': 'URL is required'}), 400
    
    short_code = generate_short_code(original_url)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT short_code FROM links WHERE original_url = %s', (original_url,))
        existing = cur.fetchone()
        
        if existing:
            short_code = existing[0]
        else:
            cur.execute(
                'INSERT INTO links (original_url, short_code) VALUES (%s, %s)',
                (original_url, short_code)
            )
            conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({'short_code': short_code, 'short_url': f'/{short_code}'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT original_url FROM links WHERE short_code = %s', (short_code,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            original_url = result[0]
            
            try:
                requests.post(
                    f'{Config.ANALYTICS_SERVICE_URL}/api/track',
                    json={'short_code': short_code},
                    timeout=2
                )
            except:
                pass
            
            return redirect(original_url)
        else:
            return jsonify({'error': 'URL not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/links', methods=['GET'])
def get_all_links():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT original_url, short_code, created_at FROM links ORDER BY created_at DESC')
        links = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([{
            'original_url': link[0],
            'short_code': link[1],
            'created_at': link[2].isoformat()
        } for link in links]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=Config.PORT, debug=True)