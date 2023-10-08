import json

def json_to_class(json_str, class_name="DynamicClass"):
    data_dict = json.loads(json_str)
    return type(class_name, (object,), data_dict)