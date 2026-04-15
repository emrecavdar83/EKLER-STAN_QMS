from sqlalchemy import text
from database.connection import get_engine

def cleanup_dead_tables():
    """Artık kullanılmayan Flow Engine tablolarını siler."""
    print("Connecting to Database...")
    try:
        engine = get_engine()
        print("Connection Established.")
        
        dead_tables = [
            "flow_definitions", 
            "flow_nodes", 
            "flow_edges", 
            "flow_bypass_logs", 
            "personnel_tasks",
            "sistem_modulleri"
        ]
        
        with engine.begin() as conn:
            for table in dead_tables:
                print(f"Attempting to delete: {table}...")
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    print(f"Deleted: {table}")
                except Exception as e:
                    print(f"Error deleting {table}: {e}")
        print("Cleanup Finished.")
    except Exception as general_e:
        print(f"Critical Connection Error: {general_e}")

if __name__ == "__main__":
    cleanup_dead_tables()
