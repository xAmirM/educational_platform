from pymongo import MongoClient
from pymongo.collection import Collection
import time
from utility import time_expierd
client = MongoClient()

db = client["education_platform"]

users = db["users"]
messages = db["messages"]
items = db["items"]
discount_codes = db["discount_codes"]


class Model:
    def __init__(self, collection: Collection):
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

# the _id argument is "code" for DiscountCodeModel and item_name for ItemModel
    def update(self, _id, updated_data):
        try:
            data = self.collection.find_one({"_id": _id})
            if data:
                self.collection.update_one({"_id": _id}, {"$set": updated_data})
        except Exception as e:
            print(f"Exeption {e}")

# the _id argument is "code" for DiscountCodeModel and item_name for ItemModel
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
    
#TODO  need a method to update all prices 

class ItemModel(Model):
    def get_by_name(self, name):
        try:
            item = self.collection.find_one({"name": name})
            if item:
                return item
            return False
        except Exception as e:
            print(f"Exception {e}")
    

    def get_item_list(self) -> list:
        items = self.collection.find()
        item_name_list = []
        for item in items:
            item_name_list.extend(item.values())
        item_name_list = list(set(item_name_list))
        return item_name_list
    
# this inherits from the model class but functions a bit different(needs some special arguments )
# overrides create method
class DiscountCodeModel(Model):
    def get_by_code(self, code):
        try:
            result = self.collection.find_one({"code": code})
            if result:
                return result
            return False
        except Exception as e:
            print(f"Exception {e}")


    def create(self, code, expiery_seconds, percentage):
        try:
            now = time.time()
            data = {"code": code, "expiery_seconds": expiery_seconds, "percentage": percentage, "starting_time": now}
            self.collection.insert_one(data)
        except Exception as e:
            print(f"Exception {e}")    


    def is_useable(self, code):
        code_data = self.get_by_code(code)
        if not code_data:
            return False
        if time_expierd(code_data["starting_time"], code_data["expiery_seconds"]):
            return False
        return True


    def delete(self, code):
        try:
            resault = self.get_by_code(code)
            if not resault:
                return False
            self.collection.delete_one({"code": code})
            return True
        except Exception as e:
            print(f"Exeption {e}")


    def get_by_id(self):
        raise NotImplementedError("this method is not available in DiscountCodeModel")
    
    

class ExamModel(Model):
    ...


user_model = UserModel(users)
item_model = ItemModel(items)
discount_code_model = DiscountCodeModel(discount_codes)