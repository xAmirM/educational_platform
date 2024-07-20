from pymongo import MongoClient

client = MongoClient()

db = client["education_platform"]

users = db["users"]
messages = db["messages"]
items = db["items"]


class Model:
    def __init__(self, collection):
        self.collection = collection

    
    def create(self, data):
        try:
            resault = self.get_by_id(data["_id"])
            
            if resault:
                return False
            self.collection.insert_one(data)
            return True
        except Exception as e:
            print(f"Exeption {e}")


    def get_by_id(self, _id):
        try:
            resault = self.collection.find_one({"_id": _id})

            if resault:
                return resault
            return False
        except Exception as e:
            print(f"Exeption {e}")


    def update(self, _id, updated_data):
        try:
            data = self.collection.find_one({"_id": _id})
            if data:
                self.collection.update_one({"_id": _id}, {"$set": updated_data})
        except Exception as e:
            print(f"Exeption {e}")


    def delete(self, _id):
        try:
            resault = self.get_by_id(_id)
            if not resault:
                return False
            self.collection.delete_one({"_id": _id})
        except Exception as e:
            print(f"Exeption {e}")


class UserModel(Model):
    def get_by_username(self, username):
        try:
            user = self.collection.find_one({"username": username})
            if user:
                return user
            return
        except Exception as e:
            print(f"An error occurred: {e}")
            return 
    
#TODO write neccessary methods (need methods for managing)

class ItemModel(Model):
    def get_by_name(self, name):
        try:
            item = self.collection.find_one({"name": name})
            if item:
                return item
            return False
        except Exception as e:
            print(f"Exception {e}")


user_model = UserModel(users)
item_model = ItemModel(items)