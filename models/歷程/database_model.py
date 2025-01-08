from models.user_records_db import UserRecordsDB
from models.dev_ops_db import DevOpsDB

def main():
    # 使用 UserRecordsDB
    user_db = UserRecordsDB()
    user_db.load_database()

    # 使用 DevOpsDB
    dev_ops_db = DevOpsDB()
    dev_ops_db.save_to_database("Your Query", "AI Response")

if __name__ == "__main__":
    main()
