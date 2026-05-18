import pytest
import psycopg2

@pytest.fixture(scope="session")
def test_db():
    conn = psycopg2.connect("postgresql://localhost/mailroom_test")  
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS person (
            id SERIAL, name TEXT, building TEXT, room TEXT, department TEXT, school TEXT
        )
    """)
    
    cur.execute("INSERT INTO person (name, building, room, department, school) VALUES ('Seth Alison', 'Ent Center', '204B', 'Theatreworks', 'UCCS')")
    conn.commit()
    yield conn
    
    # Teardown — wipe it clean after tests
    cur.execute("DROP TABLE person")
    conn.commit()
    conn.close()