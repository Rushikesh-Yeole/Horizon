from google.cloud import firestore



db = firestore.Client(database="hackathonfirestore")

def insert_user_to_db(user_data: dict,confirm_pending):
    try:
        if confirm_pending:
            user_data["confirm_pending"] = True
        else:
            user_data["confirm_pending"] = False
        user_data["personality_ready"] = False
        doc_ref,_ = db.collection("users").add(user_data)
        print(f"user successfully inserted {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        print(f"firestore error while inserting user {e}")
        raise 

def get_user(user_id: str):
    try:
        doc_ref = db.collection("users").document(user_id)
        if not doc_ref.get().exists:
            raise ValueError("user does not exist")
        doc = doc_ref.get()
        print(f"user successfully extracted {doc_ref.id}")
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"firestore error while fetching user {e}")
        raise 
    
def mark_user_onboarded(user_id: str):
    try:
        doc_ref = db.collection("users").document(user_id)
        if not doc_ref.get().exists:
            raise ValueError("user does not exist")
        doc_ref.update({"confirm_pending":False})

        print(f"user successfully updated {doc_ref.id}")
    except Exception as e:
        print(f"firestore error while onboarding user {e}")
        raise 
    
def update_user_personality(user_id:str, personality: dict):
    try:
        doc_ref = db.collection("users").document(user_id)
        doc_ref.update({"personality":personality,"personality_ready":True})

        print(f"user personality successfully updated {doc_ref.id}")
    except Exception as e:
        print(f"firestore error while updating user personality {e}")
        raise 
    